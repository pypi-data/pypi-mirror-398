"""Test Tools - start_test, get_status, stop_test, get_result."""

from ..server import mcp
from ..shared import executor


@mcp.tool()
async def start_test(script: str, vus: int = 10, duration: str = "30s") -> dict:
    """启动 K6 压力测试。
    
    Args:
        script: K6 测试脚本内容（JavaScript）
        vus: 虚拟用户数，默认 10
        duration: 测试持续时间，如 "30s", "5m", "1h"
    
    Returns:
        包含 testId 和状态的结果
    """
    return await executor.start_test(script, vus, duration)


@mcp.tool()
def get_status(test_id: str) -> dict:
    """获取测试实时状态和进度。
    
    Args:
        test_id: 测试 ID
    
    Returns:
        测试状态、进度百分比和实时指标
    """
    return executor.get_status(test_id)


@mcp.tool()
async def stop_test(test_id: str) -> dict:
    """停止正在运行的测试。
    
    Args:
        test_id: 测试 ID
    
    Returns:
        停止后的状态
    """
    return await executor.stop_test(test_id)


@mcp.tool()
def get_result(test_id: str) -> dict:
    """获取完整的测试结果。
    
    Args:
        test_id: 测试 ID
    
    Returns:
        包含详细指标的完整测试结果
    """
    return executor.get_result(test_id)
