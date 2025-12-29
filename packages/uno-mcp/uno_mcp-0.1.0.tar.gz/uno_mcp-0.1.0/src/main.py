"""
Uno MCP Server - 入口文件
"""

import asyncio
import socket
import subprocess
import time
from hypercorn.config import Config
from hypercorn.asyncio import serve

from .config import settings
from .server import app
from .utils import setup_logging, get_logger


def check_port_in_use(host: str, port: int) -> bool:
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def kill_process_on_port(port: int, logger) -> bool:
    """强制终止占用指定端口的进程（包括子进程）"""
    try:
        # 使用 lsof 查找占用端口的进程
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            killed_pids = []
            
            for pid in pids:
                pid = pid.strip()
                if not pid:
                    continue
                
                try:
                    # 获取进程的所有子进程
                    try:
                        children_result = subprocess.run(
                            ['pgrep', '-P', pid],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        child_pids = []
                        if children_result.returncode == 0 and children_result.stdout.strip():
                            child_pids = children_result.stdout.strip().split('\n')
                    except:
                        child_pids = []
                    
                    # 先杀掉所有子进程
                    for child_pid in child_pids:
                        child_pid = child_pid.strip()
                        if child_pid:
                            logger.warning(f"发现子进程 {child_pid}，正在强制终止...")
                            try:
                                subprocess.run(['kill', '-9', child_pid], timeout=3, check=False)
                            except:
                                pass
                    
                    # 强制杀掉主进程
                    logger.warning(f"发现端口 {port} 被进程 {pid} 占用，正在强制终止...")
                    subprocess.run(['kill', '-9', pid], timeout=5, check=False)
                    killed_pids.append(pid)
                    
                except Exception as e:
                    logger.warning(f"终止进程 {pid} 时出错: {e}")
                    # 尝试使用 pkill 作为备选方案
                    try:
                        subprocess.run(['pkill', '-9', '-f', f':{port}'], timeout=3, check=False)
                    except:
                        pass
            
            if killed_pids:
                # 等待进程完全退出
                time.sleep(1)
                
                # 再次检查并强制杀掉残留进程
                for _ in range(3):
                    result = subprocess.run(
                        ['lsof', '-ti', f':{port}'],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        remaining_pids = result.stdout.strip().split('\n')
                        for pid in remaining_pids:
                            pid = pid.strip()
                            if pid:
                                logger.warning(f"发现残留进程 {pid}，再次强制终止...")
                                subprocess.run(['kill', '-9', pid], timeout=3, check=False)
                        time.sleep(0.5)
                    else:
                        break
                
                logger.info(f"已强制清理端口 {port} 上的进程: {', '.join(killed_pids)}")
                return True
        
        return False
        
    except subprocess.TimeoutExpired:
        logger.error(f"清理端口 {port} 超时")
        # 尝试使用 pkill 作为最后的备选方案
        try:
            logger.warning(f"尝试使用 pkill 强制清理端口 {port}...")
            subprocess.run(['pkill', '-9', '-f', f':{port}'], timeout=3, check=False)
            time.sleep(1)
        except:
            pass
        return False
    except FileNotFoundError:
        # lsof 命令不存在（非 Unix 系统）
        logger.warning("lsof 命令不可用，无法自动清理端口")
        return False
    except Exception as e:
        logger.error(f"清理端口 {port} 时出错: {e}")
        # 尝试使用 pkill 作为最后的备选方案
        try:
            logger.warning(f"尝试使用 pkill 强制清理端口 {port}...")
            subprocess.run(['pkill', '-9', '-f', f':{port}'], timeout=3, check=False)
            time.sleep(1)
        except:
            pass
        return False


def ensure_port_available(host: str, port: int, logger) -> bool:
    """确保端口可用，如果被占用则尝试强制清理"""
    if not check_port_in_use(host, port):
        logger.info(f"端口 {port} 可用")
        return True
    
    logger.warning(f"端口 {port} 被占用，尝试强制清理...")
    
    # 多次尝试清理，最多3次
    for attempt in range(3):
        if attempt > 0:
            logger.warning(f"第 {attempt + 1} 次尝试清理端口 {port}...")
        
        if kill_process_on_port(port, logger):
            # 等待端口释放，增加等待时间
            for i in range(15):
                time.sleep(0.5)
                if not check_port_in_use(host, port):
                    logger.info(f"端口 {port} 已成功释放")
                    return True
            
            # 如果仍然被占用，尝试最后一次强制清理
            if attempt < 2:
                logger.warning(f"端口 {port} 清理后仍被占用，尝试更强制的方式...")
                try:
                    # 使用 pkill 强制杀掉所有相关进程
                    subprocess.run(['pkill', '-9', '-f', f':{port}'], timeout=3, check=False)
                    time.sleep(1.5)
                except:
                    pass
        else:
            # 如果 kill_process_on_port 失败，尝试直接使用 pkill
            logger.warning(f"尝试使用 pkill 强制清理端口 {port}...")
            try:
                subprocess.run(['pkill', '-9', '-f', f':{port}'], timeout=3, check=False)
                time.sleep(1.5)
            except:
                pass
    
    # 最后检查一次
    if not check_port_in_use(host, port):
        logger.info(f"端口 {port} 已成功释放")
        return True
    
    logger.error(f"端口 {port} 清理后仍然被占用，无法启动服务器")
    logger.error(f"请手动执行以下命令终止占用端口的进程:")
    logger.error(f"  lsof -ti :{port} | xargs kill -9")
    logger.error(f"  或: pkill -9 -f ':{port}'")
    return False


def main():
    """主入口函数"""
    setup_logging()
    logger = get_logger("main")
    
    logger.info("=" * 60)
    logger.info("  Uno MCP Server")
    logger.info("  All-in-One MCP Gateway with Skills")
    logger.info("=" * 60)
    
    # 打印配置提示
    hints = settings.print_config_hints()
    for hint in hints:
        logger.info(hint)
    
    # 检查并清理端口
    host = "0.0.0.0" if settings.host == "0.0.0.0" else "127.0.0.1"
    if not ensure_port_available(host, settings.port, logger):
        logger.error(f"端口 {settings.port} 不可用，无法启动服务器")
        logger.error(f"请手动终止占用端口的进程或更改配置中的端口号")
        return
    
    # 配置 Hypercorn
    config = Config()
    config.bind = [f"{settings.host}:{settings.port}"]
    config.use_reloader = settings.debug
    config.accesslog = "-" if settings.debug else None
    
    logger.info(f"启动服务器: http://{settings.host}:{settings.port}")
    logger.info(f"调试模式: {settings.debug}")
    logger.info(f"GUI 地址: http://{settings.host}:{settings.port}/gui")
    
    # 运行服务器
    asyncio.run(serve(app, config))


if __name__ == "__main__":
    main()

