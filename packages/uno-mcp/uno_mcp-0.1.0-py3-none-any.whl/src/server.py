"""
Uno MCP Server - 主服务器实现

提供 MCP 协议端点和 GUI API。
支持 OAuth 2.0 认证（mcpmarket 作为认证服务器）。
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from quart import Quart, request, jsonify, Response
from quart_cors import cors

from .config import settings
from .utils import get_logger, setup_logging
from .auth import generate_wellknown_mcp
from .auth.oauth_server import resource_server
from .registry import ServerRegistry
from .registry.server_registry import server_registry
from .registry.mcp_client_manager import mcp_client_manager
from .skills import SkillManager
from .tools import GetServersTool, GetSkillTool, CallTool, ExecuteTool

logger = get_logger("server")

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
GUI_DIR = PROJECT_ROOT / "gui"


# 全局组件
skill_manager: Optional[SkillManager] = None
get_servers_tool: Optional[GetServersTool] = None
get_skill_tool: Optional[GetSkillTool] = None
call_tool: Optional[CallTool] = None
execute_tool: Optional[ExecuteTool] = None


def create_app() -> Quart:
    """创建 Quart 应用"""
    app = Quart(__name__)
    app = cors(app, allow_origin=settings.get_cors_origins())
    
    # 注册启动/关闭事件
    @app.before_serving
    async def startup():
        """应用启动"""
        global skill_manager, get_servers_tool, get_skill_tool, call_tool, execute_tool
        
        setup_logging()
        logger.info("Uno MCP Server 启动中...")
        
        # 刷新 server 列表
        await server_registry.refresh()
        
        # 初始化 Skill 管理器
        skill_manager = SkillManager()
        await skill_manager.initialize()
        
        # 初始化工具（3个核心工具）
        get_servers_tool = GetServersTool(server_registry)
        get_skill_tool = GetSkillTool(skill_manager, server_registry)
        call_tool = CallTool(server_registry)
        execute_tool = ExecuteTool()
        
        logger.info(f"服务器地址: {settings.server_url}")
        logger.info(f"已加载 {len(server_registry.list_servers())} 个 MCP servers")
        logger.info(f"已加载 {len(skill_manager.list_skills())} 个 skills")
        logger.info("Uno MCP Server 启动完成!")
    
    @app.after_serving
    async def shutdown():
        """应用关闭"""
        logger.info("Uno MCP Server 关闭中...")
        await server_registry.close()
        await mcp_client_manager.close()
        logger.info("Uno MCP Server 已关闭")
    
    # ============= 认证辅助函数 =============
    
    async def require_auth() -> tuple[bool, Optional[str], Optional[Dict]]:
        """
        检查请求是否已认证
        
        支持两种认证方式：
        1. Bearer token（OAuth access_token）- 用于 MCP 客户端和 GUI
        2. Cookie session - 备用方式
        
        Returns:
            (is_authenticated, user_id, user_info)
        """
        import httpx
        
        # 1. 优先检查 Bearer token（OAuth access_token）
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header[7:]
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        f"{settings.mcpmarket_url}/api/uno/verify-token",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('valid'):
                            return True, data.get('user_id'), data
            except Exception as e:
                logger.error(f"Bearer token 验证失败: {e}")
            
            # Token 无效
            return False, None, None
        
        # 2. 备用：检查 cookie session
        try:
            cookies = {}
            for key, value in request.cookies.items():
                cookies[key] = value
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.mcpmarket_url}/api/uno/current-user",
                    cookies=cookies
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('logged_in'):
                        return True, data.get('user_id'), data
            
            return False, None, None
            
        except Exception as e:
            logger.error(f"验证用户身份失败: {e}")
            return False, None, None
    
    def make_401_response() -> Response:
        """创建 401 未授权响应"""
        www_auth = resource_server.get_www_authenticate_header()
        response = Response(
            json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32001,
                    "message": "Unauthorized. OAuth authentication required."
                },
                "id": None
            }),
            status=401,
            content_type="application/json"
        )
        response.headers["WWW-Authenticate"] = www_auth
        return response
    
    # ============= 首页 =============
    
    @app.route("/")
    async def root():
        """首页 - 显示服务信息"""
        return jsonify({
            "service": "Uno MCP Server",
            "version": "0.1.0",
            "description": "All-in-One MCP Gateway with Skills",
            "status": "running",
            "authentication": "OAuth 2.0 (mcpmarket)",
            "endpoints": {
                "mcp": {
                    "well_known_mcp": "GET /.well-known/mcp.json",
                    "well_known_oauth": "GET /.well-known/oauth-protected-resource",
                    "message": "POST /mcp (需要 OAuth 认证)"
                },
                "api": {
                    "servers": "GET /api/servers",
                    "skills": "GET /api/skills",
                    "health": "GET /health"
                },
                "gui": "GET /gui"
            },
            "statistics": {
                "available_servers": len(server_registry.list_servers()),
                "available_skills": len(skill_manager.list_skills()) if skill_manager else 0
            }
        })
    
    # ============= Well-known 端点 =============
    
    @app.route("/.well-known/mcp.json")
    async def wellknown_mcp():
        """MCP 协议发现端点"""
        return jsonify(generate_wellknown_mcp())
    
    @app.route("/.well-known/oauth-protected-resource")
    async def wellknown_oauth_protected_resource():
        """
        Protected Resource Metadata (RFC 9728)
        
        告诉客户端去哪里进行 OAuth 认证。
        """
        return jsonify(resource_server.get_protected_resource_metadata())
    
    # ============= MCP 协议端点 =============
    
    @app.route("/mcp", methods=["GET", "POST"])
    @app.route("/mcp/message", methods=["GET", "POST"])
    async def mcp_message():
        """
        MCP 消息处理端点
        
        支持两种请求方式：
        - GET: SSE 连接（返回 401 让客户端进行 OAuth 认证）
        - POST: JSON-RPC 消息
        
        需要 OAuth 认证。未认证时返回 401 + WWW-Authenticate。
        """
        # GET 请求：可能是 SSE 连接或认证检测
        if request.method == "GET":
            # 检查认证
            is_authenticated, user_id, user_info = await require_auth()
            if not is_authenticated:
                # 返回 401，让客户端知道需要认证
                return make_401_response()
            
            # 已认证的 GET 请求，返回基本信息
            return jsonify({
                "jsonrpc": "2.0",
                "result": {
                    "message": "MCP endpoint ready",
                    "user_id": user_id
                }
            })
        
        # POST 请求：处理 JSON-RPC 消息
        try:
            # 获取请求体
            body = await request.get_json()
            method = body.get("method")
            params = body.get("params", {})
            request_id = body.get("id")
            
            # 检查认证
            is_authenticated, user_id, user_info = await require_auth()
            
            # initialize 请求不需要认证（用于检测认证需求）
            if method == "initialize":
                if not is_authenticated:
                    # 返回 401，让客户端知道需要认证
                    return make_401_response()
                
                result = await handle_initialize()
            elif method == "notifications/initialized":
                return Response(status=204)
            elif method == "tools/list":
                if not is_authenticated:
                    return make_401_response()
                result = await handle_tools_list(user_id)
            elif method == "tools/call":
                if not is_authenticated:
                    return make_401_response()
                result = await handle_tools_call(params, user_id)
            else:
                if not is_authenticated:
                    return make_401_response()
                result = {"error": f"不支持的方法: {method}"}
            
            logger.info(f"MCP 请求: method={method}, user={user_id}")
            
            # 返回响应
            response_data = {
                "jsonrpc": "2.0",
                "result": result
            }
            if request_id is not None:
                response_data["id"] = request_id
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"处理 MCP 消息失败: {e}", exc_info=True)
            return jsonify({
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e)},
                "id": None
            }), 500
    
    async def handle_initialize() -> Dict[str, Any]:
        """处理 initialize 请求"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False}
            },
            "serverInfo": {
                "name": "Uno MCP Server",
                "version": "0.1.0"
            }
        }
    
    async def handle_tools_list(user_id: str) -> Dict[str, Any]:
        """处理 tools/list 请求"""
        tools = []
        
        # 添加核心工具（discover_servers 已自动处理授权，不再需要 authorize_server）
        if get_servers_tool:
            tools.append(get_servers_tool.get_tool_definition())
        # if get_skill_tool:
        #     tools.append(get_skill_tool.get_tool_definition())
        if call_tool:
            tools.append(call_tool.get_tool_definition())
        if execute_tool:
            tools.append(execute_tool.get_tool_definition())
        
        return {"tools": tools}
    
    async def handle_tools_call(params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """处理 tools/call 请求"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        logger.info(f"调用工具: {tool_name}, user={user_id}")
        
        try:
            if tool_name == "uno_discover_servers":
                result = await get_servers_tool.execute(
                    server_names=arguments.get("server_names", []),
                    user_id=user_id
                )
            elif tool_name == "discover_skills":
                result = await get_skill_tool.execute(
                    question=arguments.get("question", ""),
                    skill_name=arguments.get("skill_name"),
                    user_id=user_id
                )
            elif tool_name == "uno_call_tool":
                result = await call_tool.execute(
                    tool_name=arguments.get("tool_name", ""),
                    arguments=arguments.get("arguments", {}),
                    user_id=user_id
                )
            elif tool_name == "uno_execute_script":
                result = await execute_tool.execute(
                    script=arguments.get("script", ""),
                    language=arguments.get("language", "bash"),
                    stdin=arguments.get("stdin"),
                    user_id=user_id
                )
            else:
                result = {"success": False, "error": f"未知工具: {tool_name}"}
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                }],
                "isError": not result.get("success", True)
            }
            
        except Exception as e:
            logger.error(f"工具调用失败: {tool_name}, {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }
    
    # ============= API 端点（供 GUI 使用） =============
    
    @app.route("/api/servers")
    async def api_servers():
        """获取所有 server 列表"""
        return jsonify({
            "servers": server_registry.list_servers(),
            "count": len(server_registry.list_servers())
        })
    
    @app.route("/api/servers/<server_name>")
    async def api_server_detail(server_name: str):
        """获取指定 server 的详情"""
        detail = await server_registry.get_server_detail(server_name)
        if detail:
            return jsonify(detail)
        return jsonify({"error": f"Server '{server_name}' not found"}), 404
    
    @app.route("/api/skills")
    async def api_skills():
        """获取所有 skill 列表"""
        if skill_manager:
            return jsonify({
                "skills": skill_manager.list_skills(),
                "count": len(skill_manager.list_skills())
            })
        return jsonify({"skills": [], "count": 0})
    
    @app.route("/api/skills/<skill_name>")
    async def api_skill_detail(skill_name: str):
        """获取指定 skill 的详情"""
        if skill_manager:
            skill = await skill_manager.get_skill(skill_name)
            if skill:
                return jsonify(skill)
        return jsonify({"error": f"Skill '{skill_name}' not found"}), 404
    
    @app.route("/api/match-skill", methods=["POST"])
    async def api_match_skill():
        """根据问题匹配 skill"""
        body = await request.get_json()
        question = body.get("question", "")
        
        if skill_manager:
            skill = await skill_manager.match_skill(question)
            if skill:
                return jsonify({"matched": True, "skill": skill})
        
        return jsonify({"matched": False, "skill": None})
    
    @app.route("/health")
    async def health():
        """健康检查"""
        return jsonify({
            "status": "healthy",
            "version": "0.1.0",
            "servers_count": len(server_registry.list_servers()),
            "skills_count": len(skill_manager.list_skills()) if skill_manager else 0
        })
    
    @app.route("/api/config")
    async def api_config():
        """获取前端配置"""
        return jsonify({
            "mcpmarket_url": settings.mcpmarket_url,
            "server_url": settings.server_url
        })
    
    @app.route("/api/tools")
    async def api_tools():
        """获取 Uno 暴露的所有工具定义（供 GUI 使用）"""
        tools = []
        
        if get_servers_tool:
            tools.append(get_servers_tool.get_tool_definition())
        # if get_skill_tool:
        #     tools.append(get_skill_tool.get_tool_definition())
        if call_tool:
            tools.append(call_tool.get_tool_definition())
        if execute_tool:
            tools.append(execute_tool.get_tool_definition())
        
        return jsonify({"tools": tools})
    
    @app.route("/api/tools/call", methods=["POST"])
    async def api_tools_call():
        """执行工具调用（供 GUI 使用）"""
        body = await request.get_json()
        tool_name = body.get("name")
        arguments = body.get("arguments", {})
        
        # 从认证信息获取 user_id
        is_authenticated, user_id, user_info = await require_auth()
        
        # 如果未认证，使用测试用户 ID（开发环境）
        if not user_id:
            user_id = "gui-test-user"
            logger.warning("GUI API 使用测试用户 ID，生产环境请确保已登录")
        
        try:
            if tool_name == "uno_discover_servers":
                result = await get_servers_tool.execute(
                    server_names=arguments.get("server_names", []),
                    user_id=user_id
                )
            elif tool_name == "discover_skills":
                result = await get_skill_tool.execute(
                    question=arguments.get("question", ""),
                    skill_name=arguments.get("skill_name"),
                    user_id=user_id
                )
            elif tool_name == "uno_call_tool":
                result = await call_tool.execute(
                    tool_name=arguments.get("tool_name", ""),
                    arguments=arguments.get("arguments", {}),
                    user_id=user_id
                )
            elif tool_name == "uno_execute_script":
                result = await execute_tool.execute(
                    script=arguments.get("script", ""),
                    language=arguments.get("language", "bash"),
                    stdin=arguments.get("stdin"),
                    user_id=user_id
                )
            else:
                result = {"success": False, "error": f"未知工具: {tool_name}"}
            
            return jsonify({
                "content": [{
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                }],
                "isError": not result.get("success", True)
            })
            
        except Exception as e:
            logger.error(f"GUI 工具调用失败: {tool_name}, {e}")
            return jsonify({
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }), 500
    
    # ============= OAuth API（供 GUI 使用） =============
    
    @app.route("/api/oauth/token", methods=["POST"])
    async def api_oauth_token():
        """
        OAuth Token 交换端点（代理到 mcpmarket）
        
        GUI 用 authorization code 换取 access_token
        """
        try:
            import httpx
            body = await request.get_json()
            code = body.get("code")
            code_verifier = body.get("code_verifier")
            redirect_uri = body.get("redirect_uri")
            
            if not code or not code_verifier or not redirect_uri:
                return jsonify({"error": "Missing required parameters"}), 400
            
            # 代理请求到 mcpmarket
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{settings.mcpmarket_url}/oauth/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": "uno-gui",
                        "code_verifier": code_verifier
                    },
                    headers={"Accept": "application/json"}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    return jsonify(token_data)
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"error": response.text}
                    logger.error(f"Token 交换失败: {error_data}")
                    return jsonify(error_data), response.status_code
                    
        except Exception as e:
            logger.error(f"OAuth token 交换失败: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/oauth/verify", methods=["GET"])
    async def api_oauth_verify():
        """验证 access_token 是否有效"""
        try:
            import httpx
            
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"valid": False, "error": "No token provided"}), 401
            
            access_token = auth_header[7:]
            
            # 调用 mcpmarket API 验证
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.mcpmarket_url}/api/uno/verify-token",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return jsonify({
                        "valid": data.get("valid", False),
                        "user_id": data.get("user_id"),
                        "username": data.get("username")
                    })
                else:
                    return jsonify({"valid": False}), 401
                    
        except Exception as e:
            logger.error(f"Token 验证失败: {e}")
            return jsonify({"valid": False, "error": str(e)}), 500
    
    @app.route("/api/oauth/userinfo", methods=["GET"])
    async def api_oauth_userinfo():
        """获取当前用户信息"""
        try:
            import httpx
            
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "No token provided"}), 401
            
            access_token = auth_header[7:]
            
            # 调用 mcpmarket API 获取用户信息
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.mcpmarket_url}/api/uno/verify-token",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("valid"):
                        return jsonify({
                            "user_id": data.get("user_id"),
                            "username": data.get("username"),
                            "email": data.get("email")
                        })
                
                return jsonify({"error": "Invalid token"}), 401
                    
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return jsonify({"error": str(e)}), 500
    
    # ============= GUI 静态文件 =============
    
    @app.route("/gui")
    @app.route("/gui/")
    @app.route("/GUI")
    @app.route("/GUI/")
    async def gui_index():
        """GUI 首页"""
        from quart import send_from_directory
        templates_dir = GUI_DIR / "templates"
        return await send_from_directory(str(templates_dir), "index.html")
    
    @app.route("/gui/callback")
    @app.route("/gui/callback/")
    async def gui_oauth_callback():
        """
        OAuth 回调页面
        
        mcpmarket 授权后会重定向到这里，携带 code 和 state 参数。
        这个页面会加载 GUI 的 index.html，让前端 JS 处理回调。
        """
        from quart import send_from_directory
        templates_dir = GUI_DIR / "templates"
        return await send_from_directory(str(templates_dir), "index.html")
    
    @app.route("/gui/static/<path:filename>")
    @app.route("/GUI/static/<path:filename>")
    async def gui_static(filename: str):
        """GUI 静态文件"""
        from quart import send_from_directory
        static_dir = GUI_DIR / "static"
        return await send_from_directory(str(static_dir), filename)
    
    return app


# 创建应用实例
app = create_app()
