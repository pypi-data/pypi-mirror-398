"""
discover_servers 工具

获取指定 server 的详细 tools 定义。
通过 mcpmarket API 获取用户 MCP 实例，使用 MCP SDK 连接真实 server 获取最新 tools。
自动处理 OAuth 认证流程。
"""

from typing import Dict, Any, List, Optional
import httpx

from ..config import settings
from ..utils import get_logger
from ..registry.mcp_client_manager import mcp_client_manager, AuthRequiredError

logger = get_logger("tools.discover_servers")


class GetServersTool:
    """
    Discover Servers 工具
    
    核心功能：
    1. 通过 mcpmarket API 检查/创建用户 MCP 实例
    2. 使用 MCP SDK 连接到真实 server
    3. 获取最新的 tools 定义
    4. 自动处理 OAuth 认证流程
    """
    
    def __init__(self, server_registry: Any):
        """
        初始化
        
        Args:
            server_registry: Server 注册表实例
        """
        self.server_registry = server_registry
        self.mcpmarket_api_url = settings.mcpmarket_api_url
        logger.info("GetServersTool (discover_servers) 已初始化")
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        获取工具定义（用于 MCP tools/list）
        
        description 中动态包含所有可用 server 的索引
        """
        servers_summary = self._build_servers_summary()
        
        return {
            "name": "uno_discover_servers",
            "description": f"""【第一步】发现 MCP Server 并获取其工具定义。

【重要】只能查询以下列表中的 MCP Server：
{servers_summary}

【使用规则】
1. server_names 参数必须从上述列表中选择
2. 如果用户的问题与上述 server 无关，请直接告知"当前没有相关的 MCP Server"
3. 不要尝试查询列表之外的任何名称

【工作流程】
此工具返回工具定义后，你必须**立即**调用 uno_call_tool 来执行具体工具，不要等待用户确认！

示例流程：
1. 用户问"旧金山时间" 
2. 你调用：uno_discover_servers(server_names=["Time"])
3. 收到工具列表后，立即调用：uno_call_tool(tool_name="Time.get_current_time", arguments={{"timezone": "America/Los_Angeles"}})
4. 然后告诉用户结果

【返回内容】
- servers: 各 server 的 tools 定义（名称、描述、inputSchema）
- auth_required: 需要用户授权的 server 列表（如有）

