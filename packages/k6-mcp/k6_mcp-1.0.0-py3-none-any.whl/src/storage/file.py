"""File Storage - JSON file-based storage for baselines and environments."""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_data_dir() -> Path:
    """Get the data directory for storing baselines and configs."""
    # 使用用户目录下的 .k6-mcp-pro 目录
    data_dir = Path.home() / ".k6-mcp"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@dataclass
class BaselineData:
    """Baseline data structure."""
    name: str
    saved_at: str
    avg_duration: float
    p50_duration: float
    p90_duration: float
    p95_duration: float
    p99_duration: float
    min_duration: float
    max_duration: float
    rps: float
    error_rate: float
    total_requests: int


@dataclass
class EnvironmentConfig:
    """Environment configuration."""
    name: str
    base_url: str
    headers: dict[str, str]
    auth_type: Optional[str] = None
    auth_token: Optional[str] = None
    auth_username: Optional[str] = None
    auth_password: Optional[str] = None


class FileStorage:
    """File-based storage for baselines and environments."""
    
    BASELINES_FILE = "baselines.json"
    ENVIRONMENTS_FILE = "environments.json"
    
    def __init__(self):
        self._data_dir = get_data_dir()
        self._current_env: Optional[str] = None
    
    # ============ Baseline Methods ============
    
    def _get_baselines_path(self) -> Path:
        return self._data_dir / self.BASELINES_FILE
    
    def _load_baselines(self) -> dict[str, dict]:
        """Load baselines from file."""
        path = self._get_baselines_path()
        try:
            if path.exists():
                with open(path, "r") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return {}
    
    def _save_baselines(self, baselines: dict[str, dict]):
        """Save baselines to file atomically."""
        path = self._get_baselines_path()
        temp_path = path.with_suffix(".tmp")
        
        with open(temp_path, "w") as f:
            json.dump(baselines, f, indent=2, ensure_ascii=False)
        
        temp_path.replace(path)
    
    def save_baseline(self, name: str, metrics: dict) -> dict:
        """Save a baseline from test metrics."""
        baselines = self._load_baselines()
        
        baseline = BaselineData(
            name=name,
            saved_at=datetime.now().isoformat(),
            avg_duration=metrics.get("avgDuration", 0),
            p50_duration=metrics.get("p50Duration", 0),
            p90_duration=metrics.get("p90Duration", 0),
            p95_duration=metrics.get("p95Duration", 0),
            p99_duration=metrics.get("p99Duration", 0),
            min_duration=metrics.get("minDuration", 0),
            max_duration=metrics.get("maxDuration", 0),
            rps=metrics.get("rps", 0),
            error_rate=metrics.get("errorRate", 0),
            total_requests=metrics.get("totalRequests", 0)
        )
        
        baselines[name] = asdict(baseline)
        self._save_baselines(baselines)
        
        return {"success": True, "baseline": asdict(baseline)}
    
    def get_baseline(self, name: str) -> Optional[dict]:
        """Get a baseline by name."""
        baselines = self._load_baselines()
        return baselines.get(name)
    
    def list_baselines(self) -> list[dict]:
        """List all baselines."""
        baselines = self._load_baselines()
        return list(baselines.values())
    
    def delete_baseline(self, name: str) -> bool:
        """Delete a baseline by name."""
        baselines = self._load_baselines()
        if name in baselines:
            del baselines[name]
            self._save_baselines(baselines)
            return True
        return False
    
    def compare_baseline(self, name: str, current_metrics: dict) -> dict:
        """Compare current metrics with a baseline."""
        baseline = self.get_baseline(name)
        if not baseline:
            return {"error": True, "message": f"基线 '{name}' 不存在"}
        
        def calc_change(before: float, after: float) -> tuple[str, str]:
            if before == 0:
                return "+∞%", "unknown"
            change = ((after - before) / before) * 100
            change_str = f"{'+' if change > 0 else ''}{change:.1f}%"
            
            # 对于延迟，增加是回归；对于 RPS，减少是回归
            if abs(change) < 5:
                status = "stable"
            elif change > 0:
                status = "regression"
            else:
                status = "improvement"
            
            return change_str, status
        
        comparison = {}
        metrics_to_compare = [
            ("avgDuration", "avg_duration"),
            ("p95Duration", "p95_duration"),
            ("rps", "rps"),
            ("errorRate", "error_rate")
        ]
        
        overall_regression = False
        overall_improvement = False
        
        for current_key, baseline_key in metrics_to_compare:
            before = baseline.get(baseline_key, 0)
            after = current_metrics.get(current_key, 0)
            change_str, status = calc_change(before, after)
            
            # RPS 的逻辑相反
            if current_key == "rps" and status == "regression":
                status = "improvement"
            elif current_key == "rps" and status == "improvement":
                status = "regression"
            
            comparison[current_key] = {
                "before": before,
                "after": after,
                "change": change_str,
                "status": status
            }
            
            if status == "regression":
                overall_regression = True
            elif status == "improvement":
                overall_improvement = True
        
        if overall_regression:
            overall_status = "regression"
        elif overall_improvement:
            overall_status = "improvement"
        else:
            overall_status = "stable"
        
        return {
            "baseline": baseline,
            "current": current_metrics,
            "comparison": comparison,
            "overallStatus": overall_status
        }
    
    # ============ Environment Methods ============
    
    def _get_environments_path(self) -> Path:
        return self._data_dir / self.ENVIRONMENTS_FILE
    
    def _load_environments(self) -> dict[str, dict]:
        """Load environments from file."""
        path = self._get_environments_path()
        try:
            if path.exists():
                with open(path, "r") as f:
                    data = json.load(f)
                    self._current_env = data.get("_current")
                    return data.get("environments", {})
        except (json.JSONDecodeError, IOError):
            pass
        return {}
    
    def _save_environments(self, environments: dict[str, dict]):
        """Save environments to file atomically."""
        path = self._get_environments_path()
        temp_path = path.with_suffix(".tmp")
        
        data = {
            "_current": self._current_env,
            "environments": environments
        }
        
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        temp_path.replace(path)
    
    def set_environment(self, name: str, config: dict) -> dict:
        """Set or update an environment configuration."""
        environments = self._load_environments()
        
        env_config = EnvironmentConfig(
            name=name,
            base_url=config.get("baseUrl", ""),
            headers=config.get("headers", {}),
            auth_type=config.get("auth", {}).get("type"),
            auth_token=config.get("auth", {}).get("token"),
            auth_username=config.get("auth", {}).get("username"),
            auth_password=config.get("auth", {}).get("password")
        )
        
        environments[name] = asdict(env_config)
        self._save_environments(environments)
        
        return {"success": True, "environment": name}
    
    def use_environment(self, name: str) -> dict:
        """Switch to an environment."""
        environments = self._load_environments()
        
        if name not in environments:
            return {"error": True, "message": f"环境 '{name}' 不存在"}
        
        self._current_env = name
        self._save_environments(environments)
        
        return {"success": True, "current": name}
    
    def get_current_environment(self) -> Optional[dict]:
        """Get current environment configuration."""
        if not self._current_env:
            self._load_environments()
        
        if not self._current_env:
            return None
        
        environments = self._load_environments()
        return environments.get(self._current_env)
    
    def list_environments(self) -> dict:
        """List all environments."""
        environments = self._load_environments()
        return {
            "current": self._current_env,
            "environments": list(environments.keys())
        }
    
    def delete_environment(self, name: str) -> bool:
        """Delete an environment."""
        environments = self._load_environments()
        if name in environments:
            del environments[name]
            if self._current_env == name:
                self._current_env = None
            self._save_environments(environments)
            return True
        return False
    
    # ============ Saved APIs Methods ============
    
    APIS_FILE = "saved_apis.json"
    
    def _get_apis_path(self) -> Path:
        return self._data_dir / self.APIS_FILE
    
    def _load_apis(self) -> dict[str, dict]:
        """Load saved APIs from file."""
        path = self._get_apis_path()
        try:
            if path.exists():
                with open(path, "r") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return {}
    
    def _save_apis(self, apis: dict[str, dict]):
        """Save APIs to file atomically."""
        path = self._get_apis_path()
        temp_path = path.with_suffix(".tmp")
        
        with open(temp_path, "w") as f:
            json.dump(apis, f, indent=2, ensure_ascii=False)
        
        temp_path.replace(path)
    
    def save_api(self, name: str, curl: str, description: str = "") -> dict:
        """Save an API configuration."""
        from ..utils.curl_parser import parse_curl
        
        apis = self._load_apis()
        
        # 解析 cURL 获取基本信息
        parsed = parse_curl(curl)
        
        api_data = {
            "name": name,
            "curl": curl,
            "description": description,
            "method": parsed.method,
            "url": parsed.url,
            "saved_at": datetime.now().isoformat()
        }
        
        apis[name] = api_data
        self._save_apis(apis)
        
        return {
            "success": True, 
            "message": f"接口 '{name}' 已保存",
            "api": {
                "name": name,
                "method": parsed.method,
                "url": parsed.url
            }
        }
    
    def get_api(self, name: str) -> Optional[dict]:
        """Get a saved API by name."""
        apis = self._load_apis()
        return apis.get(name)
    
    def list_apis(self) -> list[dict]:
        """List all saved APIs."""
        apis = self._load_apis()
        result = []
        for name, api in apis.items():
            result.append({
                "name": api.get("name", name),
                "method": api.get("method", "GET"),
                "url": api.get("url", ""),
                "description": api.get("description", ""),
                "saved_at": api.get("saved_at", "")
            })
        return result
    
    def delete_api(self, name: str) -> bool:
        """Delete a saved API by name."""
        apis = self._load_apis()
        if name in apis:
            del apis[name]
            self._save_apis(apis)
            return True
        return False

