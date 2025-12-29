"""
Well-known 端点配置

生成 MCP 协议发现信息和 OAuth 配置。
"""

from typing import Dict, Any

from ..config import settings


def generate_wellknown_mcp() -> Dict[str, Any]:
    """
    生成 .well-known/mcp.json 内容
    
    用于 MCP 协议发现和 OAuth 配置。
    """
    return {
        "version": "2024-11-05",
        "name": "Uno MCP Server",
        "description": "All-in-One MCP Gateway with Skills - 集成的 MCP 网关服务",
        "vendor": {
            "name": "MCPMarket",
            "url": settings.mcpmarket_url
        },
        "endpoints": {
            "message": f"{settings.server_url}/mcp",
            "sse": f"{settings.server_url}/mcp/sse"
        },
        "authentication": {
            "type": "oauth2",
            "authorization_url": f"{settings.mcpmarket_url}/oauth/authorize",
            "token_url": f"{settings.mcpmarket_url}/oauth/token",
            "scopes": {
                "read": "读取服务和工具信息",
                "write": "调用工具和执行操作"
            }
        },
        "capabilities": {
            "tools": {
                "listChanged": False
            },
            "skills": True,
            "sandbox": settings.sandbox_enabled
        },
        "contact": {
            "url": f"{settings.mcpmarket_url}/support"
        }
    }


def generate_oauth_metadata() -> Dict[str, Any]:
    """
    生成 OAuth 2.0 授权服务器元数据
    
    符合 RFC 8414 标准。
    """
    return {
        "issuer": settings.mcpmarket_url,
        "authorization_endpoint": f"{settings.mcpmarket_url}/oauth/authorize",
        "token_endpoint": f"{settings.mcpmarket_url}/oauth/token",
        "userinfo_endpoint": f"{settings.mcpmarket_url}/oauth/userinfo",
        "revocation_endpoint": f"{settings.mcpmarket_url}/oauth/revoke",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "scopes_supported": ["read", "write", "openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
        "code_challenge_methods_supported": ["S256"]
    }

