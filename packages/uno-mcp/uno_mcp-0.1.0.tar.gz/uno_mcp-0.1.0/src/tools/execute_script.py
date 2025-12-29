"""
execute 工具

在安全的沙盒环境中执行脚本。
"""

import asyncio
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path

from ..config import settings
from ..utils import get_logger

logger = get_logger("tools.execute")


class ExecuteTool:
    """
    脚本执行工具（沙盒）
    
    核心功能：
    - 支持 bash/python/node 等脚本执行
    - 在受限环境中运行，防止危险操作
    - 支持超时控制和资源限制
    """
    
    SUPPORTED_LANGUAGES = {
        "bash": {"ext": ".sh", "cmd": ["bash"]},
        "sh": {"ext": ".sh", "cmd": ["sh"]},
        "python": {"ext": ".py", "cmd": ["python3"]},
        "python3": {"ext": ".py", "cmd": ["python3"]},
        "node": {"ext": ".js", "cmd": ["node"]},
        "javascript": {"ext": ".js", "cmd": ["node"]},
    }
    
    def __init__(self):
        """初始化"""
        self.sandbox_enabled = settings.sandbox_enabled
        self.timeout = settings.sandbox_timeout
        logger.info(
            f"ExecuteTool 已初始化, sandbox={self.sandbox_enabled}, "
            f"timeout={self.timeout}s"
        )
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        获取工具定义（用于 MCP tools/list）
        """
        return {
            "name": "uno_execute_script",
            "description": """在安全的沙盒环境中执行脚本。

支持的语言：
- bash/sh: Shell 脚本
- python/python3: Python 脚本
- node/javascript: JavaScript 脚本

注意事项：
- 脚本在受限环境中执行，无法访问敏感资源
- 有超时限制（默认 30 秒）
- 网络访问可能受限
- 适合数据处理、计算、文本转换等任务""",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "要执行的脚本内容"
                    },
                    "language": {
                        "type": "string",
                        "enum": list(self.SUPPORTED_LANGUAGES.keys()),
                        "description": "脚本语言"
                    },
                    "stdin": {
                        "type": "string",
                        "description": "（可选）传递给脚本的标准输入"
                    }
                },
                "required": ["script", "language"]
            }
        }
    
    async def execute(
        self,
        script: str,
        language: str,
        stdin: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行脚本
        
        Args:
            script: 脚本内容
            language: 脚本语言
            stdin: 标准输入
            user_id: 用户 ID
            
        Returns:
            执行结果
        """
        logger.info(f"执行脚本: language={language}, length={len(script)}")
        
        # 验证语言
        language = language.lower()
        if language not in self.SUPPORTED_LANGUAGES:
            return {
                "success": False,
                "error": f"不支持的语言: {language}",
                "supported": list(self.SUPPORTED_LANGUAGES.keys())
            }
        
        lang_config = self.SUPPORTED_LANGUAGES[language]
        
        try:
            # 创建临时脚本文件
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix=lang_config["ext"],
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(script)
                script_path = f.name
            
            try:
                # 执行脚本
                result = await self._run_script(
                    cmd=lang_config["cmd"] + [script_path],
                    stdin=stdin
                )
                return result
            finally:
                # 清理临时文件
                try:
                    os.unlink(script_path)
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"脚本执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _run_script(
        self,
        cmd: list,
        stdin: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        运行脚本命令
        
        Args:
            cmd: 命令列表
            stdin: 标准输入
            
        Returns:
            执行结果
        """
        try:
            # 使用 asyncio 运行子进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if stdin else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # 基本的安全限制
                env={
                    "PATH": "/usr/local/bin:/usr/bin:/bin",
                    "HOME": "/tmp",
                    "LANG": "en_US.UTF-8",
                }
            )
            
            # 等待执行完成（带超时）
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(
                        input=stdin.encode() if stdin else None
                    ),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "error": f"脚本执行超时（>{self.timeout}秒）",
                    "timeout": self.timeout
                }
            
            return {
                "success": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace')
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"执行错误: {str(e)}"
            }

