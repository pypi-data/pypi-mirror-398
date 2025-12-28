"""Scenario Tools - run_scenario, list_scenarios."""

from typing import Literal

from ..server import mcp
from ..shared import executor

# 预设场景配置
SCENARIOS = {
    "smoke": {
        "name": "冒烟测试",
        "description": "快速验证接口是否正常工作",
        "vus": 1,
        "duration": "10s"
    },
    "load": {
        "name": "负载测试",
        "description": "模拟正常负载下的性能表现",
        "vus": 50,
        "duration": "5m"
    },
    "stress": {
        "name": "压力测试",
        "description": "逐渐增加负载直到系统极限",
        "stages": [
            {"duration": "1m", "target": 50},
            {"duration": "2m", "target": 100},
            {"duration": "2m", "target": 200},
            {"duration": "1m", "target": 0}
        ]
    },
    "spike": {
        "name": "峰值测试",
        "description": "模拟突发流量峰值",
        "stages": [
            {"duration": "30s", "target": 10},
            {"duration": "10s", "target": 500},
            {"duration": "1m", "target": 500},
            {"duration": "10s", "target": 10},
            {"duration": "30s", "target": 0}
        ]
    },
    "soak": {
        "name": "持久测试",
        "description": "长时间运行以发现内存泄漏等问题",
        "vus": 50,
        "duration": "30m"
    }
}


def _wrap_script_with_options(script: str, scenario: dict) -> str:
    """Wrap script with K6 options based on scenario."""
    options_lines = []
    
    if "stages" in scenario:
        stages_str = ",\n    ".join([
            f'{{ duration: "{s["duration"]}", target: {s["target"]} }}'
            for s in scenario["stages"]
        ])
        options_lines.append(f"  stages: [\n    {stages_str}\n  ]")
    else:
        if "vus" in scenario:
            options_lines.append(f"  vus: {scenario['vus']}")
        if "duration" in scenario:
            options_lines.append(f'  duration: "{scenario["duration"]}"')
    
    options_block = "export const options = {\n" + ",\n".join(options_lines) + "\n};\n\n"
    
    # 检查脚本是否已有 options
    if "export const options" in script or "export let options" in script:
        return script  # 不覆盖已有配置
    
    # 在 import 语句后插入 options
    import_end = 0
    lines = script.split("\n")
    for i, line in enumerate(lines):
        if line.strip().startswith("import "):
            import_end = i + 1
    
    if import_end > 0:
        lines.insert(import_end, "\n" + options_block)
        return "\n".join(lines)
    else:
        return options_block + script


@mcp.tool()
async def run_scenario(
    scenario: Literal["smoke", "load", "stress", "spike", "soak"],
    script: str
) -> dict:
    """运行预设的测试场景。
    
    Args:
        scenario: 场景类型
            - smoke: 冒烟测试 (1 VU, 10s)
            - load: 负载测试 (50 VUs, 5m)
            - stress: 压力测试 (50→100→200→0)
            - spike: 峰值测试 (10→500→10)
            - soak: 持久测试 (50 VUs, 30m)
        script: K6 测试脚本
    
    Returns:
        测试 ID 和状态
    """
    if scenario not in SCENARIOS:
        return {"error": True, "message": f"未知场景: {scenario}"}
    
    config = SCENARIOS[scenario]
    wrapped_script = _wrap_script_with_options(script, config)
    
    # 对于有 stages 的场景，使用较长的默认时长
    if "stages" in config:
        # 计算总时长
        total_duration = sum(
            int(s["duration"].rstrip("sm")) * (60 if "m" in s["duration"] else 1)
            for s in config["stages"]
        )
        duration = f"{total_duration}s"
        vus = max(s["target"] for s in config["stages"])
    else:
        vus = config.get("vus", 10)
        duration = config.get("duration", "30s")
    
    result = await executor.start_test(wrapped_script, vus, duration)
    
    if not result.get("error"):
        result["scenario"] = scenario
        result["scenarioName"] = config["name"]
    
    return result


@mcp.tool()
def list_scenarios() -> dict:
    """列出所有可用的测试场景。
    
    Returns:
        场景列表及其描述
    """
    scenarios = []
    for key, config in SCENARIOS.items():
        scenario_info = {
            "id": key,
            "name": config["name"],
            "description": config["description"]
        }
        
        if "stages" in config:
            scenario_info["type"] = "staged"
            scenario_info["stages"] = config["stages"]
        else:
            scenario_info["type"] = "constant"
            scenario_info["vus"] = config.get("vus")
            scenario_info["duration"] = config.get("duration")
        
        scenarios.append(scenario_info)
    
    return {"scenarios": scenarios}
