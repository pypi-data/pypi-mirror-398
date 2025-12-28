"""Quick Tools - quick_test, save_api, test_saved, list_apis, delete_api, long_test."""

from ..server import mcp
from ..shared import executor, storage
from ..utils.curl_parser import curl_to_k6_script, parse_curl


@mcp.tool()
async def quick_test(
    curl: str, 
    vus: int = 5, 
    duration: str = "10s",
    save_as: str = None
) -> dict:
    """快速压测 - 直接传 cURL 命令执行压测。
    
    Args:
        curl: cURL 命令字符串
        vus: 虚拟用户数，默认 5
        duration: 测试持续时间，默认 "10s"
        save_as: 可选，保存接口的名称
    
    Returns:
        包含 testId 和状态的结果
    """
    # 解析 cURL 并生成 K6 脚本
    try:
        script, parsed = curl_to_k6_script(curl)
    except Exception as e:
        return {
            "error": True,
            "message": f"cURL 解析失败: {str(e)}"
        }
    
    if not parsed.url:
        return {
            "error": True,
            "message": "无法从 cURL 中解析出 URL"
        }
    
    # 如果指定了保存名称，保存接口
    if save_as:
        storage.save_api(save_as, curl)
    
    # 执行测试
    result = await executor.start_test(script, vus, duration)
    
    # 添加解析信息
    if not result.get("error"):
        result["parsedRequest"] = {
            "method": parsed.method,
            "url": parsed.url
        }
        if save_as:
            result["savedAs"] = save_as
    
    return result


@mcp.tool()
def save_api(name: str, curl: str, description: str = "") -> dict:
    """保存接口配置，方便后续复用。
    
    Args:
        name: 接口名称，如 "文章列表"
        curl: cURL 命令字符串
        description: 可选的接口描述
    
    Returns:
        保存结果
    """
    return storage.save_api(name, curl, description)


@mcp.tool()
async def test_saved(name: str, vus: int = 5, duration: str = "10s") -> dict:
    """测试已保存的接口。
    
    Args:
        name: 接口名称
        vus: 虚拟用户数，默认 5
        duration: 测试持续时间，默认 "10s"
    
    Returns:
        包含 testId 和状态的结果
    """
    # 获取保存的接口
    api = storage.get_api(name)
    if not api:
        return {
            "error": True,
            "message": f"接口 '{name}' 不存在，请先保存"
        }
    
    curl = api.get("curl")
    if not curl:
        return {
            "error": True,
            "message": f"接口 '{name}' 的 cURL 配置无效"
        }
    
    # 解析并执行
    try:
        script, parsed = curl_to_k6_script(curl)
    except Exception as e:
        return {
            "error": True,
            "message": f"cURL 解析失败: {str(e)}"
        }
    
    result = await executor.start_test(script, vus, duration)
    
    if not result.get("error"):
        result["apiName"] = name
        result["parsedRequest"] = {
            "method": parsed.method,
            "url": parsed.url
        }
    
    return result


@mcp.tool()
def list_apis() -> dict:
    """列出所有保存的接口。
    
    Returns:
        接口列表
    """
    apis = storage.list_apis()
    return {
        "count": len(apis),
        "apis": apis
    }


@mcp.tool()
def delete_api(name: str) -> dict:
    """删除保存的接口。
    
    Args:
        name: 接口名称
    
    Returns:
        删除结果
    """
    success = storage.delete_api(name)
    if success:
        return {"success": True, "message": f"接口 '{name}' 已删除"}
    else:
        return {"error": True, "message": f"接口 '{name}' 不存在"}


