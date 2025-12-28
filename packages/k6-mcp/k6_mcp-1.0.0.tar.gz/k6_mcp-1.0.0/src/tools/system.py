"""System Tools - check_k6, set_thresholds, export_report, analyze_result."""

import json
import os
from datetime import datetime
from typing import Literal, Optional

from ..server import mcp
from ..shared import executor


@mcp.tool()
def check_k6() -> dict:
    """检查 K6 安装状态。
    
    Returns:
        K6 安装信息，包括版本和安装指南
    """
    return executor.check_k6_installed()


@mcp.tool()
def set_thresholds(
    avg_duration: Optional[float] = None,
    p95_duration: Optional[float] = None,
    error_rate: Optional[float] = None,
    min_rps: Optional[float] = None
) -> dict:
    """设置性能阈值，用于判断测试是否通过。
    
    Args:
        avg_duration: 平均响应时间阈值（毫秒）
        p95_duration: P95 响应时间阈值（毫秒）
        error_rate: 最大错误率阈值（百分比，如 5.0 表示 5%）
        min_rps: 最小 RPS 阈值
    
    Returns:
        阈值配置
    """
    thresholds = {}
    
    if avg_duration is not None:
        thresholds["http_req_duration"] = [f"avg<{avg_duration}"]
    
    if p95_duration is not None:
        if "http_req_duration" in thresholds:
            thresholds["http_req_duration"].append(f"p(95)<{p95_duration}")
        else:
            thresholds["http_req_duration"] = [f"p(95)<{p95_duration}"]
    
    if error_rate is not None:
        thresholds["http_req_failed"] = [f"rate<{error_rate / 100}"]
    
    if min_rps is not None:
        thresholds["http_reqs"] = [f"rate>{min_rps}"]
    
    # 生成 K6 thresholds 代码片段
    threshold_code = "export const options = {\n  thresholds: {\n"
    for metric, conditions in thresholds.items():
        conditions_str = ", ".join([f'"{c}"' for c in conditions])
        threshold_code += f"    '{metric}': [{conditions_str}],\n"
    threshold_code += "  }\n};"
    
    return {
        "thresholds": thresholds,
        "code": threshold_code,
        "usage": "将上面的 code 添加到你的 K6 脚本中"
    }


