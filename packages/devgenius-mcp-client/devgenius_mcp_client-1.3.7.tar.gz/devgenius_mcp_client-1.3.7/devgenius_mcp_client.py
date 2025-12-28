#!/usr/bin/env python3
"""
DevGenius MCP Server - stdio 实现

标准的 MCP Server 实现，使用 stdio 协议与 AI IDE 通信。
这是最通用的方式，兼容所有支持 MCP 的 AI IDE（Cursor、Windsurf、Claude Desktop 等）。

使用方法:
1. 配置环境变量 DEVGENIUS_MCP_TOKEN
2. 在 AI IDE 的 MCP 配置中添加:
   {
     "mcpServers": {
       "devgenius": {
         "command": "python",
         "args": ["/path/to/devgenius_mcp_client.py"],
         "env": {
           "DEVGENIUS_MCP_TOKEN": "mcp_your_token",
           "DEVGENIUS_API_URL": "http://localhost:8000/api/v1/mcp",
           "DEVGENIUS_VERIFY_SSL": "false"
         }
       }
     }
   }
"""

import sys
import os
import asyncio
import logging
import io

# 强制设置 UTF-8 编码
sys.stdin = io.TextIOWrapper(
    sys.stdin.buffer,
    encoding='utf-8',
    errors='replace',
    newline=None
)
sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer,
    encoding='utf-8',
    errors='replace',
    newline=None,
    line_buffering=False,
    write_through=True
)
sys.stderr = io.TextIOWrapper(
    sys.stderr.buffer,
    encoding='utf-8',
    errors='replace',
    newline=None,
    line_buffering=False,
    write_through=True
)

# 配置日志（输出到文件）
from pathlib import Path

# 使用绝对路径，确保日志文件位置固定
log_file = Path(__file__).parent / 'devgenius_mcp_server.log'

# 创建支持 UTF-8 编码的文件处理器
file_handler = logging.FileHandler(
    str(log_file),
    mode='a',
    encoding='utf-8'  # 强制使用 UTF-8 编码
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
)

# 配置根日志记录器（重要：配置根 logger，让所有子模块继承）
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)

# 禁用第三方库的 DEBUG 日志（避免日志过多）
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

# 获取当前模块的 logger
logger = logging.getLogger(__name__)

# 记录日志文件位置
logger.info(f"📁 日志文件位置: {log_file.absolute()}")

# 添加当前目录到 Python 路径（确保能导入 devgenius 包）
sys.path.insert(0, str(Path(__file__).parent))

# 导入模块化组件
try:
    from devgenius.mcp_server import DevGeniusMCPServer
except ImportError as e:
    logger.error(f"无法导入 devgenius 模块: {e}")
    logger.error(f"Python 路径: {sys.path}")
    sys.stderr.write(f"导入错误: {e}\n")
    sys.stderr.flush()
    sys.exit(1)


async def async_main():
    """异步主函数"""
    try:
        logger.info("=" * 60)
        logger.info("DevGenius MCP Server 正在启动...")
        logger.info(f"Python 版本: {sys.version}")
        logger.info(f"平台: {sys.platform}")
        logger.info("=" * 60)
        
        # 从环境变量获取配置
        def parse_bool(env_name: str, default: bool) -> bool:
            raw = os.getenv(env_name)
            if raw is None:
                return default
            val = raw.strip().lower()
            if val in {"1", "true", "yes", "y", "on"}:
                return True
            if val in {"0", "false", "no", "n", "off"}:
                return False
            return default

        token = os.getenv("DEVGENIUS_MCP_TOKEN")
        api_url = os.getenv("DEVGENIUS_API_URL", "http://localhost:8000/api/v1/mcp")
        verify_ssl = parse_bool("DEVGENIUS_VERIFY_SSL", 'true')
        logger.info(f"API URL: {api_url}")
        logger.info(f"Token: {token[:20]}..." if token else "Token: 未设置")
        logger.info(f"Verify SSL: {verify_ssl}")
        
        if not token:
            logger.error("❌ 未设置 DEVGENIUS_MCP_TOKEN 环境变量")
            sys.stderr.write("错误: 请设置 DEVGENIUS_MCP_TOKEN 环境变量\n")
            sys.stderr.flush()
            sys.exit(1)
        
        # 使用模块化的 MCP Server
        server = DevGeniusMCPServer(token=token, api_url=api_url, verify_ssl=verify_ssl)
        await server.run()
        
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}", exc_info=True)
        sys.stderr.write(f"启动失败: {str(e)}\n")
        sys.stderr.flush()
        sys.exit(1)


def main():
    """同步入口点（供 uvx/pip 调用）"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
