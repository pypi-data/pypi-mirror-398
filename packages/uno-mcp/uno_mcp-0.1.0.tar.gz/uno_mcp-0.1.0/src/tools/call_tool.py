"""
call 工具

调用已连接的远程 MCP 工具。
如果未连接，会自动触发 connect 流程。

使用官方 MCP SDK 进行通信。
"""

from typing import Dict, Any, Optional
import httpx

from ..config import settings
from ..utils import get_logger
from ..registry.mcp_client_manager import mcp_client_manager

logger = get_logger("tools.call")


class CallTool:
    """
    调用工具
    
    核心功能：
    - 接收 tool 全名（server.tool_name）和参数
    - 检查用户是否已连接该 server
    - 如果未连接：
      - 非 OAuth server：自动创建连接并继续调用
      - OAuth server：返回需要授权的提示
    - 路由到对应的远程 MCP server
    - 返回执行结果
    """
    
    def __init__(self, server_registry: Any = None):
        """
        初始化
        
        Args:
            server_registry: Server 注册表实例
        """
        self.server_registry = server_registry
        self.mcpmarket_api_url = settings.mcpmarket_api_url
        logger.info("CallTool 已初始化")
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """获取工具定义"""
        return {
            "name": "uno_call_tool",
            "description": """【第二步】执行 MCP Server 上的具体工具。

在调用 uno_discover_servers 获取工具列表后，使用此工具执行具体操作。

【tool_name 格式】
"server_name.tool_name"，例如：
- Time.get_current_time
- Time.convert_time  
- Github.search_repositories
- Fetch.fetch

【自动连接】
- 非认证 server：自动创建连接
- OAuth server：返回授权链接供用户点击

【使用示例】
uno_call_tool(
  tool_name="Time.get_current_time",
  arguments={"timezone": "America/Los_Angeles"}
)""",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "要调用的工具全名，格式：server_name.tool_name"
                    },
                    "arguments": {
                        "type": "object",
                        "description": "工具参数，具体参数见各工具的 inputSchema 定义"
                    }
                },
                "required": ["tool_name", "arguments"]
            }
        }
    
    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        执行工具调用
        
        Args:
            tool_name: 工具全名（server.tool_name）
            arguments: 工具参数
            user_id: 用户 ID
            
        Returns:
            工具执行结果
        """
        logger.info(f"调用工具: {tool_name}, user={user_id}")
        
        # 解析 tool 名称
        parts = tool_name.split(".", 1)
        if len(parts) != 2:
            return {
                "success": False,
                "error": f"无效的工具名称格式: {tool_name}",
                "hint": "格式应为 'server_name.tool_name'"
            }
        
        server_name, remote_tool_name = parts
        
        try:
            # 1. 优先从缓存获取 mcp_url（由 discover_servers 设置）
            cached = mcp_client_manager.get_cached_url(user_id, server_name)
            
            if cached:
                # 缓存命中！直接使用，无需查询 proxy server
                mcp_url = cached["mcp_url"]
                logger.info(f"缓存命中: {server_name} -> {mcp_url}")
                
                try:
                    result = await self._call_remote_tool(mcp_url, remote_tool_name, arguments)
                    return {
                        "success": True,
                        "tool": tool_name,
                        "result": result
                    }
                except Exception as e:
                    # 连接可能已断开，清除缓存，走 fallback 路径
                    logger.warning(f"缓存连接失败，清除缓存: {e}")
                    mcp_client_manager.invalidate_cache(user_id, server_name)
            
            # 2. 缓存未命中或失败，走传统路径（查询 proxy server）
            logger.info(f"缓存未命中，查询 proxy server: {server_name}")
            
            # 从 server_registry 获取 server_id
            server_id = None
            if self.server_registry:
                server_detail = await self.server_registry.get_server_detail(server_name)
                if server_detail:
                    server_id = server_detail.get("metadata", {}).get("server_id")
            
            if not server_id:
                return {
                    "success": False,
                    "error": f"Server '{server_name}' 不存在或非托管服务器",
                    "hint": "请先调用 uno_discover_servers 获取可用的 server 列表"
                }
            
            # 检查连接状态
            connection = await self._check_connection(user_id, server_id)
            
            if not connection.get("connected"):
                if connection.get("requires_auth"):
                    return await self._handle_oauth_required(user_id, server_id, server_name)
                else:
                    connect_result = await self._auto_connect(user_id, server_id, server_name)
                    if not connect_result.get("success"):
                        return connect_result
                    connection = await self._check_connection(user_id, server_id)
            
            # 3. 调用远程工具
            mcp_url = connection.get("mcp_url")
            if not mcp_url:
                return {
                    "success": False,
                    "error": f"无法获取 {server_name} 的连接 URL"
                }
            
            # 缓存这个 mcp_url 供下次使用
            mcp_client_manager.cache_url(user_id, server_name, mcp_url, server_id)
            
            result = await self._call_remote_tool(mcp_url, remote_tool_name, arguments)
            
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"工具调用失败: {tool_name}, error={e}")
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }
    
    async def _check_connection(
        self,
        user_id: str,
        server_id: str
    ) -> Dict[str, Any]:
        """检查用户与 server 的连接状态（使用 server_id）"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.mcpmarket_api_url}/uno/check-connection",
                    params={"user_id": user_id, "server_id": server_id}
                )
                
                if response.status_code == 200:
                    return response.json()
                
                return {"connected": False, "requires_auth": False}
                
        except Exception as e:
            logger.warning(f"检查连接状态失败: {e}")
            return {"connected": False, "requires_auth": False}
    
    async def _auto_connect(
        self,
        user_id: str,
        server_id: str,
        server_name: str = None
    ) -> Dict[str, Any]:
        """自动创建连接（仅用于非 OAuth server，使用 server_id）"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.mcpmarket_api_url}/uno/create-instance",
                    json={
                        "user_id": user_id,
                        "server_id": server_id,  # 使用 server_id
                        "pre_auth": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info(f"自动创建连接成功: {server_name or server_id}")
                        return {"success": True}
                
                return {
                    "success": False,
                    "error": f"自动创建连接失败"
                }
                
        except Exception as e:
            logger.error(f"自动创建连接失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_oauth_required(
        self,
        user_id: str,
        server_id: str,
        server_name: str = None
    ) -> Dict[str, Any]:
        """处理需要 OAuth 授权的情况（使用 server_id）"""
        display_name = server_name or server_id
        # 获取授权 URL
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.mcpmarket_api_url}/uno/create-instance",
                    json={
                        "user_id": user_id,
                        "server_id": server_id,  # 使用 server_id
                        "pre_auth": True
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    auth_url = data.get("auth_url")
                    
                    return {
                        "success": False,
                        "status": "need_auth",
                        "server_name": display_name,
                        "auth_url": auth_url,
                        "message": f"""需要先授权连接 {display_name}。