def _generate_html_report(report: dict) -> str:
    """Generate HTML report content."""
    summary = report.get("summary", {})
    errors = report.get("errors", [])
    
    # 判断状态
    status = report.get("status", "unknown")
    status_color = "#22c55e" if status == "completed" else "#ef4444"
    status_text = "✅ 测试通过" if status == "completed" else "❌ 测试失败"
    
    # 性能评级
    avg_duration = summary.get("avgDuration", 0)
    if avg_duration < 100:
        perf_grade = "A"
        perf_color = "#22c55e"
    elif avg_duration < 300:
        perf_grade = "B"
        perf_color = "#84cc16"
    elif avg_duration < 500:
        perf_grade = "C"
        perf_color = "#eab308"
    elif avg_duration < 1000:
        perf_grade = "D"
        perf_color = "#f97316"
    else:
        perf_grade = "F"
        perf_color = "#ef4444"
    
    errors_html = ""
    if errors:
        errors_html = "<h2>❌ 错误列表</h2><table><tr><th>错误码</th><th>次数</th><th>描述</th></tr>"
        for e in errors:
            errors_html += f"<tr><td>{e.get('code', '')}</td><td>{e.get('count', 0)}</td><td>{e.get('message', '')}</td></tr>"
        errors_html += "</table>"
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>K6 性能测试报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #6366f1, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .meta {{
            color: #888;
            margin-bottom: 30px;
        }}
        .status-bar {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .status {{
            font-size: 1.5rem;
            font-weight: bold;
            color: {status_color};
        }}
        .grade {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: {perf_color};
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            font-weight: bold;
            color: #fff;
            box-shadow: 0 4px 20px {perf_color}40;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .metric-card .label {{
            font-size: 0.9rem;
            color: #888;
            margin-bottom: 8px;
        }}
        .metric-card .value {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #fff;
        }}
        .metric-card .unit {{
            font-size: 0.9rem;
            color: #666;
        }}
        h2 {{
            font-size: 1.3rem;
            margin: 30px 0 15px;
            color: #a855f7;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            overflow: hidden;
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{
            background: rgba(255,255,255,0.05);
            font-weight: 600;
        }}
        .percentiles {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 10px;
        }}
        .percentile {{
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }}
        .percentile .name {{
            font-size: 0.8rem;
            color: #888;
        }}
        .percentile .value {{
            font-size: 1.2rem;
            font-weight: bold;
            color: #6366f1;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 K6 性能测试报告</h1>
        <p class="meta">测试 ID: {report.get('testId', 'N/A')} | 生成时间: {report.get('generatedAt', 'N/A')}</p>
        
        <div class="status-bar">
            <span class="status">{status_text}</span>
            <div class="grade">{perf_grade}</div>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="label">平均响应时间</div>
                <div class="value">{summary.get('avgDuration', 0):.1f}<span class="unit">ms</span></div>
            </div>
            <div class="metric-card">
                <div class="label">总请求数</div>
                <div class="value">{summary.get('totalRequests', 0):,}</div>
            </div>
            <div class="metric-card">
                <div class="label">吞吐量 (RPS)</div>
                <div class="value">{summary.get('rps', 0):.1f}<span class="unit">/s</span></div>
            </div>
            <div class="metric-card">
                <div class="label">成功率</div>
                <div class="value">{summary.get('successRate', 0):.1f}<span class="unit">%</span></div>
            </div>
        </div>
        
        <h2>📊 响应时间分布</h2>
        <div class="percentiles">
            <div class="percentile">
                <div class="name">MIN</div>
                <div class="value">{summary.get('minDuration', 0):.1f}ms</div>
            </div>
            <div class="percentile">
                <div class="name">P50</div>
                <div class="value">{summary.get('p50Duration', 0):.1f}ms</div>
            </div>
            <div class="percentile">
                <div class="name">P90</div>
                <div class="value">{summary.get('p90Duration', 0):.1f}ms</div>
            </div>
            <div class="percentile">
                <div class="name">P95</div>
                <div class="value">{summary.get('p95Duration', 0):.1f}ms</div>
            </div>
            <div class="percentile">
                <div class="name">MAX</div>
                <div class="value">{summary.get('maxDuration', 0):.1f}ms</div>
            </div>
        </div>
        
        {errors_html}
        
        <div class="footer">
            Generated by k6-mcp-pro | Powered by K6 & MCP
        </div>
    </div>
</body>
</html>"""
    return html


@mcp.tool()
def export_report(
    test_id: str,
    format: Literal["json", "html"] = "json",
    output_path: Optional[str] = None
) -> dict:
    """导出测试报告。
    
    Args:
        test_id: 测试 ID
        format: 报告格式，"json" 或 "html"
        output_path: 输出文件路径（可选）
    
    Returns:
        导出结果和文件路径
    """
    result = executor.get_result(test_id)
    
    if result.get("error"):
        return result
    
    # 构建报告数据
    report = {
        "reportVersion": "1.0",
        "generatedAt": datetime.now().isoformat(),
        "testId": test_id,
        "status": result.get("status"),
        "summary": result.get("summary", {}),
        "errors": result.get("errors", [])
    }
    
    # 确定输出路径和内容
    ext = "html" if format == "html" else "json"
    if not output_path:
        output_path = f"k6-report-{test_id[:8]}.{ext}"
    
    # 生成内容
    if format == "html":
        content = _generate_html_report(report)
    else:
        content = json.dumps(report, indent=2, ensure_ascii=False)
    
    # 写入文件
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return {"error": True, "message": f"导出失败: {str(e)}"}
    
    return {
        "success": True,
        "format": format,
        "path": os.path.abspath(output_path),
        "message": f"报告已导出到 {output_path}"
    }


@mcp.tool()
def analyze_result(test_id: str) -> dict:
    """分析测试结果并给出结构化的分析数据供 AI 分析。
    
    这个工具返回结构化的分析数据，AI 可以基于此给出优化建议。
    
    Args:
        test_id: 测试 ID
    
    Returns:
        结构化的分析数据，包含性能评级、问题列表、优化建议方向
    """
    result = executor.get_result(test_id)
    
    if result.get("error"):
        return result
    
    summary = result.get("summary", {})
    errors = result.get("errors", [])
    
    # 性能评级
    avg_duration = summary.get("avgDuration", 0)
    p95_duration = summary.get("p95Duration", 0)
    error_rate = 100 - summary.get("successRate", 100)
    rps = summary.get("rps", 0)
    
    # 评分规则
    issues = []
    suggestions = []
    
    # 平均响应时间分析
    if avg_duration > 1000:
        issues.append({
            "type": "critical",
            "metric": "avgDuration",
            "value": avg_duration,
            "threshold": 1000,
            "message": "平均响应时间过长 (>1000ms)"
        })
        suggestions.append("考虑添加缓存、优化数据库查询、使用 CDN")
    elif avg_duration > 500:
        issues.append({
            "type": "warning",
            "metric": "avgDuration",
            "value": avg_duration,
            "threshold": 500,
            "message": "平均响应时间偏高 (>500ms)"
        })
        suggestions.append("检查是否有 N+1 查询、考虑异步处理")
    elif avg_duration > 200:
        issues.append({
            "type": "info",
            "metric": "avgDuration",
            "value": avg_duration,
            "threshold": 200,
            "message": "平均响应时间可以优化 (>200ms)"
        })
    
    # P95 分析
    if p95_duration > 2000:
        issues.append({
            "type": "critical",
            "metric": "p95Duration",
            "value": p95_duration,
            "threshold": 2000,
            "message": "P95 响应时间过长，存在严重的长尾问题"
        })
        suggestions.append("检查是否有慢查询、外部 API 调用超时")
    elif p95_duration > avg_duration * 3:
        issues.append({
            "type": "warning",
            "metric": "p95Duration",
            "value": p95_duration,
            "message": f"P95 是平均值的 {p95_duration/avg_duration:.1f} 倍，响应时间不稳定"
        })
        suggestions.append("检查是否有间歇性的性能问题")
    
    # 错误率分析
    if error_rate > 10:
        issues.append({
            "type": "critical",
            "metric": "errorRate",
            "value": error_rate,
            "threshold": 10,
            "message": f"错误率过高: {error_rate:.1f}%"
        })
        suggestions.append("检查服务器日志、增加超时时间、检查连接池配置")
    elif error_rate > 1:
        issues.append({
            "type": "warning",
            "metric": "errorRate",
            "value": error_rate,
            "threshold": 1,
            "message": f"存在错误: {error_rate:.1f}%"
        })
    
    # 吞吐量分析
    if rps < 10:
        issues.append({
            "type": "info",
            "metric": "rps",
            "value": rps,
            "message": f"吞吐量较低: {rps:.1f} req/s"
        })
        suggestions.append("考虑增加服务器实例、使用负载均衡")
    
    # 计算总体评级
    critical_count = sum(1 for i in issues if i["type"] == "critical")
    warning_count = sum(1 for i in issues if i["type"] == "warning")
    
    if critical_count > 0:
        grade = "F"
        overall = "性能存在严重问题，需要立即优化"
    elif warning_count > 1:
        grade = "C"
        overall = "性能有待改善"
    elif warning_count > 0:
        grade = "B"
        overall = "性能良好，有优化空间"
    elif avg_duration < 100:
        grade = "A"
        overall = "性能优秀"
    else:
        grade = "B"
        overall = "性能良好"
    
    return {
        "testId": test_id,
        "status": result.get("status"),
        "grade": grade,
        "overall": overall,
        "metrics": {
            "avgDuration": avg_duration,
            "p95Duration": p95_duration,
            "p99Duration": summary.get("p99Duration", 0),
            "rps": rps,
            "errorRate": error_rate,
            "totalRequests": summary.get("totalRequests", 0)
        },
        "issues": issues,
        "suggestions": suggestions,
        "errors": errors
    }
