"""
get_skill 工具

根据用户问题，智能匹配最相关的 Skill（一组跨 server 的 tools 组合）。
"""

from typing import Dict, Any, Optional, List
from ..utils import get_logger

logger = get_logger("tools.get_skill")


class GetSkillTool:
    """
    获取 Skill 工具
    
    核心功能：
    - 接收用户问题/需求描述
    - 智能匹配最相关的 Skill
    - 返回 Skill 描述和完整的 tools 定义
    
    Skill 是跨多个 server 的 tools 组合，例如：
    - 旅游订票 skill: 酒店预订 + 机票/火车票 + 地图导航
    - 数据分析 skill: 数据获取 + 处理 + 可视化
    """
    
    def __init__(self, skill_manager: Any, server_registry: Any):
        """
        初始化
        
        Args:
            skill_manager: Skill 管理器实例
            server_registry: Server 注册表实例
        """
        self.skill_manager = skill_manager
        self.server_registry = server_registry
        logger.info("GetSkillTool 已初始化")
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        获取工具定义（用于 MCP tools/list）
        """
        # 获取所有 skill 的摘要
        skills_summary = self._build_skills_summary()
        
        return {
            "name": "discover_skills",
            "description": f"""根据问题或需求，智能匹配最相关的 Skill。

Skill 是一组相关工具的组合，可以跨多个 server，用于完成特定的复杂任务。

可用的 Skills:
{skills_summary}

传入你的问题或需求描述，将返回最匹配的 Skill，包含：
- Skill 的详细说明和使用指南
- 相关 tools 的完整定义（可直接调用）""",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "用户的问题或需求描述"
                    },
                    "skill_name": {
                        "type": "string",
                        "description": "（可选）直接指定 skill 名称，跳过智能匹配"
                    }
                },
                "required": ["question"]
            }
        }
    
    def _build_skills_summary(self) -> str:
        """
        构建所有 skill 的摘要信息
        """
        skills = self.skill_manager.list_skills()
        if not skills:
            return "（暂无预定义 skill，将根据问题动态推荐相关 tools）"
        
        lines = []
        for skill in skills:
            name = skill.get("name", "unknown")
            description = skill.get("description", "无描述")
            if len(description) > 50:
                description = description[:47] + "..."
            lines.append(f"- {name}: {description}")
        
        return "\n".join(lines)
    
    async def execute(
        self,
        question: str,
        skill_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行工具：根据问题匹配 skill
        
        Args:
            question: 用户问题或需求
            skill_name: 直接指定的 skill 名称（可选）
            user_id: 用户 ID
            
        Returns:
            Skill 信息和完整的 tools 定义
        """
        logger.info(f"匹配 skill: question='{question[:50]}...', skill_name={skill_name}")
        
        # 如果直接指定了 skill 名称
        if skill_name:
            skill = await self.skill_manager.get_skill(skill_name)
            if not skill:
                return {
                    "success": False,
                    "error": f"Skill '{skill_name}' 不存在",
                    "available_skills": [s["name"] for s in self.skill_manager.list_skills()]
                }
        else:
            # 智能匹配
            skill = await self.skill_manager.match_skill(question)
            if not skill:
                return {
                    "success": False,
                    "error": "无法匹配到合适的 skill",
                    "suggestion": "请尝试使用 uno_discover_servers 获取具体 server 的 tools"
                }
        
        # 获取 skill 中所有 tools 的完整定义
        tools_definitions = await self._get_skill_tools(skill)
        
        return {
            "success": True,
            "skill": {
                "name": skill.get("name"),
                "description": skill.get("description"),
                "instructions": skill.get("instructions", ""),
                "tags": skill.get("tags", [])
            },
            "tools": tools_definitions,
            "total_tools": len(tools_definitions),
            "usage_hint": skill.get("usage_hint", "")
        }
    
    async def _get_skill_tools(self, skill: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        获取 skill 中所有 tools 的完整定义
        
        Args:
            skill: Skill 配置
            
        Returns:
            Tools 定义列表
        """
        tools = []
        tool_refs = skill.get("tools", [])
        
        for ref in tool_refs:
            # 格式: "server_name.tool_name" 或 {"server": "xxx", "tool": "yyy"}
            if isinstance(ref, str):
                parts = ref.split(".", 1)
                if len(parts) == 2:
                    server_name, tool_name = parts
                else:
                    continue
            elif isinstance(ref, dict):
                server_name = ref.get("server")
                tool_name = ref.get("tool")
            else:
                continue
            
            # 获取 tool 定义
            tool_def = await self.server_registry.get_tool_definition(
                server_name, tool_name
            )
            if tool_def:
                # 添加全名标识
                tool_def["full_name"] = f"{server_name}.{tool_name}"
                tool_def["server"] = server_name
                tools.append(tool_def)
        
        return tools

