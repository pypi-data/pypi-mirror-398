"""
MCP 客户端连接管理器

使用官方 MCP SDK 管理与远程 MCP 服务器的连接。
参考 mcpmarket chat 的设计，每次创建新连接并正确释放。
"""

import asyncio
from typing import Dict, Any, Optional, List, Tuple
from contextlib import AsyncExitStack
from datetime import timedelta, datetime

from mcp import ClientSession

from ..utils import get_logger

logger = get_logger("registry.mcp_client_manager")


class UserConnectionRegistry:
    """
    用户连接注册表
    
    维护两层缓存：
    1. URL 缓存: (user_id, server_name) -> {mcp_url, server_id}
    2. 连接池: mcp_url -> MCPClient (临时持有，用完即关）
    
    设计说明：
    - discover_servers 后缓存 mcp_url，call_tool 无需再查询 proxy
    - 连接在使用期间（ref_count > 0）保持在池中
    - 使用完毕（ref_count = 0）立即关闭，避免 SSE 空闲重连
    """
    
    def __init__(self, url_ttl_seconds: int = 3600, max_idle_seconds: int = 300):
        """
        Args:
            url_ttl_seconds: URL 缓存有效期（秒），默认 1 小时
            max_idle_seconds: 连接最大空闲时间（秒），默认 5 分钟
        """
        # URL 缓存: (user_id, server_name) -> {mcp_url, server_id, cached_at}
        self._url_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._url_ttl = timedelta(seconds=url_ttl_seconds)
        
        # 连接池: mcp_url -> {client, last_used, ref_count}
        self._connection_pool: Dict[str, Dict[str, Any]] = {}
        self._max_idle = timedelta(seconds=max_idle_seconds)
        
        # 锁，保护并发访问
        self._lock = asyncio.Lock()
        
        logger.info(f"UserConnectionRegistry 已初始化，URL TTL={url_ttl_seconds}s，连接空闲={max_idle_seconds}s")
    
    # ==================== URL 缓存 ====================
    
    def get_url(self, user_id: str, server_name: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的 mcp_url
        
        Returns:
            {"mcp_url": str, "server_id": str} 或 None
        """
        key = (user_id, server_name)
        entry = self._url_cache.get(key)
        
        if entry is None:
            return None
        
        # 检查是否过期
        if datetime.now() - entry["cached_at"] > self._url_ttl:
            logger.debug(f"URL 缓存过期: {user_id}/{server_name}")
            del self._url_cache[key]
            return None
        
        logger.debug(f"URL 缓存命中: {user_id}/{server_name} -> {entry['mcp_url']}")
        return {
            "mcp_url": entry["mcp_url"],
            "server_id": entry["server_id"]
        }
    
    def set_url(self, user_id: str, server_name: str, mcp_url: str, server_id: str = None):
        """缓存 mcp_url（由 discover_servers 调用）"""
        key = (user_id, server_name)
        self._url_cache[key] = {
            "mcp_url": mcp_url,
            "server_id": server_id,
            "cached_at": datetime.now()
        }
        logger.info(f"URL 已缓存: {user_id}/{server_name} -> {mcp_url}")
    
    def invalidate_url(self, user_id: str, server_name: str = None):
        """使 URL 缓存失效"""
        if server_name:
            key = (user_id, server_name)
            if key in self._url_cache:
                del self._url_cache[key]
                logger.info(f"URL 缓存已清除: {user_id}/{server_name}")
        else:
            keys_to_delete = [k for k in self._url_cache if k[0] == user_id]
            for key in keys_to_delete:
                del self._url_cache[key]
            logger.info(f"已清除用户 {user_id} 的所有 URL 缓存（{len(keys_to_delete)} 条）")
    
    # ==================== 连接池 ====================
    
    async def get_client(self, mcp_url: str) -> "MCPClient":
        """
        从连接池获取或创建 MCPClient
        
        Returns:
            已连接的 MCPClient
        """
        async with self._lock:
            # 检查是否已有连接
            if mcp_url in self._connection_pool:
                entry = self._connection_pool[mcp_url]
                client = entry["client"]
                
                # 检查连接是否还活着
                if client.session is not None:
                    entry["last_used"] = datetime.now()
                    entry["ref_count"] += 1
                    logger.debug(f"连接池命中: {mcp_url}，引用计数={entry['ref_count']}")
                    return client
                else:
                    # 连接已断开，清理
                    logger.warning(f"连接已断开，重新创建: {mcp_url}")
                    await self._cleanup_client(mcp_url)
            
            # 创建新连接
            logger.info(f"创建新连接: {mcp_url}")
            client = MCPClient()
            await client.connect(mcp_url)
            
            self._connection_pool[mcp_url] = {
                "client": client,
                "last_used": datetime.now(),
                "ref_count": 1
            }
            
            return client
    
    async def release_client(self, mcp_url: str):
        """
        释放客户端引用
        
        当引用计数降为 0 时，立即关闭连接以避免 SSE 空闲重连
        """
        async with self._lock:
            if mcp_url in self._connection_pool:
                entry = self._connection_pool[mcp_url]
                entry["ref_count"] = max(0, entry["ref_count"] - 1)
                entry["last_used"] = datetime.now()
                logger.debug(f"释放连接引用: {mcp_url}，引用计数={entry['ref_count']}")
                
                # 当引用计数为 0 时，立即关闭连接（避免 SSE 空闲重连）
                if entry["ref_count"] == 0:
                    logger.info(f"引用计数为 0，立即关闭连接: {mcp_url}")
                    await self._cleanup_client(mcp_url)
    
    async def _cleanup_client(self, mcp_url: str):
        """清理单个连接（内部方法，需要持有锁）"""
        if mcp_url in self._connection_pool:
            entry = self._connection_pool[mcp_url]
            try:
                await entry["client"].cleanup()
            except Exception as e:
                logger.warning(f"清理连接失败: {mcp_url}, {e}")
            del self._connection_pool[mcp_url]
            logger.info(f"连接已清理: {mcp_url}")
    
    async def cleanup_idle_connections(self):
        """清理空闲连接（可定期调用）"""
        async with self._lock:
            now = datetime.now()
            urls_to_cleanup = []
            
            for mcp_url, entry in self._connection_pool.items():
                # 只清理引用计数为 0 且空闲超时的连接
                if entry["ref_count"] == 0 and now - entry["last_used"] > self._max_idle:
                    urls_to_cleanup.append(mcp_url)
            
            for mcp_url in urls_to_cleanup:
                await self._cleanup_client(mcp_url)
            
            if urls_to_cleanup:
                logger.info(f"已清理 {len(urls_to_cleanup)} 个空闲连接")
    
    async def close_all(self):
        """关闭所有连接"""
        async with self._lock:
            for mcp_url in list(self._connection_pool.keys()):
                await self._cleanup_client(mcp_url)
            self._url_cache.clear()
            logger.info("所有连接和缓存已清理")
    
    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "url_cache_count": len(self._url_cache),
            "connection_pool_count": len(self._connection_pool),
            "connections": {
                url: {
                    "ref_count": entry["ref_count"],
                    "idle_seconds": (datetime.now() - entry["last_used"]).total_seconds()
                }
                for url, entry in self._connection_pool.items()
            }
        }


# 全局连接注册表实例
connection_registry = UserConnectionRegistry()


class AuthRequiredError(Exception):
    """MCP 服务器需要认证的错误"""
    def __init__(self, status_code: int, www_authenticate: str = "", server_url: str = ""):
        self.status_code = status_code
        self.www_authenticate = www_authenticate
        self.server_url = server_url
        super().__init__(f"Authentication required for {server_url} (HTTP {status_code})")


class MCPClient:
    """
    基础 MCP 客户端
    
    参考 mcpmarket 的设计：
    - 使用 AsyncExitStack 管理异步上下文
    - 在后台任务中运行连接，确保资源在同一任务中创建和清理
    - 使用事件信号协调初始化和关闭
    """
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self._cleanup_done = False
        self._connection_task: Optional[asyncio.Task] = None
        self._server_url: Optional[str] = None
        self._initialized_event = asyncio.Event()
        self._shutdown_event = asyncio.Event()
        self._init_error: Optional[Exception] = None
    
    def _get_server_type(self, server_url: str) -> str:
        """判断服务器类型：sse 或 streamable_http"""
        url_lower = server_url.lower()
        if "sse" in url_lower:
            return "sse"
        elif "mcp" in url_lower:
            return "streamable_http"
        return "unknown"
    
    async def _run_connection(self, server_url: str):
        """在后台任务中运行连接（确保资源在同一任务中创建和清理）"""
        from mcp.client.streamable_http import streamablehttp_client
        from mcp.client.sse import sse_client
        
        exit_stack = AsyncExitStack()
        
        try:
            async with exit_stack:
                server_type = self._get_server_type(server_url)
                
                if server_type == "streamable_http":
                    streams_context = streamablehttp_client(
                        url=server_url,
                        timeout=10.0,
                        sse_read_timeout=60
                    )
                    streams = await exit_stack.enter_async_context(streams_context)
                    read_stream, write_stream, _ = streams
                    
                elif server_type == "sse":
                    streams_context = sse_client(
                        url=server_url,
                        timeout=10.0,
                        sse_read_timeout=60
                    )
                    streams = await exit_stack.enter_async_context(streams_context)
                    read_stream, write_stream = streams
                    
                else:
                    raise ValueError(f"Unsupported server type: {server_type}")
                
                # 创建会话
                session_context = ClientSession(
                    read_stream,
                    write_stream,
                    read_timeout_seconds=timedelta(seconds=60)
                )
                
                self.session = await exit_stack.enter_async_context(session_context)
                
                # 初始化会话
                try:
                    await self.session.initialize()
                    logger.debug(f"Successfully initialized MCP session: {server_url}")
                    self._initialized_event.set()
                except Exception as init_error:
                    logger.error(f"Session initialization failed: {init_error}")
                    self._init_error = init_error
                    self._initialized_event.set()
                    return
                
                # 等待关闭信号
                await self._shutdown_event.wait()
                logger.info("Received shutdown signal, cleaning up...")
                
        except asyncio.CancelledError:
            logger.info("Connection task cancelled")
            if not self._initialized_event.is_set():
                self._init_error = ConnectionError("Connection cancelled")
                self._initialized_event.set()
        except Exception as e:
            # 记录完整的异常信息（包括嵌套异常）
            full_error = str(e).lower()
            
            # 尝试获取嵌套异常的信息
            if hasattr(e, 'exceptions'):  # ExceptionGroup
                for sub_e in e.exceptions:
                    full_error += " " + str(sub_e).lower()
                    logger.debug(f"Sub-exception: {type(sub_e).__name__}: {sub_e}")
            if hasattr(e, '__cause__') and e.__cause__:
                full_error += " " + str(e.__cause__).lower()
            
            logger.debug(f"Full error string for analysis: {full_error}")
            
            # 检查是否是认证错误（多种模式）
            auth_patterns = [
                "401", "unauthorized", "authentication", "oauth",
                "access denied", "forbidden", "credential", "token",
                "www-authenticate", "bearer"
            ]
            is_auth_error = any(pattern in full_error for pattern in auth_patterns)
            
            if is_auth_error:
                self._init_error = AuthRequiredError(401, "", server_url)
                logger.info(f"Authentication required for: {server_url}")
            else:
                self._init_error = ConnectionError(f"Cannot connect to MCP server: {e}")
                logger.error(f"Connection failed: {e}")
            
            if not self._initialized_event.is_set():
                self._initialized_event.set()
        finally:
            self.session = None
            logger.debug("Connection task completed, resources cleaned up")
    
    async def connect(self, server_url: str, timeout: float = 10.0):
        """连接到 MCP 服务器"""
        self._server_url = server_url
        
        # 重置信号
        self._initialized_event.clear()
        self._shutdown_event.clear()
        self._init_error = None
        self._cleanup_done = False
        
        # 创建后台任务管理连接
        self._connection_task = asyncio.create_task(self._run_connection(server_url))
        
        # 错误处理回调
        def handle_task_exception(task):
            try:
                task.result()
            except Exception:
                pass
        
        self._connection_task.add_done_callback(handle_task_exception)
        
        # 等待初始化完成
        try:
            await asyncio.wait_for(self._initialized_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            if self._connection_task and not self._connection_task.done():
                self._shutdown_event.set()
                await asyncio.sleep(0.1)
                if not self._connection_task.done():
                    self._connection_task.cancel()
                try:
                    await self._connection_task
                except asyncio.CancelledError:
                    pass
            raise ConnectionError(f"Connection timeout: {server_url}")
        
        # 检查初始化错误
        if self._init_error:
            self._shutdown_event.set()
            if self._connection_task and not self._connection_task.done():
                try:
                    await self._connection_task
                except (asyncio.CancelledError, Exception):
                    pass
            raise self._init_error
        
        # 确认 session 已创建
        if self.session is None:
            self._shutdown_event.set()
            if self._connection_task and not self._connection_task.done():
                try:
                    await self._connection_task
                except (asyncio.CancelledError, Exception):
                    pass
            raise ConnectionError(f"Failed to create session: {server_url}")
    
    async def cleanup(self):
        """清理连接资源"""
        if self._cleanup_done:
            return
        
        try:
            self._cleanup_done = True
            self.session = None
            self._shutdown_event.set()
            
            if self._connection_task and not self._connection_task.done():
                try:
                    await asyncio.wait_for(self._connection_task, timeout=2.0)
                except asyncio.TimeoutError:
                    logger.warning("Connection task did not respond, cancelling...")
                    self._connection_task.cancel()
                    try:
                        await self._connection_task
                    except asyncio.CancelledError:
                        pass
                except (asyncio.CancelledError, Exception) as e:
                    logger.debug(f"Cleanup exception: {e}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        finally:
            self.session = None
            self._connection_task = None
            self._initialized_event.clear()
            self._shutdown_event.clear()
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出服务器的所有工具"""
        if not self.session:
            raise RuntimeError("Not connected to any MCP server")
        
        try:
            tools_result = await asyncio.wait_for(
                self.session.list_tools(),
                timeout=10.0
            )
            
            # 转换为字典格式
            tools = []
            for tool in tools_result.tools:
                tool_dict = {
                    "name": tool.name,
                    "description": tool.description or "",
                }
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    tool_dict["inputSchema"] = tool.inputSchema
                tools.append(tool_dict)
            
            return tools
            
        except asyncio.TimeoutError:
            raise RuntimeError("List tools timeout")
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用工具"""
        if not self.session:
            raise RuntimeError("Not connected to any MCP server")
        
        try:
            result = await asyncio.wait_for(
                self.session.call_tool(tool_name, arguments),
                timeout=60.0
            )
            return result
        except asyncio.TimeoutError:
            raise RuntimeError(f"Call tool timeout: {tool_name}")
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            raise


class MCPClientManager:
    """
    MCP 客户端连接管理器
    
    功能：
    - 使用连接池管理 MCP 连接（复用连接，避免重复创建/释放）
    - 使用 URL 缓存避免重复查询 proxy server
    - 处理认证错误
    """
    
    def __init__(self):
        self._registry = connection_registry
        logger.info("MCPClientManager 已初始化（使用连接池）")
    
    async def get_tools_from_server(self, mcp_url: str) -> Dict[str, Any]:
        """
        从远程 MCP 服务器获取工具列表（使用连接池）
        """
        client = None
        try:
            client = await self._registry.get_client(mcp_url)
            tools = await client.list_tools()
            
            return {
                "success": True,
                "tools": tools
            }
            
        except AuthRequiredError as e:
            logger.info(f"Server requires authentication: {mcp_url}")
            return {
                "success": False,
                "auth_required": True,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Failed to get tools from {mcp_url}: {e}")
            return {
                "success": False,
                "auth_required": False,
                "error": str(e)
            }
        finally:
            if client:
                await self._registry.release_client(mcp_url)
    
    async def call_tool(
        self,
        mcp_url: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        调用远程 MCP 工具（使用连接池）
        """
        client = None
        try:
            client = await self._registry.get_client(mcp_url)
            result = await client.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            # 连接可能已断开，清理缓存重试
            logger.warning(f"调用失败，可能需要重连: {e}")
            raise RuntimeError(f"Cannot connect to MCP server: {e}")
        finally:
            if client:
                await self._registry.release_client(mcp_url)
    
    # ==================== URL 缓存操作 ====================
    
    def get_cached_url(self, user_id: str, server_name: str) -> Optional[Dict[str, Any]]:
        """获取缓存的 mcp_url"""
        return self._registry.get_url(user_id, server_name)
    
    def cache_url(self, user_id: str, server_name: str, mcp_url: str, server_id: str = None):
        """缓存 mcp_url（由 discover_servers 调用）"""
        self._registry.set_url(user_id, server_name, mcp_url, server_id)
    
    def invalidate_cache(self, user_id: str, server_name: str = None):
        """使缓存失效"""
        self._registry.invalidate_url(user_id, server_name)
    
    # ==================== 管理操作 ====================
    
    async def cleanup_idle(self):
        """清理空闲连接"""
        await self._registry.cleanup_idle_connections()
    
    async def close(self):
        """关闭管理器，清理所有连接"""
        await self._registry.close_all()
        logger.info("MCPClientManager 已关闭")
    
    def stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        return self._registry.stats()


# 全局实例
mcp_client_manager = MCPClientManager()
