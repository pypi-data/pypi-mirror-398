import os
import asyncio
import sys
import uvicorn
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
import argparse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from .state import set_mcp_session, get_openai_client
from .app import app
from .tools import get_tools
from .config import Config

async def main():
    """应用主入口"""
    # 打印版本号
    try:
        import importlib.metadata
        version = importlib.metadata.version("lightpdf-aipdf-backend")
        print(f"LightPDF AI-PDF Backend v{version}, Debug = {os.getenv('DEBUG')}", file=sys.stderr)
    except Exception as e:
        print(f"LightPDF AI-PDF Backend (版本信息获取失败), Debug = {os.getenv('DEBUG')}", file=sys.stderr)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="LightPDF AI-PDF Backend服务")
    parser.add_argument("-p", "--port", type=int, default=3300, help="指定后端服务监听端口，默认3300")
    # 传输模式互斥组：--sse 或 --http 可接受 MCP 端口号（默认3301）
    transport_group = parser.add_mutually_exclusive_group()
    transport_group.add_argument("-s", "--sse", type=int, nargs="?", const=3301, default=None, metavar="MCP_PORT", help="使用SSE连接外部MCP服务器，可指定端口（默认3301）")
    transport_group.add_argument("--http", type=int, nargs="?", const=3301, default=None, metavar="MCP_PORT", help="使用streamable-http连接外部MCP服务器，可指定端口（默认3301）")
    args = parser.parse_args()
    
    # 更新全局变量
    port = args.port
    if args.sse is not None:
        transport_mode, mcp_port = "sse", args.sse
    elif args.http is not None:
        transport_mode, mcp_port = "http", args.http
    else:
        transport_mode, mcp_port = "stdio", 0
    
    # 初始化 OpenAI 客户端 - 只需调用get_openai_client即可
    get_openai_client()
    
    if transport_mode == "sse":
        # 使用SSE连接MCP服务器
        mcp_url = f"http://127.0.0.1:{mcp_port}/sse/"
        print(f"使用SSE连接MCP服务器: {mcp_url}", file=sys.stderr)
        try:
            async with sse_client(mcp_url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    set_mcp_session(session)
                    print(f"正在启动服务，监听端口: {port}")
                    config = uvicorn.Config(app, host="0.0.0.0", port=port)
                    server = uvicorn.Server(config)
                    await server.serve()
        except Exception as e:
            print(f"SSE连接MCP服务器失败: {e}", file=sys.stderr)
            print("请确保MCP服务器已经以SSE模式启动: uvx lightpdf-aipdf-mcp -p 3301 --sse", file=sys.stderr)
            sys.exit(1)
    elif transport_mode == "http":
        # 使用streamable-http连接MCP服务器
        mcp_url = f"http://127.0.0.1:{mcp_port}/mcp"
        print(f"使用streamable-http连接MCP服务器: {mcp_url}", file=sys.stderr)
        try:
            async with streamablehttp_client(mcp_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    set_mcp_session(session)
                    print(f"正在启动服务，监听端口: {port}")
                    config = uvicorn.Config(app, host="0.0.0.0", port=port)
                    server = uvicorn.Server(config)
                    await server.serve()
        except Exception as e:
            print(f"streamable-http连接MCP服务器失败: {e}", file=sys.stderr)
            print("请确保MCP服务器已经以HTTP模式启动: uvx lightpdf-aipdf-mcp -p 3301", file=sys.stderr)
            sys.exit(1)
    else:
        # 准备 MCP 服务参数 (STDIO方式)
        mcp_package = os.getenv("MCP_PACKAGE", "lightpdf-aipdf-mcp@latest")
        mcp_index_url = os.getenv("MCP_INDEX_URL")  # 如需使用 TestPyPI: https://test.pypi.org/simple
        mcp_args_prefix = []
        if mcp_index_url:
            mcp_args_prefix = ["--index-url", mcp_index_url, "--extra-index-url", "https://pypi.org/simple"]

        # DEBUG 模式下优先使用本地 whl（仅当文件存在时）
        repo_root = Path(__file__).resolve().parents[4]
        local_whl = repo_root / "mcp_server" / "dist" / "lightpdf_aipdf_mcp-0.0.1-py3-none-any.whl"
        use_local_whl = bool(os.getenv("DEBUG")) and local_whl.is_file()

        server_params = StdioServerParameters(
            command="uvx",
            args=(["-n", str(local_whl)]
                  if use_local_whl
                  else mcp_args_prefix + [mcp_package]),
            env={
                **dict(filter(lambda x: x[1] is not None, {
                    "API_ENDPOINT": Config.API_ENDPOINT,
                    "API_KEY": os.getenv("API_KEY"),
                    "DEBUG": os.getenv("DEBUG"),
                }.items()))
            }
        )
        
        # 启动 MCP 会话 (STDIO方式)
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # 设置全局 MCP 会话
                set_mcp_session(session)

                print(f"正在启动服务，监听端口: {port}")
                # 启动 FastAPI 服务器
                config = uvicorn.Config(app, host="0.0.0.0", port=port)
                server = uvicorn.Server(config)
                await server.serve()

# 确保与原始 main 函数相同
if __name__ == "__main__":
    # 启动服务
    asyncio.run(main()) 