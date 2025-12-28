"""
后端应用主入口模块
"""
import asyncio
from .main import main

if __name__ == "__main__":
    # 命令行参数现在由main函数内部处理
    asyncio.run(main()) 