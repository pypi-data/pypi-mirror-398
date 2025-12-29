"""
OAuth 2.0 资源服务器实现

Uno 作为资源服务器，mcpmarket 作为认证服务器。
遵循 MCP 规范和 RFC 9728 (Protected Resource Metadata)。
"""

from typing import Dict, Any, Optional
from datetime import datetime
import httpx

from ..config import settings
from ..utils import get_logger

logger = get_logger("auth.oauth_server")


class UnoResourceServer:
    """
    Uno 资源服务器
    
    实现 OAuth 2.0 资源服务器规范：
    1. 未认证请求返回 401 + WWW-Authenticate
    2. 提供 /.well-known/oauth-protected-resource 端点
    3. 验证 access token（通过 mcpmarket）
    """
    
    def __init__(self):
        self.mcpmarket_url = settings.mcpmarket_url
        self._token_cache: Dict[str, Dict[str, Any]] = {}  # token -> user_info
        self._cache_ttl = 300  # 5 分钟缓存
        
        logger.info(f"资源服务器初始化, mcpmarket={self.mcpmarket_url}")
    
    def get_protected_resource_metadata(self) -> Dict[str, Any]:
        """
        获取 Protected Resource Metadata (RFC 9728)
        
        这个端点告诉客户端去哪里进行 OAuth 认证。
        """
        return {
            "resource": settings.server_url,
            "authorization_servers": [
                self.mcpmarket_url
            ],
            "bearer_methods_supported": ["header"],
            "resource_documentation": f"{settings.server_url}/docs",
            "resource_signing_alg_values_supported": ["RS256"]
        }
    
    def get_www_authenticate_header(self) -> str:
        """
        生成 WWW-Authenticate header
        
        根据 RFC 9728，包含 resource_metadata 参数指向 well-known 端点。
        """
        resource_metadata_url = f"{settings.server_url}/.well-known/oauth-protected-resource"
        return f'Bearer resource_metadata="{resource_metadata_url}"'
    
    async def verify_access_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        验证 access token
        
        通过 mcpmarket API 验证 token 并获取用户信息。
        
        Args:
            access_token: Bearer token
            
        Returns:
            用户信息字典，如果 token 无效则返回 None
        """
        # 检查缓存
        if access_token in self._token_cache:
            cached = self._token_cache[access_token]
            if (datetime.now() - cached['cached_at']).total_seconds() < self._cache_ttl:
                return cached['user_info']
            else:
                del self._token_cache[access_token]
        
        try:
            # 调用 mcpmarket API 验证 token
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.mcpmarket_url}/api/uno/verify-token",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('valid'):
                        user_info = {
                            'user_id': data.get('user_id'),
                            'username': data.get('username'),
                            'email': data.get('email')
                        }
                        
                        # 缓存
                        self._token_cache[access_token] = {
                            'user_info': user_info,
                            'cached_at': datetime.now()
                        }
                        
                        logger.debug(f"Token 验证成功: user_id={user_info['user_id']}")
                        return user_info
                
                logger.warning(f"Token 验证失败: status={response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Token 验证异常: {e}")
            return None
    
    def clear_token_cache(self, access_token: str = None):
        """清除 token 缓存"""
        if access_token:
            self._token_cache.pop(access_token, None)
        else:
            self._token_cache.clear()


# 全局资源服务器实例
resource_server = UnoResourceServer()

