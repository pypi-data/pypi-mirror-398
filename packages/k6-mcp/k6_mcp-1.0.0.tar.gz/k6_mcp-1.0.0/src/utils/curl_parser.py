"""cURL Parser - Parse cURL command to request parameters."""

import re
import shlex
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse, parse_qs


@dataclass
class ParsedRequest:
    """Parsed HTTP request from cURL."""
    method: str = "GET"
    url: str = ""
    headers: dict = field(default_factory=dict)
    body: Optional[str] = None
    cookies: dict = field(default_factory=dict)


def parse_curl(curl_command: str) -> ParsedRequest:
    """
    Parse a cURL command into request parameters.
    
    Args:
        curl_command: The cURL command string
        
    Returns:
        ParsedRequest with method, url, headers, body, cookies
    """
    # 清理命令：移除换行和多余空格
    curl_command = curl_command.replace('\\\n', ' ')
    curl_command = curl_command.replace('\n', ' ')
    curl_command = re.sub(r'\s+', ' ', curl_command).strip()
    
    # 移除开头的 curl
    if curl_command.lower().startswith('curl '):
        curl_command = curl_command[5:]
    
    result = ParsedRequest()
    
    try:
        # 使用 shlex 解析命令行参数
        tokens = shlex.split(curl_command)
    except ValueError:
        # 如果 shlex 解析失败，尝试简单分割
        tokens = curl_command.split()
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # URL (不以 - 开头的参数)
        if not token.startswith('-') and ('http://' in token or 'https://' in token):
            result.url = token.strip("'\"")
            i += 1
            continue
        
        # Method: -X POST
        if token in ('-X', '--request'):
            if i + 1 < len(tokens):
                result.method = tokens[i + 1].upper()
                i += 2
                continue
        
        # Headers: -H "Content-Type: application/json"
        if token in ('-H', '--header'):
            if i + 1 < len(tokens):
                header = tokens[i + 1]
                if ':' in header:
                    key, value = header.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    # 跳过空的 header 值（如 "GameToken;"）
                    if value and not value.endswith(';'):
                        result.headers[key] = value
                    elif value.endswith(';') and len(value) > 1:
                        result.headers[key] = value[:-1]
                i += 2
                continue
        
        # Data: -d '{"key": "value"}'
        if token in ('-d', '--data', '--data-raw', '--data-binary'):
            if i + 1 < len(tokens):
                result.body = tokens[i + 1]
                if result.method == "GET":
                    result.method = "POST"
                i += 2
                continue
        
        # Cookies: -b "name=value"
        if token in ('-b', '--cookie'):
            if i + 1 < len(tokens):
                cookie_str = tokens[i + 1]
                for cookie in cookie_str.split(';'):
                    if '=' in cookie:
                        key, value = cookie.split('=', 1)
                        result.cookies[key.strip()] = value.strip()
                i += 2
                continue
        
        # 跳过其他参数
        if token.startswith('-'):
            # 检查是否是带值的参数
            if token in ('--compressed', '--insecure', '-k', '-L', '--location', 
                        '-s', '--silent', '-v', '--verbose'):
                i += 1
            elif i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
                i += 2
            else:
                i += 1
        else:
            i += 1
    
    return result


def generate_k6_script(request: ParsedRequest, check_status: int = 200) -> str:
    """
    Generate K6 script from parsed request.
    
    Args:
        request: ParsedRequest object
        check_status: Expected HTTP status code
        
    Returns:
        K6 JavaScript script
    """
    # 构建 headers
    headers_js = "{\n"
    for key, value in request.headers.items():
        # 转义引号
        escaped_value = value.replace('"', '\\"')
        headers_js += f'            "{key}": "{escaped_value}",\n'
    headers_js += "        }"
    
    # 构建请求选项
    params_js = f"""{{
        headers: {headers_js}
    }}"""
    
    # 构建请求体
    body_js = ""
    if request.body:
        escaped_body = request.body.replace('\\', '\\\\').replace('`', '\\`')
        body_js = f", `{escaped_body}`"
    
    # 选择 HTTP 方法
    method_lower = request.method.lower()
    if method_lower == "get":
        request_call = f'http.get(url, params)'
    elif method_lower == "post":
        request_call = f'http.post(url, body, params)'
    elif method_lower == "put":
        request_call = f'http.put(url, body, params)'
    elif method_lower == "patch":
        request_call = f'http.patch(url, body, params)'
    elif method_lower == "delete":
        request_call = f'http.del(url, params)'
    else:
        request_call = f'http.get(url, params)'
    
    # 生成完整脚本
    script = f'''import http from "k6/http";
import {{ check, sleep }} from "k6";

export default function() {{
    const url = "{request.url}";
    
    const params = {params_js};
'''
    
    if request.body:
        escaped_body = request.body.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
        script += f'''
    const body = `{escaped_body}`;
'''
    
    script += f'''
    const res = {request_call};
    
    check(res, {{
        "status is {check_status}": (r) => r.status === {check_status},
        "response time < 500ms": (r) => r.timings.duration < 500,
    }});
    
    sleep(0.1);
}}'''
    
    return script


def curl_to_k6_script(curl_command: str) -> tuple[str, ParsedRequest]:
    """
    Convert cURL command to K6 script.
    
    Args:
        curl_command: The cURL command string
        
    Returns:
        Tuple of (K6 script, ParsedRequest)
    """
    request = parse_curl(curl_command)
    script = generate_k6_script(request)
    return script, request