请点击以下链接完成授权：
{auth_url}

授权步骤：
1. 点击上面的链接
2. 使用您的 {display_name} 账户登录并授权
3. 授权完成后关闭窗口
4. 告诉我"已完成授权"，我会继续操作"""
                    }
                    
        except Exception as e:
            logger.error(f"获取授权 URL 失败: {e}")
        
        return {
            "success": False,
            "error": f"需要先连接 {display_name}，请使用 connect 工具"
        }
    
    async def _call_remote_tool(
        self,
        mcp_url: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        调用远程 MCP 工具
        
        使用官方 MCP SDK 进行通信，SDK 会自动处理：
        - JSON-RPC 协议细节
        - 会话管理
        - 错误处理
        """
        try:
            # 使用 MCP SDK 调用工具
            result = await mcp_client_manager.call_tool(
                mcp_url=mcp_url,
                tool_name=tool_name,
                arguments=arguments
            )
            
            # 序列化结果
            return self._serialize_result(result)
                
        except Exception as e:
            logger.error(f"远程调用失败: {e}")
            raise
    
    def _serialize_result(self, result: Any) -> Any:
        """
        序列化 MCP 调用结果
        
        MCP SDK 返回的结果可能包含：
        - content: 内容列表（文本、图片等）
        - isError: 是否为错误
        """
        # 如果是 MCP CallToolResult 对象
        if hasattr(result, 'content'):
            content_list = []
            for item in result.content:
                if hasattr(item, 'type'):
                    content_item = {'type': item.type}
                    if hasattr(item, 'text'):
                        content_item['text'] = item.text
                    if hasattr(item, 'data'):
                        content_item['data'] = item.data
                    if hasattr(item, 'mimeType'):
                        content_item['mimeType'] = item.mimeType
                    content_list.append(content_item)
                else:
                    content_list.append(str(item))
            
            return {
                'content': content_list,
                'isError': getattr(result, 'isError', False)
            }
        
        # 如果已经是字典，直接返回
        if isinstance(result, dict):
            return result
        
        # 其他情况，转换为字符串
        return {"content": [{"type": "text", "text": str(result)}], "isError": False}
