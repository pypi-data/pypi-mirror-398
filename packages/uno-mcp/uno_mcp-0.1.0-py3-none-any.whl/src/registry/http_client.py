"""
HTTP MCP 客户端

用于与远程 MCP server 通信（Streamable HTTP 协议）。
"""

import json
from typing import Dict, Any, Optional, List
import httpx

from ..utils import get_logger

logger = get_logger("registry.http_client")


class HTTPMCPClient:
    """
    HTTP MCP 客户端
    
    实现 Streamable HTTP MCP 协议，用于调用远程 MCP server。
    """
    
    def __init__(
        self,
        server_url: str,
        server_name: str,
        timeout: float = 30.0,
        auth_token: Optional[str] = None
    ):
        """
        初始化
        
        Args:
            server_url: Server URL
            server_name: Server 名称
            timeout: 请求超时时间
            auth_token: 认证 token（可选）
        """
        self.server_url = server_url.rstrip("/")
        self.server_name = server_name
        self.timeout = timeout
        self.auth_token = auth_token
        
        self._client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        
        logger.info(f"HTTPMCPClient 创建: {server_name} -> {server_url}")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=headers
            )
        return self._client
    
    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def initialize(self) -> bool:
        """
        初始化 MCP 连接
        
        Returns:
            是否初始化成功
        """
        if self._initialized:
            return True
        
        try:
            response = await self._send_request({
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "uno",
                        "version": "0.1.0"
                    }
                },
                "id": 1
            })
            
            if response and "result" in response:
                self._initialized = True
                logger.info(f"MCP 初始化成功: {self.server_name}")
                return True
            
            logger.warning(f"MCP 初始化失败: {self.server_name}")
            return False
            
        except Exception as e:
            logger.error(f"MCP 初始化异常: {self.server_name}, {e}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        列出 server 的所有工具
        
        Returns:
            工具列表
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            response = await self._send_request({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            })
            
            if response and "result" in response:
                tools = response["result"].get("tools", [])
                logger.info(f"获取工具列表: {self.server_name}, count={len(tools)}")
                return tools
            
            return []
            
        except Exception as e:
            logger.error(f"获取工具列表失败: {self.server_name}, {e}")
            return []
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            调用结果
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"调用工具: {self.server_name}.{tool_name}")
        
        response = await self._send_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 3
        })
        
        if response and "result" in response:
            return response["result"]
        
        if response and "error" in response:
            raise Exception(response["error"].get("message", "Unknown error"))
        
        raise Exception("Invalid response from server")
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送 JSON-RPC 请求
        
        Args:
            request: 请求数据
            
        Returns:
            响应数据
        """
        client = await self._get_client()
        
        response = await client.post(
            self.server_url,
            json=request
        )
        response.raise_for_status()
        
        return response.json()

