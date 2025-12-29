"""
配置管理模块

Uno MCP Server 的配置可以通过以下方式设置（优先级从高到低）：
1. 环境变量（推荐用于生产环境）
2. .env 文件（推荐用于开发环境）
3. 默认值

示例：
  export OPENAI_API_KEY=sk-xxx
  uvx uno-mcp
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Uno 配置"""
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器地址")
    port: int = Field(default=8089, description="服务器端口")
    debug: bool = Field(default=False, description="调试模式")
    
    # 服务器 URL（用于 OAuth 回调和 well-known）
    server_url: str = Field(
        default="http://localhost:8089",
        description="服务器外部访问 URL"
    )
    
    # MCPMarket 配置（用于获取 server 数据和 OAuth）
    mcpmarket_url: str = Field(
        default="https://mcpmarket.cn",
        description="MCPMarket 服务地址"
    )
    mcpmarket_api_url: str = Field(
        default="https://mcpmarket.cn/api",
        description="MCPMarket API 地址"
    )
    
    # OpenAI 配置（用于 skill 智能匹配，可选）
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API Key（可选，不配置则使用关键词匹配）"
    )
    openai_base_url: Optional[str] = Field(
        default=None,
        description="OpenAI API Base URL（可选）"
    )
    skill_matcher_model: str = Field(
        default="gpt-4o-mini",
        description="Skill 匹配使用的模型"
    )
    
    # CORS 配置
    cors_origins: str = Field(
        default="*",
        description="CORS 允许的源，逗号分隔"
    )
    
    # 沙盒配置
    sandbox_enabled: bool = Field(
        default=True,
        description="是否启用脚本执行沙盒"
    )
    sandbox_timeout: int = Field(
        default=30,
        description="脚本执行超时时间（秒）"
    )
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str = Field(default="logs/uno.log", description="日志文件路径")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_cors_origins(self) -> List[str]:
        """获取 CORS 源列表"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def check_config(self) -> dict:
        """
        检查配置状态，返回各功能的可用性
        
        Returns:
            dict: 包含各功能可用性状态的字典
        """
        status = {
            "server": True,  # 服务器始终可用
            "openai_skill_match": self.openai_api_key is not None,
            "sandbox": self.sandbox_enabled,
        }
        return status
    
    def print_config_hints(self):
        """打印配置提示信息"""
        status = self.check_config()
        hints = []
        
        if not status["openai_skill_match"]:
            hints.append(
                "💡 提示: 未配置 OPENAI_API_KEY，Skill 匹配将使用关键词模式。"
                "\n   设置方法: export OPENAI_API_KEY=sk-xxx"
            )
        
        return hints


# 全局配置实例
settings = Settings()

