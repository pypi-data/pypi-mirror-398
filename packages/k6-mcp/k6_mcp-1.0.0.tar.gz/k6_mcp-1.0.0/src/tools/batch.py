"""Batch Tools - batch_test, get_batch_status, get_batch_result."""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from ..server import mcp
from ..shared import executor


class BatchStatus(str, Enum):
    """Batch test status."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BatchTestItem:
    """Single test in a batch."""
    name: str
    script: str
    vus: int = 10
    duration: str = "30s"
    test_id: Optional[str] = None
    status: str = "pending"
    result: Optional[dict] = None


@dataclass
class BatchState:
    """Batch test state."""
    id: str
    status: BatchStatus
    tests: list[BatchTestItem]
    current_index: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    stop_on_fail: bool = False


# 存储批量测试状态
_batches: dict[str, BatchState] = {}


@mcp.tool()
async def batch_test(
    tests: list[dict],
    stop_on_fail: bool = False
) -> dict:
    """批量执行多个压力测试（顺序执行）。
    
    Args:
        tests: 测试列表，每个包含 name, script, vus(可选), duration(可选)
        stop_on_fail: 失败时是否停止后续测试，默认 False
    
    Returns:
        批量测试 ID 和状态
    """
    batch_id = str(uuid.uuid4())
    
    # 解析测试项
    test_items = []
    for t in tests:
        item = BatchTestItem(
            name=t.get("name", f"Test {len(test_items) + 1}"),
            script=t.get("script", ""),
            vus=t.get("vus", 10),
            duration=t.get("duration", "30s")
        )
        test_items.append(item)
    
    if not test_items:
        return {"error": True, "message": "没有提供测试"}
    
    batch = BatchState(
        id=batch_id,
        status=BatchStatus.RUNNING,
        tests=test_items,
        start_time=datetime.now(),
        stop_on_fail=stop_on_fail
    )
    _batches[batch_id] = batch
    
    # 后台执行批量测试
    asyncio.create_task(_run_batch(batch_id))
    
    return {
        "batchId": batch_id,
        "total": len(test_items),
        "status": "running"
    }


async def _run_batch(batch_id: str):
    """Run batch tests sequentially."""
    batch = _batches.get(batch_id)
    if not batch:
        return
    
    for i, test_item in enumerate(batch.tests):
        batch.current_index = i
        test_item.status = "running"
        
        # 启动测试
        result = await executor.start_test(
            test_item.script,
            test_item.vus,
            test_item.duration
        )
        
        if result.get("error"):
            test_item.status = "failed"
            test_item.result = result
            if batch.stop_on_fail:
                batch.status = BatchStatus.FAILED
                break
            continue
        
        test_item.test_id = result.get("testId")
        
        # 等待测试完成
        while True:
            status = executor.get_status(test_item.test_id)
            if status.get("status") not in ["running"]:
                break
            await asyncio.sleep(1)
        
        # 获取结果
        test_item.result = executor.get_result(test_item.test_id)
        test_item.status = "completed" if not test_item.result.get("error") else "failed"
        
        if test_item.status == "failed" and batch.stop_on_fail:
            batch.status = BatchStatus.FAILED
            break
    
    batch.end_time = datetime.now()
    if batch.status == BatchStatus.RUNNING:
        failed_count = sum(1 for t in batch.tests if t.status == "failed")
        batch.status = BatchStatus.FAILED if failed_count > 0 else BatchStatus.COMPLETED


@mcp.tool()
def get_batch_status(batch_id: str) -> dict:
    """获取批量测试的进度状态。
    
    Args:
        batch_id: 批量测试 ID
    
    Returns:
        批量测试进度和当前运行的测试信息
    """
    batch = _batches.get(batch_id)
    if not batch:
        return {"error": True, "message": "批量测试不存在"}
    
    completed = sum(1 for t in batch.tests if t.status in ["completed", "failed"])
    failed = sum(1 for t in batch.tests if t.status == "failed")
    
    current = None
    if batch.status == BatchStatus.RUNNING and batch.current_index < len(batch.tests):
        current_test = batch.tests[batch.current_index]
        current = {
            "name": current_test.name,
            "progress": 0
        }
        if current_test.test_id:
            status = executor.get_status(current_test.test_id)
            current["progress"] = status.get("progress", 0)
    
    return {
        "batchId": batch_id,
        "status": batch.status.value,
        "total": len(batch.tests),
        "completed": completed,
        "failed": failed,
        "current": current
    }


@mcp.tool()
def get_batch_result(batch_id: str) -> dict:
    """获取批量测试的完整结果。
    
    Args:
        batch_id: 批量测试 ID
    
    Returns:
        所有测试的结果汇总
    """
    batch = _batches.get(batch_id)
    if not batch:
        return {"error": True, "message": "批量测试不存在"}
    
    if batch.status == BatchStatus.RUNNING:
        return {"error": True, "message": "批量测试仍在运行中"}
    
    results = []
    slowest = None
    fastest = None
    slowest_avg = 0
    fastest_avg = float("inf")
    
    for test_item in batch.tests:
        status = "pass"
        metrics = {}
        
        if test_item.result and "summary" in test_item.result:
            summary = test_item.result["summary"]
            avg = summary.get("avgDuration", 0)
            metrics = {
                "avg": avg,
                "p95": summary.get("p95Duration", 0),
                "rps": summary.get("rps", 0),
                "errorRate": summary.get("errorRate", 0)
            }
            
            # 判断状态
            if summary.get("errorRate", 0) > 10:
                status = "fail"
            elif avg > 500:  # 超过 500ms 警告
                status = "warning"
            
            # 追踪最慢/最快
            if avg > slowest_avg:
                slowest_avg = avg
                slowest = test_item.name
            if avg < fastest_avg:
                fastest_avg = avg
                fastest = test_item.name
        elif test_item.status == "failed":
            status = "fail"
        
        results.append({
            "name": test_item.name,
            "status": status,
            "metrics": metrics
        })
    
    # 计算时长
    duration = ""
    if batch.start_time and batch.end_time:
        delta = batch.end_time - batch.start_time
        duration = f"{int(delta.total_seconds())}s"
    
    passed = sum(1 for r in results if r["status"] == "pass")
    warning = sum(1 for r in results if r["status"] == "warning")
    failed = sum(1 for r in results if r["status"] == "fail")
    
    return {
        "batchId": batch_id,
        "status": batch.status.value,
        "duration": duration,
        "results": results,
        "summary": {
            "total": len(results),
            "passed": passed,
            "warning": warning,
            "failed": failed,
            "slowest": slowest,
            "fastest": fastest
        }
    }
