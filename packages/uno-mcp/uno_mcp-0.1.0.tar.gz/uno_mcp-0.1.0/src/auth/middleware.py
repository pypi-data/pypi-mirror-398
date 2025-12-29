"""
认证中间件

验证请求中的 token，获取用户信息。
通过 mcpmarket HTTP API 访问，不再直接访问数据库。
"""

from typing import Optional, Dict, Any
import httpx

from ..config import settings
from ..utils import get_logger

logger = get_logger("auth.middleware")


class AuthClient:
    """认证客户端 - 通过 mcpmarket HTTP API 集成"""
    
    def __init__(self):
        self.mcpmarket_api_url = settings.mcpmarket_api_url
        logger.info("AuthClient 已初始化（使用 HTTP API）")
    
    async def verify_token(self, access_token: str) -> Optional[str]:
        """
        验证 access_token，返回 user_id
        
        通过 mcpmarket API 验证 token。
        
        Args:
            access_token: 访问令牌
            
        Returns:
            用户 ID，如果 token 无效则返回 None
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.mcpmarket_api_url}/uno/verify-token",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('valid'):
                        user_id = data.get('user_id')
                        logger.debug(f"Token 验证成功: user_id={user_id}")
                        return user_id
                
                logger.warning(f"Token 验证失败: status={response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"验证 token 失败: {e}")
            return None
    
    async def get_user_info(self, user_id: str, access_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取用户信息
        
        通过 mcpmarket API 获取用户信息。
        
        Args:
            user_id: 用户 ID
            access_token: 访问令牌（可选，如果提供则获取完整信息）
            
        Returns:
            用户信息字典
        """
        # 如果没有提供 access_token，返回基本信息
        if not access_token:
            return {
                'id': user_id,
                'username': None,
                'email': None,
            }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.mcpmarket_api_url}/uno/user-info",
                    params={"user_id": user_id},
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"获取用户信息成功: user_id={user_id}")
                    return data
                
                logger.warning(f"获取用户信息失败: status={response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None


# 全局认证客户端实例
auth_client = AuthClient()


async def verify_token(authorization: Optional[str] = None) -> str:
    """
    验证请求中的 token
    
    Args:
        authorization: Authorization header
        
    Returns:
        用户 ID
    """
    # 如果没有 Authorization header，使用默认用户
    if not authorization:
        logger.debug("未提供 Authorization header，使用默认用户")
        return "default_user"
    
    # 解析 Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        logger.warning(f"无效的 Authorization 格式，使用默认用户")
        return "default_user"
    
    access_token = parts[1]
    
    # 验证 token（通过 HTTP API）
    user_id = await auth_client.verify_token(access_token)
    if not user_id:
        logger.warning("Token 验证失败，使用默认用户")
        return "default_user"
    
    return user_id


async def get_current_user(user_id: str) -> Dict[str, Any]:
    """
    获取当前用户信息
    
    Args:
        user_id: 用户 ID
        
    Returns:
        用户信息
    """
    # 如果是默认用户
    if user_id == "default_user":
        return {
            'id': 'default_user',
            'username': 'default_user',
            'email': 'default@uno.local',
            'display_name': '默认测试用户',
            'auth_type': 'default',
        }
    
    user_info = await auth_client.get_user_info(user_id)
    if not user_info:
        return {
            'id': user_id,
            'username': 'unknown',
            'display_name': '未知用户',
        }
    
    return user_info

