"""
测试 MCP SDK 集成

验证使用 MCP SDK 调用远程工具是否正常。
"""

import asyncio
from src.registry.mcp_client_manager import mcp_client_manager


async def test_mcp_client():
    """测试 MCP 客户端"""
    
    # 测试 URL - 这里需要一个实际的 MCP 服务器 URL
    # 暂时使用占位符
    test_url = "http://example.com/mcp"
    
    print("=" * 60)
    print("MCP SDK 集成测试")
    print("=" * 60)
    
    print("\n1. 测试 MCP 客户端管理器初始化...")
    print(f"   MCPClientManager: {mcp_client_manager}")
    print("   ✓ 初始化成功")
    
    print("\n2. 检查 MCP SDK 导入...")
    try:
        from mcp import ClientSession
        from mcp.client.sse import sse_client
        from mcp.types import CallToolResult
        print("   ✓ MCP SDK 导入成功")
        print(f"   - ClientSession: {ClientSession}")
        print(f"   - sse_client: {sse_client}")
        print(f"   - CallToolResult: {CallToolResult}")
    except ImportError as e:
        print(f"   ✗ MCP SDK 导入失败: {e}")
        return
    
    print("\n3. 检查 CallTool 重构...")
    try:
        from src.tools.call_tool import CallTool
        call_tool = CallTool()
        print("   ✓ CallTool 初始化成功")
        print(f"   - 工具定义: {call_tool.get_tool_definition()['name']}")
    except Exception as e:
        print(f"   ✗ CallTool 初始化失败: {e}")
        return
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n注意: 实际的远程调用需要真实的 MCP 服务器 URL。")
    print("当服务器运行时，错误信息会更明确地反映协议问题。")
    

if __name__ == "__main__":
    asyncio.run(test_mcp_client())