@mcp.tool()
async def long_test(curl: str, timeout: str = "5m") -> dict:
    """长耗时接口测试（导出/报表类接口）。
    
    单次请求，超长超时，适合测试导出、报表生成等耗时接口。
    
    Args:
        curl: cURL 命令字符串
        timeout: 超时时间，默认 "5m"（5分钟）
    
    Returns:
        请求结果，包含响应时间和状态
    """
    from ..utils import parse_duration
    import asyncio
    import aiohttp
    import time
    
    # 解析 cURL
    try:
        parsed = parse_curl(curl)
    except Exception as e:
        return {
            "error": True,
            "message": f"cURL 解析失败: {str(e)}"
        }
    
    if not parsed.url:
        return {
            "error": True,
            "message": "无法从 cURL 中解析出 URL"
        }
    
    timeout_ms = parse_duration(timeout)
    timeout_seconds = timeout_ms / 1000
    
    # 执行单次请求
    start_time = time.time()
    
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            method = parsed.method.upper()
            
            kwargs = {
                "headers": parsed.headers,
                "timeout": aiohttp.ClientTimeout(total=timeout_seconds)
            }
            
            if parsed.body:
                kwargs["data"] = parsed.body
            
            async with session.request(method, parsed.url, **kwargs) as response:
                status = response.status
                content_length = response.headers.get("Content-Length", "unknown")
                # 读取响应（但不保存全部内容，只获取大小）
                body = await response.read()
                body_size = len(body)
        
        elapsed = time.time() - start_time
        
        return {
            "success": True,
            "request": {
                "method": parsed.method,
                "url": parsed.url
            },
            "response": {
                "status": status,
                "duration": f"{elapsed:.2f}s",
                "durationMs": int(elapsed * 1000),
                "bodySize": body_size,
                "bodySizeFormatted": _format_size(body_size)
            },
            "verdict": "success" if status == 200 else "failed"
        }
        
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        return {
            "error": True,
            "message": f"请求超时（{timeout}）",
            "elapsed": f"{elapsed:.2f}s"
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "error": True,
            "message": f"请求失败: {str(e)}",
            "elapsed": f"{elapsed:.2f}s"
        }