【OAuth 认证说明】
如果返回了 auth_url，需要用户先点击链接完成授权，授权后再次调用此工具获取 tools。""",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "server_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要获取详细信息的 MCP Server 名称列表，必须从工具描述中的可用列表中选择"
                    }
                },
                "required": ["server_names"]
            }
        }
    
    def _build_servers_summary(self) -> str:
        """构建所有 mcp server 的摘要信息"""
        servers = self.server_registry.list_servers()
        if not servers:
            return "（暂无可用 mcp server）"
        
        lines = []
        for server in servers:
            name = server.get("name", "unknown")
            description = server.get("description", "无描述")
            # 处理多语言描述
            if isinstance(description, dict):
                description = description.get("zh") or description.get("en") or "无描述"
            lines.append(f"- {name}: {description}")
        
        return "\n".join(lines)
    
    async def execute(
        self,
        server_names: List[str],
        user_id: str
    ) -> Dict[str, Any]:
        """
        执行工具：获取指定 server 的详细 tools 定义
        
        工作流程：
        1. 检查用户是否已有该 server 的 MCP 实例
        2. 如果没有，创建实例（可能需要 OAuth）
        3. 使用 MCP SDK 连接到实例，获取最新 tools
        
        Args:
            server_names: server 名称列表
            user_id: 用户 ID
            
        Returns:
            包含 server、tools 信息的字典
        """
        logger.info(f"discover_servers: {server_names}, user={user_id}")
        
        result = {
            "servers": {},
            "auth_required": []
        }
        
        total_tools = 0
        for name in server_names:
            server_result = await self._process_server(name, user_id)
            result["servers"][name] = server_result
            
            if server_result.get("tools"):
                total_tools += len(server_result["tools"])
            
            # 如果需要授权，添加到 auth_required 列表（不在 servers 中重复 auth_url）
            if server_result.get("status") == "auth_required" and server_result.get("auth_url"):
                result["auth_required"].append({
                    "server": name,
                    "auth_url": server_result.pop("auth_url"),  # 从 server_result 中移除，只保留在 auth_required
                    "message": server_result.pop("message", f"请点击链接完成 {name} 的授权")
                })
        
        # 移除空的 auth_required 列表
        if not result["auth_required"]:
            del result["auth_required"]
        
        logger.info(
            f"discover_servers 完成: {len(result['servers'])} servers, "
            f"{total_tools} tools, "
            f"{len(result.get('auth_required', []))} need auth"
        )
        
        return result
    
    async def _process_server(self, server_name: str, user_id: str) -> Dict[str, Any]:
        """
        处理单个 server
        
        Args:
            server_name: server 名称（来自 server_registry，已筛选 hosted=true）
            user_id: 用户 ID
            
        Returns:
            server 处理结果
        """
        try:
            # 0. 从 server_registry 获取 server_id（确保是托管的 server）
            server_detail = await self.server_registry.get_server_detail(server_name)
            if not server_detail:
                return {"error": f"Server '{server_name}' 不存在或非托管服务器"}
            
            server_id = server_detail.get("metadata", {}).get("server_id")
            if not server_id:
                return {"error": f"Server '{server_name}' 缺少 server_id"}
            
            # 1. 用 server_id 检查连接状态
            connection = await self._check_connection(user_id, server_id)
            
            if connection.get("error") == "Server not found":
                return {"error": f"Server '{server_name}' 不存在"}
            
            # 2. 如果已连接，直接获取 tools
            if connection.get("connected") and connection.get("mcp_url"):
                return await self._get_tools_from_instance(
                    server_name, 
                    connection["mcp_url"],
                    user_id,
                    server_id
                )
            
            # 3. 未连接，需要创建实例（用 server_id）
            create_result = await self._create_instance(user_id, server_id, server_name)
            
            if not create_result.get("success"):
                return {"error": create_result.get("error", "创建实例失败")}
            
            # 4. 如果需要 OAuth 认证，返回 auth_url
            if create_result.get("need_auth") and create_result.get("auth_url"):
                return {
                    "status": "auth_required",
                    "auth_url": create_result["auth_url"],
                    "message": f"请点击链接完成 {server_name} 的 OAuth 授权"
                }
            
            # 5. 实例创建成功，获取 tools
            mcp_url = create_result.get("mcp_url")
            if mcp_url:
                return await self._get_tools_from_instance(server_name, mcp_url, user_id, server_id)
            
            return {"error": "无法获取 MCP URL"}
            
        except Exception as e:
            logger.error(f"处理 server {server_name} 失败: {e}")
            return {"error": str(e)}
    
    async def _check_connection(
        self,
        user_id: str,
        server_id: str
    ) -> Dict[str, Any]:
        """
        检查用户与 server 的连接状态
        
        Args:
            user_id: 用户 ID
            server_id: Server ID（来自 server_registry，确保是托管 server）
        """
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
    
    async def _create_instance(
        self,
        user_id: str,
        server_id: str,
        server_name: str = None
    ) -> Dict[str, Any]:
        """
        创建用户 MCP 实例
        
        Args:
            user_id: 用户 ID
            server_id: Server ID（来自 server_registry，确保是托管 server）
            server_name: Server 显示名称（可选，用于日志）
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.mcpmarket_api_url}/uno/create-instance",
                    json={
                        "user_id": user_id,
                        "server_id": server_id,  # 用 server_id 而不是 server_name
                        "pre_auth": True
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                
                return {
                    "success": False,
                    "error": f"创建实例失败: HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"创建实例失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_tools_from_instance(
        self,
        server_name: str,
        mcp_url: str,
        user_id: str = None,
        server_id: str = None
    ) -> Dict[str, Any]:
        """
        从 MCP 实例获取 tools 列表
        
        Args:
            server_name: server 显示名称
            mcp_url: 用户 MCP 实例 URL
            user_id: 用户 ID（用于缓存和获取 auth_url）
            server_id: Server ID（用于重新创建实例获取 auth_url）
            
        Returns:
            包含 tools 的结果
        """
        try:
            result = await mcp_client_manager.get_tools_from_server(mcp_url)
            
            if result.get("success"):
                # 成功获取 tools，缓存 mcp_url（供 call_tool 复用）
                if user_id:
                    mcp_client_manager.cache_url(user_id, server_name, mcp_url, server_id)
                    logger.info(f"已缓存连接: {user_id}/{server_name} -> {mcp_url}")
                
                return {
                    "tools": result["tools"],
                    "mcp_url": mcp_url  # 返回 mcp_url 供调用者知道
                }
            
            # 如果需要认证，尝试获取 auth_url
            if result.get("auth_required") and user_id and server_id:
                auth_result = await self._get_auth_url(user_id, server_id, server_name)
                if auth_result.get("auth_url"):
                    return {
                        "status": "auth_required",
                        "auth_url": auth_result["auth_url"],
                        "message": f"请点击链接完成 {server_name} 的 OAuth 授权"
                    }
                return {
                    "status": "auth_required",
                    "error": "Server 需要认证，请稍后重试"
                }
            
            # 连接失败，可能是认证问题，尝试获取 auth_url
            if user_id and server_id:
                auth_result = await self._get_auth_url(user_id, server_id, server_name, force=True)
                if auth_result.get("auth_url"):
                    return {
                        "status": "auth_required",
                        "auth_url": auth_result["auth_url"],
                        "message": f"请点击链接完成 {server_name} 的 OAuth 授权"
                    }
                if auth_result.get("auth_type"):
                    return {
                        "status": "auth_required",
                        "error": auth_result.get("error", f"{server_name} 需要 OAuth 认证")
                    }
            
            return {"error": result.get("error", "获取 tools 失败")}
            
        except AuthRequiredError:
            if user_id and server_id:
                auth_result = await self._get_auth_url(user_id, server_id, server_name)
                if auth_result.get("auth_url"):
                    return {
                        "status": "auth_required",
                        "auth_url": auth_result["auth_url"],
                        "message": f"请点击链接完成 {server_name} 的 OAuth 授权"
                    }
            return {
                "status": "auth_required",
                "error": "Server 需要认证"
            }
        except Exception as e:
            logger.error(f"获取 tools 失败: {server_name}, {e}")
            return {"error": str(e)}
    
    async def _get_auth_url(
        self,
        user_id: str,
        server_id: str,
        server_name: str = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        获取 OAuth 授权 URL
        
        Args:
            user_id: 用户 ID
            server_id: Server ID（来自 server_registry，确保是托管 server）
            server_name: Server 显示名称（用于日志）
            force: 是否强制重新获取
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 用 server_id 创建实例以获取 auth_url
                response = await client.post(
                    f"{self.mcpmarket_api_url}/uno/create-instance",
                    json={
                        "user_id": user_id,
                        "server_id": server_id,
                        "pre_auth": True,
                        "force_reauth": force
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("need_auth") and data.get("auth_url"):
                        return {"auth_url": data["auth_url"]}
                
                return {}
                
        except Exception as e:
            logger.warning(f"获取 auth_url 失败: {server_name or server_id}, {e}")
            return {}
