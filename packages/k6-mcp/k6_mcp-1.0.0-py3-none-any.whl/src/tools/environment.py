"""Environment Tools - set_environment, use_environment, list_environments."""

from typing import Optional

from ..server import mcp
from ..shared import storage


@mcp.tool()
def set_environment(
    name: str,
    base_url: str,
    headers: Optional[dict] = None,
    auth_type: Optional[str] = None,
    auth_token: Optional[str] = None,
    auth_username: Optional[str] = None,
    auth_password: Optional[str] = None
) -> dict:
    """配置测试环境。
    
    Args:
        name: 环境名称，如 "local", "staging", "production"
        base_url: 基础 URL，如 "http://localhost:3000"
        headers: 自定义请求头
        auth_type: 认证类型，"bearer" 或 "basic"
        auth_token: Bearer token（当 auth_type 为 "bearer" 时）
        auth_username: 用户名（当 auth_type 为 "basic" 时）
        auth_password: 密码（当 auth_type 为 "basic" 时）
    
    Returns:
        配置结果
    """
    config = {
        "baseUrl": base_url,
        "headers": headers or {},
    }
    
    if auth_type:
        config["auth"] = {
            "type": auth_type,
            "token": auth_token,
            "username": auth_username,
            "password": auth_password
        }
    
    return storage.set_environment(name, config)


@mcp.tool()
def use_environment(name: str) -> dict:
    """切换当前使用的测试环境。
    
    Args:
        name: 环境名称
    
    Returns:
        切换结果
    """
    return storage.use_environment(name)


@mcp.tool()
def list_environments() -> dict:
    """列出所有配置的测试环境。
    
    Returns:
        环境列表和当前使用的环境
    """
    return storage.list_environments()


@mcp.tool()
def get_environment_config() -> dict:
    """获取当前环境的配置。
    
    Returns:
        当前环境配置，可用于生成测试脚本
    """
    env = storage.get_current_environment()
    if not env:
        return {"error": True, "message": "未选择环境，请先使用 use_environment 选择环境"}
    
    return {
        "name": env.get("name"),
        "baseUrl": env.get("base_url"),
        "headers": env.get("headers", {}),
        "auth": {
            "type": env.get("auth_type"),
            "token": env.get("auth_token"),
            "username": env.get("auth_username")
            # 不返回密码
        } if env.get("auth_type") else None
    }
