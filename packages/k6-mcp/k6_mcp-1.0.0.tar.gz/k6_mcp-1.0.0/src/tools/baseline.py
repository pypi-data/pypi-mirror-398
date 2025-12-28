"""Baseline Tools - save_baseline, compare_baseline, list_baselines, delete_baseline."""

from ..server import mcp
from ..shared import executor, storage


@mcp.tool()
def save_baseline(name: str, test_id: str) -> dict:
    """保存测试结果为性能基线。
    
    Args:
        name: 基线名称，如 "登录接口"
        test_id: 要保存的测试 ID
    
    Returns:
        保存结果和基线信息
    """
    # 获取测试结果
    result = executor.get_result(test_id)
    
    if result.get("error"):
        return result
    
    if "summary" not in result:
        return {"error": True, "message": "测试结果中没有指标数据"}
    
    return storage.save_baseline(name, result["summary"])


@mcp.tool()
def compare_baseline(name: str, test_id: str) -> dict:
    """对比当前测试结果和历史基线。
    
    Args:
        name: 基线名称
        test_id: 当前测试 ID
    
    Returns:
        对比结果，包括各指标的变化百分比和状态
    """
    # 获取测试结果
    result = executor.get_result(test_id)
    
    if result.get("error"):
        return result
    
    if "summary" not in result:
        return {"error": True, "message": "测试结果中没有指标数据"}
    
    return storage.compare_baseline(name, result["summary"])


@mcp.tool()
def list_baselines() -> dict:
    """列出所有保存的性能基线。
    
    Returns:
        基线列表，包含名称、保存时间和关键指标
    """
    baselines = storage.list_baselines()
    return {"baselines": baselines}


@mcp.tool()
def delete_baseline(name: str) -> dict:
    """删除一个性能基线。
    
    Args:
        name: 要删除的基线名称
    
    Returns:
        删除结果
    """
    success = storage.delete_baseline(name)
    if success:
        return {"success": True, "message": f"基线 '{name}' 已删除"}
    return {"error": True, "message": f"基线 '{name}' 不存在"}
