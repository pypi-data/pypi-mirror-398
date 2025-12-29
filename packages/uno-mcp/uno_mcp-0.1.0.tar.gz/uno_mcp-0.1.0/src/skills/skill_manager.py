"""
Skill 管理器

加载和管理预定义的 Skills。
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..utils import get_logger
from .matcher import SkillMatcher

logger = get_logger("skills.skill_manager")


class SkillManager:
    """
    Skill 管理器
    
    功能：
    - 加载预定义 skill（从 YAML 文件）
    - 智能匹配 skill（基于问题）
    - 管理 skill 的元数据和 tools 引用
    """
    
    def __init__(self, skills_dir: Optional[Path] = None):
        """
        初始化
        
        Args:
            skills_dir: Skills 配置目录
        """
        self.skills_dir = skills_dir or Path(__file__).parent / "presets"
        self._skills: Dict[str, Dict[str, Any]] = {}
        self._matcher: Optional[SkillMatcher] = None
        
        logger.info(f"SkillManager 初始化, skills_dir={self.skills_dir}")
    
    async def initialize(self):
        """初始化：加载 skills 和匹配器"""
        self._load_skills()
        self._matcher = SkillMatcher(self._skills)
        await self._matcher.initialize()
        logger.info(f"SkillManager 初始化完成, 加载 {len(self._skills)} 个 skills")
    
    def _load_skills(self):
        """从目录加载所有 skill 配置"""
        self._skills = {}
        
        if not self.skills_dir.exists():
            logger.warning(f"Skills 目录不存在: {self.skills_dir}")
            return
        
        for file_path in self.skills_dir.glob("*.yaml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    skill = yaml.safe_load(f)
                
                if skill and "name" in skill:
                    self._skills[skill["name"]] = skill
                    logger.debug(f"加载 skill: {skill['name']}")
                    
            except Exception as e:
                logger.error(f"加载 skill 文件失败: {file_path}, {e}")
        
        logger.info(f"共加载 {len(self._skills)} 个 skills")
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """
        列出所有 skill（摘要）
        
        Returns:
            Skill 摘要列表
        """
        return [
            {
                "name": s["name"],
                "description": s.get("description", ""),
                "tags": s.get("tags", [])
            }
            for s in self._skills.values()
        ]
    
    async def get_skill(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定 skill
        
        Args:
            name: Skill 名称
            
        Returns:
            Skill 完整配置
        """
        return self._skills.get(name)
    
    async def match_skill(self, question: str) -> Optional[Dict[str, Any]]:
        """
        根据问题匹配最相关的 skill
        
        Args:
            question: 用户问题
            
        Returns:
            匹配的 skill
        """
        if not self._matcher:
            logger.warning("Matcher 未初始化")
            return None
        
        matched_name = await self._matcher.match(question)
        if matched_name:
            return self._skills.get(matched_name)
        
        return None
    
    def add_skill(self, skill: Dict[str, Any]) -> bool:
        """
        添加 skill（运行时）
        
        Args:
            skill: Skill 配置
            
        Returns:
            是否添加成功
        """
        name = skill.get("name")
        if not name:
            return False
        
        self._skills[name] = skill
        logger.info(f"添加 skill: {name}")
        return True
    
    def remove_skill(self, name: str) -> bool:
        """
        移除 skill
        
        Args:
            name: Skill 名称
            
        Returns:
            是否移除成功
        """
        if name in self._skills:
            del self._skills[name]
            logger.info(f"移除 skill: {name}")
            return True
        return False

