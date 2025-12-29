"""
Skill 匹配器

基于语义相似度或 LLM 匹配最相关的 Skill。
"""

from typing import Dict, Any, Optional, List
import json

from ..config import settings
from ..utils import get_logger

logger = get_logger("skills.matcher")


class SkillMatcher:
    """
    Skill 匹配器
    
    支持两种匹配模式：
    1. 关键词/标签匹配（快速，无需 API 调用）
    2. LLM 语义匹配（精准，需要 OpenAI API）
    """
    
    def __init__(self, skills: Dict[str, Dict[str, Any]]):
        """
        初始化
        
        Args:
            skills: Skill 配置字典
        """
        self._skills = skills
        self._openai_client = None
        self._use_llm = bool(settings.openai_api_key)
        
        logger.info(f"SkillMatcher 初始化, use_llm={self._use_llm}")
    
    async def initialize(self):
        """初始化 OpenAI 客户端"""
        if self._use_llm:
            try:
                from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url
                )
                logger.info("OpenAI 客户端初始化成功")
            except Exception as e:
                logger.warning(f"OpenAI 客户端初始化失败: {e}")
                self._use_llm = False
    
    async def match(self, question: str) -> Optional[str]:
        """
        匹配最相关的 skill
        
        Args:
            question: 用户问题
            
        Returns:
            匹配的 skill 名称
        """
        if not self._skills:
            return None
        
        # 优先尝试 LLM 匹配
        if self._use_llm and self._openai_client:
            result = await self._llm_match(question)
            if result:
                return result
        
        # 回退到关键词匹配
        return self._keyword_match(question)
    
    async def _llm_match(self, question: str) -> Optional[str]:
        """
        使用 LLM 进行语义匹配
        
        Args:
            question: 用户问题
            
        Returns:
            匹配的 skill 名称
        """
        try:
            # 构建 skills 摘要
            skills_info = []
            for name, skill in self._skills.items():
                skills_info.append({
                    "name": name,
                    "description": skill.get("description", ""),
                    "tags": skill.get("tags", [])
                })
            
            prompt = f"""你是一个 Skill 匹配助手。根据用户的问题，从可用的 Skills 中选择最匹配的一个。

可用的 Skills:
{json.dumps(skills_info, ensure_ascii=False, indent=2)}

用户问题: {question}

请只返回最匹配的 skill 名称（name 字段），如果没有合适的匹配，返回 "none"。
只返回名称，不要其他内容。"""

            response = await self._openai_client.chat.completions.create(
                model=settings.skill_matcher_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            # 验证结果
            if result != "none" and result in self._skills:
                logger.info(f"LLM 匹配成功: {result}")
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"LLM 匹配失败: {e}")
            return None
    
    def _keyword_match(self, question: str) -> Optional[str]:
        """
        使用关键词进行简单匹配
        
        Args:
            question: 用户问题
            
        Returns:
            匹配的 skill 名称
        """
        question_lower = question.lower()
        
        best_match = None
        best_score = 0
        
        for name, skill in self._skills.items():
            score = 0
            
            # 检查标签匹配
            tags = skill.get("tags", [])
            for tag in tags:
                if tag.lower() in question_lower:
                    score += 2
            
            # 检查名称匹配
            if name.lower() in question_lower:
                score += 3
            
            # 检查描述中的关键词
            description = skill.get("description", "").lower()
            keywords = skill.get("keywords", [])
            for kw in keywords:
                if kw.lower() in question_lower:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = name
        
        if best_score > 0:
            logger.info(f"关键词匹配: {best_match}, score={best_score}")
            return best_match
        
        return None

