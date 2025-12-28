"""
CLI命令入口
"""
import asyncio
from .main import main

def run_server():
    """运行API服务器的命令行入口点"""
    # 命令行参数现在由main函数内部处理
    asyncio.run(main()) 