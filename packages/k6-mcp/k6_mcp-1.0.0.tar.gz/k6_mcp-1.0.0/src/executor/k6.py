"""K6 Executor - K6 process management."""

import asyncio
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TestStatus(str, Enum):
    """Test execution status."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    TIMEOUT = "timeout"


@dataclass
class TestMetrics:
    """Test metrics snapshot."""
    vus: int = 0
    iterations: int = 0
    rps: float = 0.0
    avg_duration: float = 0.0
    p50_duration: float = 0.0
    p90_duration: float = 0.0
    p95_duration: float = 0.0
    p99_duration: float = 0.0
    min_duration: float = 0.0
    max_duration: float = 0.0
    error_rate: float = 0.0
    total_requests: int = 0
    success_rate: float = 100.0


@dataclass
class TestError:
    """Test error information."""
    code: str
    count: int
    message: str


@dataclass
class TestState:
    """Test execution state."""
    id: str
    status: TestStatus
    start_time: datetime
    duration_ms: int  # 预期时长(ms)
    summary_file: str
    stdout: str = ""
    stderr: str = ""
    process: Optional[asyncio.subprocess.Process] = None
    metrics: Optional[TestMetrics] = None
    errors: list[TestError] = field(default_factory=list)


class K6Executor:
    """K6 process executor and manager."""
    
    MAX_VUS = 500
    MAX_DURATION_MS = 30 * 60 * 1000  # 30 minutes
    DEFAULT_VUS = 10
    DEFAULT_DURATION = "30s"
    
    def __init__(self):
        self._tests: dict[str, TestState] = {}
        self._k6_path: Optional[str] = None
    
    def check_k6_installed(self) -> dict:
        """Check if K6 is installed and return version info."""
        k6_path = shutil.which("k6")
        
        if not k6_path:
            return {
                "installed": False,
                "message": "K6 未安装",
                "install_guide": {
                    "mac": "brew install k6",
                    "linux": "sudo apt install k6 或 sudo snap install k6",
                    "windows": "choco install k6"
                }
            }
        
        self._k6_path = k6_path
        
        # 获取版本
        try:
            import subprocess
            result = subprocess.run(
                [k6_path, "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            version = "unknown"
        
        return {
            "installed": True,
            "version": version,
            "path": k6_path
        }
    
    async def start_test(
        self,
        script: str,
        vus: int = DEFAULT_VUS,
        duration: str = DEFAULT_DURATION
    ) -> dict:
        """Start a K6 test asynchronously."""
        from ..utils import parse_duration
        
        # 检查 K6
        k6_info = self.check_k6_installed()
        if not k6_info["installed"]:
            return {"error": True, **k6_info}
        
        # 检查 VUs 限制
        if vus > self.MAX_VUS:
            return {
                "error": True,
                "message": f"VUs 不能超过 {self.MAX_VUS}"
            }
        
        # 检查是否有正在运行的测试
        running = [t for t in self._tests.values() if t.status == TestStatus.RUNNING]
        if running:
            return {
                "error": True,
                "message": "已有测试在运行，请等待完成或停止"
            }
        
        test_id = str(uuid.uuid4())
        summary_file = os.path.join(tempfile.gettempdir(), f"k6-summary-{test_id}.json")
        duration_ms = parse_duration(duration)
        
        # 创建临时脚本文件
        script_file = os.path.join(tempfile.gettempdir(), f"k6-script-{test_id}.js")
        with open(script_file, "w") as f:
            f.write(script)
        
        # 启动 K6 进程
        try:
            process = await asyncio.create_subprocess_exec(
                self._k6_path,
                "run",
                "--vus", str(vus),
                "--duration", duration,
                "--summary-export", summary_file,
                script_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except Exception as e:
            return {
                "error": True,
                "message": f"启动 K6 失败: {str(e)}"
            }
        
        # 保存状态
        test_state = TestState(
            id=test_id,
            status=TestStatus.RUNNING,
            start_time=datetime.now(),
            duration_ms=duration_ms,
            summary_file=summary_file,
            process=process
        )
        self._tests[test_id] = test_state
        
        # 后台监控进程
        asyncio.create_task(self._monitor_test(test_id, script_file))
        
        return {
            "testId": test_id,
            "status": "running",
            "startTime": test_state.start_time.isoformat()
        }
    
    async def _monitor_test(self, test_id: str, script_file: str):
        """Monitor test process and update status."""
        test = self._tests.get(test_id)
        if not test or not test.process:
            return
        
        # 设置超时
        timeout_seconds = min(
            test.duration_ms / 1000 + 60,  # 预期时长 + 1分钟缓冲
            self.MAX_DURATION_MS / 1000
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                test.process.communicate(),
                timeout=timeout_seconds
            )
            test.stdout = stdout.decode() if stdout else ""
            test.stderr = stderr.decode() if stderr else ""
            
            if test.status == TestStatus.RUNNING:
                test.status = (
                    TestStatus.COMPLETED 
                    if test.process.returncode == 0 
                    else TestStatus.FAILED
                )
        except asyncio.TimeoutError:
            if test.status == TestStatus.RUNNING:
                test.process.kill()
                test.status = TestStatus.TIMEOUT
        finally:
            # 清理脚本文件
            try:
                os.unlink(script_file)
            except Exception:
                pass
    
    def get_status(self, test_id: str) -> dict:
        """Get test status and progress."""
        from ..utils import format_duration
        
        test = self._tests.get(test_id)
        if not test:
            return {"error": True, "message": "测试不存在"}
        
        elapsed_ms = (datetime.now() - test.start_time).total_seconds() * 1000
        progress = min(100, int((elapsed_ms / test.duration_ms) * 100))
        
        result = {
            "testId": test_id,
            "status": test.status.value,
            "progress": progress,
            "elapsed": format_duration(int(elapsed_ms))
        }
        
        if test.metrics:
            result["metrics"] = {
                "vus": test.metrics.vus,
                "iterations": test.metrics.iterations,
                "rps": test.metrics.rps,
                "avgDuration": test.metrics.avg_duration,
                "p95Duration": test.metrics.p95_duration,
                "errorRate": test.metrics.error_rate
            }
        
        return result
    
    async def stop_test(self, test_id: str) -> dict:
        """Stop a running test."""
        test = self._tests.get(test_id)
        if not test:
            return {"error": True, "message": "测试不存在"}
        
        if test.status == TestStatus.RUNNING and test.process:
            test.process.terminate()
            try:
                await asyncio.wait_for(test.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                test.process.kill()
            test.status = TestStatus.STOPPED
        
        return {"testId": test_id, "status": test.status.value}
    
    def get_result(self, test_id: str) -> dict:
        """Get complete test results."""
        from .parser import K6Parser
        
        test = self._tests.get(test_id)
        if not test:
            return {"error": True, "message": "测试不存在"}
        
        if test.status == TestStatus.RUNNING:
            return {"error": True, "message": "测试仍在运行中"}
        
        # 解析结果
        parser = K6Parser()
        if os.path.exists(test.summary_file):
            metrics, errors = parser.parse_summary(test.summary_file)
            test.metrics = metrics
            test.errors = errors
        
        result = {
            "testId": test_id,
            "status": test.status.value,
        }
        
        if test.metrics:
            result["summary"] = {
                "totalRequests": test.metrics.total_requests,
                "successRate": test.metrics.success_rate,
                "avgDuration": test.metrics.avg_duration,
                "p50Duration": test.metrics.p50_duration,
                "p90Duration": test.metrics.p90_duration,
                "p95Duration": test.metrics.p95_duration,
                "p99Duration": test.metrics.p99_duration,
                "minDuration": test.metrics.min_duration,
                "maxDuration": test.metrics.max_duration,
                "rps": test.metrics.rps
            }
        
        if test.errors:
            result["errors"] = [
                {"code": e.code, "count": e.count, "message": e.message}
                for e in test.errors
            ]
        
        return result
    
    def get_test(self, test_id: str) -> Optional[TestState]:
        """Get test state by ID."""
        return self._tests.get(test_id)
    
    def cleanup(self, test_id: str):
        """Cleanup test resources."""
        test = self._tests.get(test_id)
        if test:
            try:
                if os.path.exists(test.summary_file):
                    os.unlink(test.summary_file)
            except Exception:
                pass