def _format_size(size_bytes: int) -> str:
    """Format byte size to human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


@mcp.tool()
async def data_driven_test(
    curl: str,
    data: list[dict],
    vus: int = 10,
    duration: str = "30s"
) -> dict:
    """数据驱动压测 - 每个请求使用不同的参数。
    
    从 MySQL MCP 获取测试数据后，传入此工具执行压测。
    cURL 中使用 __FIELD_NAME__ 格式的占位符，会被替换为 data 中对应字段的值。
    
    Args:
        curl: cURL 命令字符串，包含占位符（如 __USER_ID__、__USERNAME__）
        data: 测试数据列表，从 MySQL MCP 获取（如 [{"USER_ID": "1"}, {"USER_ID": "2"}]）
        vus: 虚拟用户数，默认 10
        duration: 测试持续时间，默认 "30s"
    
    Returns:
        包含 testId 和状态的结果
    
    示例:
        curl: "curl 'https://api.com/user?id=__USER_ID__' -H 'Authorization: __TOKEN__'"
        data: [
            {"USER_ID": "123", "TOKEN": "abc"},
            {"USER_ID": "456", "TOKEN": "def"},
            ...
        ]
        → 每个请求使用不同的 USER_ID 和 TOKEN
    """
    import json
    import re
    
    if not data or len(data) == 0:
        return {
            "error": True,
            "message": "测试数据不能为空，请先从 MySQL MCP 获取数据"
        }
    
    # 解析 cURL 获取基本信息
    try:
        parsed = parse_curl(curl)
    except Exception as e:
        return {
            "error": True,
            "message": f"cURL 解析失败: {str(e)}"
        }
    
    if not parsed.url:
        return {
            "error": True,
            "message": "无法从 cURL 中解析出 URL"
        }
    
    # 找出所有占位符
    placeholders = set(re.findall(r'__(\w+)__', curl))
    
    if not placeholders:
        return {
            "error": True,
            "message": "cURL 中没有找到占位符（格式: __FIELD_NAME__）"
        }
    
    # 检查数据中是否包含所有占位符对应的字段
    sample = data[0]
    missing_fields = []
    for placeholder in placeholders:
        if placeholder not in sample and placeholder.lower() not in [k.lower() for k in sample.keys()]:
            missing_fields.append(placeholder)
    
    if missing_fields:
        return {
            "error": True,
            "message": f"数据中缺少字段: {', '.join(missing_fields)}",
            "available_fields": list(sample.keys()),
            "required_placeholders": list(placeholders)
        }
    
    # 生成 K6 脚本
    script = _generate_data_driven_script(parsed, data, placeholders)
    
    # 执行测试
    result = await executor.start_test(script, vus, duration)
    
    if not result.get("error"):
        result["parsedRequest"] = {
            "method": parsed.method,
            "url": parsed.url
        }
        result["dataInfo"] = {
            "totalRecords": len(data),
            "placeholders": list(placeholders),
            "sampleData": data[0] if data else None
        }
    
    return result


def _generate_data_driven_script(parsed, data: list[dict], placeholders: set) -> str:
    """生成数据驱动的 K6 脚本。"""
    import json
    
    # 构建 headers（不包含占位符的部分）
    headers_obj = {}
    for key, value in parsed.headers.items():
        headers_obj[key] = value
    
    # 序列化数据
    data_json = json.dumps(data, ensure_ascii=False)
    
    # 构建 URL 模板（保留占位符）
    url_template = parsed.url
    
    # 构建 body 模板（如果有）
    body_template = parsed.body if parsed.body else None
    
    # 构建 headers JSON
    headers_json = json.dumps(headers_obj, ensure_ascii=False)
    
    # 生成替换逻辑
    replace_code = ""
    for placeholder in placeholders:
        # 尝试匹配大小写不敏感
        replace_code += f'''
    url = url.replace("__{placeholder}__", String(record["{placeholder}"] || record["{placeholder.lower()}"] || ""));'''
        if body_template:
            replace_code += f'''
    body = body.replace("__{placeholder}__", String(record["{placeholder}"] || record["{placeholder.lower()}"] || ""));'''
        replace_code += f'''
    for (let key in headers) {{
        if (typeof headers[key] === 'string') {{
            headers[key] = headers[key].replace("__{placeholder}__", String(record["{placeholder}"] || record["{placeholder.lower()}"] || ""));
        }}
    }}'''
    
    # 选择 HTTP 方法
    method_lower = parsed.method.lower()
    if method_lower == "get":
        request_call = 'http.get(url, { headers: headers })'
    elif method_lower == "post":
        request_call = 'http.post(url, body, { headers: headers })'
    elif method_lower == "put":
        request_call = 'http.put(url, body, { headers: headers })'
    elif method_lower == "patch":
        request_call = 'http.patch(url, body, { headers: headers })'
    elif method_lower == "delete":
        request_call = 'http.del(url, { headers: headers })'
    else:
        request_call = 'http.get(url, { headers: headers })'
    
    # 生成完整脚本
    script = f'''import http from "k6/http";
import {{ check, sleep }} from "k6";
import {{ SharedArray }} from "k6/data";

// 测试数据（从 MySQL 获取的 {len(data)} 条记录）
const testData = new SharedArray("test_data", function() {{
    return {data_json};
}});

export default function() {{
    // 根据迭代次数选择数据（轮流使用）
    const index = __ITER % testData.length;
    const record = testData[index];
    
    // URL 模板
    let url = "{url_template}";
    
    // Headers 模板
    let headers = {headers_json};
'''
    
    if body_template:
        escaped_body = body_template.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
        script += f'''
    // Body 模板
    let body = `{escaped_body}`;
'''
    else:
        script += '''
    let body = null;
'''
    
    script += f'''
    // 替换占位符
    {replace_code}
    
    // 发送请求
    const res = {request_call};
    
    // 检查响应
    check(res, {{
        "status is 200": (r) => r.status === 200,
        "response time < 500ms": (r) => r.timings.duration < 500,
    }});
    
    sleep(0.1);
}}'''
    
    return script

