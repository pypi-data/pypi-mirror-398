"""K6 Parser - Parse K6 output and summary files."""

import json
import re
from typing import Optional

from .k6 import TestMetrics, TestError


class K6Parser:
    """Parse K6 output and summary files.
    
    K6 --summary-export 导出的 JSON 格式:
    {
        "root_group": {
            "checks": {
                "check_name": {
                    "name": "check_name",
                    "passes": 100,
                    "fails": 0
                }
            }
        },
        "metrics": {
            "http_req_duration": {
                "avg": 45.123,
                "min": 10.5,
                "med": 42.0,
                "max": 120.5,
                "p(90)": 80.2,
                "p(95)": 95.3
            },
            "http_reqs": {
                "count": 1500,
                "rate": 50.0
            },
            ...
        }
    }
    """
    
    def parse_summary(self, summary_file: str) -> tuple[Optional[TestMetrics], list[TestError]]:
        """Parse K6 summary JSON file.
        
        Args:
            summary_file: Path to the K6 summary export JSON file
            
        Returns:
            Tuple of (TestMetrics, list of TestError)
        """
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return None, [TestError(code="PARSE_ERROR", count=1, message=str(e))]
        
        metrics = TestMetrics()
        errors: list[TestError] = []
        
        # 解析 metrics
        if "metrics" in data:
            m = data["metrics"]
            
            # HTTP 请求时长 (最重要的性能指标)
            # K6 v1.x 格式: 直接是值，不是嵌套在 values 里
            if "http_req_duration" in m:
                duration = m["http_req_duration"]
                # 兼容两种格式
                if "values" in duration:
                    v = duration["values"]
                else:
                    v = duration
                
                metrics.avg_duration = float(v.get("avg", 0))
                metrics.min_duration = float(v.get("min", 0))
                metrics.max_duration = float(v.get("max", 0))
                metrics.p50_duration = float(v.get("med", 0))
                metrics.p90_duration = float(v.get("p(90)", 0))
                metrics.p95_duration = float(v.get("p(95)", 0))
                metrics.p99_duration = float(v.get("p(99)", 0))
            
            # HTTP 请求数量和 RPS
            if "http_reqs" in m:
                reqs = m["http_reqs"]
                if "values" in reqs:
                    v = reqs["values"]
                else:
                    v = reqs
                metrics.total_requests = int(v.get("count", 0))
                metrics.rps = float(v.get("rate", 0))
            
            # 迭代次数
            if "iterations" in m:
                iterations = m["iterations"]
                if "values" in iterations:
                    v = iterations["values"]
                else:
                    v = iterations
                metrics.iterations = int(v.get("count", 0))
            
            # VUs (虚拟用户数)
            if "vus" in m:
                vus = m["vus"]
                if "values" in vus:
                    v = vus["values"]
                else:
                    v = vus
                metrics.vus = int(v.get("value", v.get("max", 0)))
            elif "vus_max" in m:
                vus_max = m["vus_max"]
                if "values" in vus_max:
                    v = vus_max["values"]
                else:
                    v = vus_max
                metrics.vus = int(v.get("value", v.get("max", 0)))
            
            # HTTP 请求失败率
            if "http_req_failed" in m:
                failed = m["http_req_failed"]
                if "values" in failed:
                    v = failed["values"]
                else:
                    v = failed
                # K6 v1.x: value 是失败率 (0-1)
                # 或者通过 passes/fails 计算
                if "value" in v:
                    fail_rate = float(v.get("value", 0))
                    metrics.error_rate = fail_rate * 100
                elif "fails" in v and "passes" in v:
                    fails = int(v.get("fails", 0))
                    passes = int(v.get("passes", 0))
                    total = fails + passes
                    if total > 0:
                        metrics.error_rate = (fails / total) * 100
                metrics.success_rate = 100 - metrics.error_rate
        
        # 解析 root_group 中的检查失败
        if "root_group" in data:
            self._parse_group_errors(data["root_group"], errors)
        
        return metrics, errors
    
    def _parse_group_errors(self, group: dict, errors: list[TestError]):
        """Parse errors from group checks."""
        if "checks" in group:
            checks = group["checks"]
            # checks 是字典格式: {"check_name": {"passes": x, "fails": y}}
            if isinstance(checks, dict):
                for check_name, check_data in checks.items():
                    if isinstance(check_data, dict):
                        fails = check_data.get("fails", 0)
                        if fails > 0:
                            errors.append(TestError(
                                code="CHECK_FAILED",
                                count=fails,
                                message=check_data.get("name", check_name)
                            ))
            # 兼容列表格式 (旧版本)
            elif isinstance(checks, list):
                for check in checks:
                    if isinstance(check, dict):
                        fails = check.get("fails", 0)
                        if fails > 0:
                            errors.append(TestError(
                                code="CHECK_FAILED",
                                count=fails,
                                message=check.get("name", "Unknown check")
                            ))
        
        # 递归处理子 group
        if "groups" in group:
            groups = group["groups"]
            if isinstance(groups, dict):
                for subgroup in groups.values():
                    if isinstance(subgroup, dict):
                        self._parse_group_errors(subgroup, errors)
            elif isinstance(groups, list):
                for subgroup in groups:
                    if isinstance(subgroup, dict):
                        self._parse_group_errors(subgroup, errors)
    
    def parse_stdout_progress(self, stdout: str) -> dict:
        """Parse real-time progress from K6 stdout.
        
        Args:
            stdout: K6 stdout content
            
        Returns:
            Dict with vus, iterations, rps
        """
        result = {
            "vus": 0,
            "iterations": 0,
            "rps": 0.0
        }
        
        lines = [l for l in stdout.strip().split("\n") if l.strip()]
        if not lines:
            return result
        
        last_line = lines[-1]
        
        # 匹配 VUs
        vus_match = re.search(r"(\d+)\s+VUs?", last_line)
        if vus_match:
            result["vus"] = int(vus_match.group(1))
        
        # 匹配完成的迭代次数
        iter_match = re.search(r"(\d+)\s+complete", last_line)
        if iter_match:
            result["iterations"] = int(iter_match.group(1))
        
        return result
