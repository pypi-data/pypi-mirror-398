"""
Server 注册表

管理所有可用的 MCP server 配置，支持从 mcpmarket 动态获取。
通过 mcpmarket HTTP API 访问，不再直接访问数据库。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx

from ..config import settings
from ..utils import get_logger
from .http_client import HTTPMCPClient

logger = get_logger("registry.server_registry")


class ServerRegistry:
    """
    Server 注册表
    
    功能：
    - 从 mcpmarket HTTP API 获取直连 server 列表
    - 缓存 server 配置和 tools 信息
    - 管理 MCP 客户端连接池
    """
    
    def __init__(self):
        """初始化"""
        self._servers: Dict[str, Dict[str, Any]] = {}
        self._clients: Dict[str, HTTPMCPClient] = {}
        self._last_refresh: Optional[datetime] = None
        self._cache_ttl = 300  # 5 分钟缓存
        self.mcpmarket_api_url = settings.mcpmarket_api_url
        
        logger.info("ServerRegistry 已初始化（使用 HTTP API）")
    
    async def refresh(self, force: bool = False) -> bool:
        """
        刷新 server 列表
        
        Args:
            force: 是否强制刷新
            
        Returns:
            是否刷新成功
        """
        # 检查缓存
        if not force and self._last_refresh:
            elapsed = (datetime.now() - self._last_refresh).total_seconds()
            if elapsed < self._cache_ttl:
                return True
        
        try:
            # 从 mcpmarket HTTP API 获取直连（hosted）server 列表
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.mcpmarket_api_url}/uno/servers",
                    params={"limit": 100}
                )
                
                if response.status_code != 200:
                    raise Exception(f"API 请求失败: HTTP {response.status_code}")
                
                data = response.json()
                servers = data.get("servers", [])
            
            self._servers = {}
            for server in servers:
                # 使用 name 或 alias 作为标识
                name = server.get("name") or "unknown"
                
                # 构建直连 URL
                server_id = server.get("server_id")
                if server_id:
                    direct_url = f"{settings.mcpmarket_url}/mcp/{server_id}"
                else:
                    logger.warning(f"Server {name} 缺少 server_id，跳过")
                    continue
                
                self._servers[name] = {
                    "name": name,
                    "description": server.get("description", "") or name,
                    "url": direct_url,
                    "tools": server.get("tools", []),
                    "metadata": {
                        "server_id": server_id,
                        "stars": server.get("stars", 0),
                    }
                }
            
            self._last_refresh = datetime.now()
            logger.info(f"刷新 server 列表成功: count={len(self._servers)}")
            return True
            
        except Exception as e:
            logger.error(f"刷新 server 列表失败: {e}")
            # 如果有缓存，继续使用缓存
            if self._servers:
                logger.warning("使用缓存的 server 列表")
                return True
            # 加载默认配置
            self._load_default_servers()
            return len(self._servers) > 0
    
    def _load_default_servers(self):
        """加载默认的 server 配置（用于测试）"""
        self._servers = {
            "time": {
                "name": "time",
                "description": "获取当前时间",
                "url": f"{settings.mcpmarket_url}/mcp/4c31848d8843221aa8274771",
                "tools": [{
                    "name": "get_current_time",
                    "description": "获取当前时间（支持不同时区）",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "timezone": {"type": "string", "description": "时区"}
                        }
                    }
                }]
            },
            "fetch": {
                "name": "fetch",
                "description": "获取网页内容",
                "url": f"{settings.mcpmarket_url}/mcp/d14dc893b4e7b712897b4e19",
                "tools": [{
                    "name": "fetch",
                    "description": "获取网页内容",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL地址"}
                        },
                        "required": ["url"]
                    }
                }]
            }
        }
        logger.info(f"加载默认 server 配置: count={len(self._servers)}")
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """
        列出所有 server（摘要信息）
        
        Returns:
            Server 摘要列表
        """
        return [
            {
                "name": s["name"],
                "description": s["description"]
            }
            for s in self._servers.values()
        ]
    
    async def get_server_detail(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取 server 详细信息（包含完整 tools 定义）
        
        Args:
            name: Server 名称
            
        Returns:
            Server 详情，包含 tools 完整定义
        """
        if name not in self._servers:
            await self.refresh()
        
        server = self._servers.get(name)
        if not server:
            return None
        
        # 如果 tools 信息不完整，尝试从远程获取
        if not server.get("tools"):
            client = await self._get_client(name)
            if client:
                tools = await client.list_tools()
                server["tools"] = tools
                self._servers[name] = server
        
        return server
    
    async def get_tool_definition(
        self,
        server_name: str,
        tool_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取单个 tool 的完整定义
        
        Args:
            server_name: Server 名称
            tool_name: Tool 名称
            
        Returns:
            Tool 定义
        """
        server = await self.get_server_detail(server_name)
        if not server:
            return None
        
        for tool in server.get("tools", []):
            if tool.get("name") == tool_name:
                return tool
        
        return None
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Any:
        """
        调用远程工具
        
        Args:
            server_name: Server 名称
            tool_name: Tool 名称
            arguments: 参数
            user_id: 用户 ID
            
        Returns:
            调用结果
        """
        client = await self._get_client(server_name)
        if not client:
            raise Exception(f"Server '{server_name}' 不存在或不可用")
        
        return await client.call_tool(tool_name, arguments)
    
    async def _get_client(self, server_name: str) -> Optional[HTTPMCPClient]:
        """
        获取或创建 MCP 客户端
        
        Args:
            server_name: Server 名称
            
        Returns:
            MCP 客户端
        """
        if server_name in self._clients:
            return self._clients[server_name]
        
        server = self._servers.get(server_name)
        if not server or not server.get("url"):
            return None
        
        client = HTTPMCPClient(
            server_url=server["url"],
            server_name=server_name
        )
        
        # 初始化连接
        if await client.initialize():
            self._clients[server_name] = client
            return client
        
        return None
    
    async def close(self):
        """关闭所有客户端连接"""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
        logger.info("已关闭所有 MCP 客户端连接")
    
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        导出为字典格式
        
        Returns:
            Server 字典
        """
        return self._servers.copy()


# 全局 Server 注册表实例
server_registry = ServerRegistry()

