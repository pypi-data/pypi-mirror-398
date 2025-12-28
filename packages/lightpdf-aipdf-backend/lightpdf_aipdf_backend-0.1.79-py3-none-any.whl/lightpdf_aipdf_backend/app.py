import sys
import os
import time
from fastapi import FastAPI, HTTPException, File, UploadFile, Header, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from contextlib import asynccontextmanager
from typing import List, Dict, AsyncGenerator, Any, Tuple, TypedDict, Optional
from uuid import uuid4
import json
import asyncio
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from .models import ChatRequest, Message, FileInfo
from .file_handler import handle_batch_file_upload
from .chat_handler import process_messages, generate_chat_response, get_file_references, validate_and_fix_messages, collect_stream_content, LANGUAGE_CODE_TO_ENGLISH, ToolCall
from .utils import async_generator_to_json_stream, safe_json_loads
from .state import cleanup_inactive_sessions, store_file_info, get_qa_state, set_qa_state, get_openai_client, get_session_history, set_session_history, append_session_history, redis_client, store_session_file_pages, get_session_file_pages, store_session_file_urls
from .config import Config
from .tools import get_tools
from .tasks import tool_task_async


def _debug_enabled() -> bool:
    """仅当 DEBUG=1/true/yes/on 时输出调试日志（避免生产噪音）"""
    v = (os.getenv("DEBUG") or "").strip().lower()
    return v in {"1", "true", "yes", "y", "on"}


def _dbg(msg: str):
    if not _debug_enabled():
        return
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[backend][{ts}] {msg}", file=sys.stderr, flush=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    Args:
        app: FastAPI应用实例
    """
    # 应用启动时的初始化
    yield
    # 应用关闭时的清理
    cleanup_inactive_sessions()

# 创建FastAPI应用
app = FastAPI(title="LightPDF Agent API", lifespan=lifespan)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root() -> dict:
    """
    API根路径
    Returns:
        dict: API启动信息
    """
    return {"message": "LightPDF Agent API已启动"}

@app.post("/api/upload")
async def upload_file(
    files: List[UploadFile] = File(None),
    session_id: Optional[str] = Header(None, alias="Session-ID"),
    extends: Optional[str] = None
) -> JSONResponse:
    """
    处理文件上传请求
    Args:
        files: 要上传的文件列表
        session_id: 会话ID
        extends: 可选的文件信息列表JSON字符串，用于直接保存并返回文件信息
    Returns:
        JSONResponse: 文件信息列表
    """
    # 准备响应头
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
    }

    # 如果没有session_id，创建新的
    if not session_id:
        session_id = str(uuid4())
        headers["Set-Session-ID"] = session_id

    _dbg(f"/api/upload enter session_id={session_id} files={len(files) if files else 0} has_extends={bool(extends)}")
    
    # 处理extends参数 - 如果提供了extends参数，直接解析并返回
    if extends:
        try:
            file_info_list = json.loads(extends)
            # 转换为FileInfo对象
            results = []
            for info in file_info_list:
                file_info = FileInfo(
                    file_id=info.get("file_id"),
                    filename=info.get("filename"),
                    content_type=info.get("content_type"),
                    path=info.get("path"),
                    url=info.get("url")
                )
                # 存储文件信息到会话
                store_file_info(session_id, file_info)
                results.append(file_info)

            # 存储 pages 信息（如果有）
            try:
                store_session_file_pages(session_id, file_info_list)
                # 存储 path->url 映射（用于不支持 oss:// 的能力）
                store_session_file_urls(session_id, results)
            except Exception:
                pass
            
            # 将FileInfo对象转换为字典
            results_dict = [result.model_dump() for result in results]
            
            return JSONResponse(
                content=results_dict,
                headers=headers
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"解析extends参数失败: {str(e)}")
    
    # 如果没有extends参数，执行常规的文件上传处理
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="未提供文件且未提供extends参数")
        
    # 使用批量处理函数处理所有文件
    results = await handle_batch_file_upload(files, session_id)
    # 存储 path->url 映射（用于不支持 oss:// 的能力）
    try:
        store_session_file_urls(session_id, results)
    except Exception:
        pass
    
    # 将FileInfo对象转换为字典
    results_dict = [result.model_dump() for result in results]
    
    return JSONResponse(
        content=results_dict,
        headers=headers
    )

@app.post("/api/chat0")
async def chat0(
    request: ChatRequest,
    session_id: Optional[str] = Header(None, alias="Session-ID")
):
    """处理聊天请求"""
    try:
        # 准备响应头
        headers = {
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
        }
        
        # 如果没有session_id，创建新的
        if not session_id:
            session_id = str(uuid4())
            headers["Set-Session-ID"] = session_id
        
        # 创建一个用户消息
        user_message = Message(
            role="user",
            content=request.content,
            file_ids=request.file_ids,
            file_infos=request.file_infos
        )
        
        # 处理消息
        processed_messages = await process_messages(session_id, [user_message])
        
        # 生成响应
        return StreamingResponse(
            async_generator_to_json_stream(generate_chat_response(session_id, processed_messages, instructions=request.instructions, language=request.language)),
            media_type="application/x-ndjson",
            headers=headers
        )
    except Exception as e:
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=f"LightPDF Agent处理错误: {error_msg}") 

async def fix_link_in_markdown(content: str, session_id: Optional[str] = None) -> str:
    """
    查找并自定义处理markdown中的所有链接
    例：example.com域名改为baidu，有foo参数的改foo=bar，其它不变。
    """
    urls = []
    if session_id:
        urls = redis_client.lrange(f"qa:{session_id}:tool_result", 0, -1)

    def link_replacer(match):
        text = match.group(1)
        url = match.group(2)
        # 解析url
        parsed = urlparse(url)
        
        if "oss" in parsed.netloc and "aliyuncs" in parsed.netloc:
            for file_url in urls:
                file_parsed = urlparse(file_url)
                if file_parsed.netloc == parsed.netloc and file_parsed.path == parsed.path:
                    return f'[{text}]({file_url})'
            else:
                qs = parse_qs(parsed.query)

                if "x-oss-signature-version" not in qs:
                    qs["x-oss-signature-version"] = ["OSS4-HMAC-SHA256"]
                if "x-oss-expires" not in qs:
                    qs["x-oss-expires"] = ["3600"]

                new_query = urlencode(qs, doseq=True)
                new_url = urlunparse(parsed._replace(query=new_query))
        # 其他链接不变
        else:
            new_url = url
        return f'[{text}]({new_url})'

    # 支持带title的链接（title会被忽略）
    pattern = r'\[([^\]]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)'
    return re.sub(pattern, link_replacer, content)

# 新增：统一ndjson流式输出工具

def ndjson_stream(generator_func):
    async def wrapper(*args, **kwargs):
        """
        将异步生成器输出转为ndjson流
        Yields:
            bytes: ndjson流
        """
        async for item in generator_func(*args, **kwargs):
            if isinstance(item, (dict, list)):
                yield (json.dumps(item, ensure_ascii=False) + "\n").encode("utf-8")
            elif isinstance(item, str):
                yield (item.rstrip('\n') + "\n").encode("utf-8")
            else:
                yield str(item).encode("utf-8") + b"\n"
    return wrapper

async def process_message(session_id: str, msg: Message) -> List[Dict]:
    """处理消息列表，包括文件处理和格式转换
    
    Args:
        session_id: 用户会话ID
        message: 消息
        
    Returns:
        List[Dict]: 处理后的消息列表
    """
    # 转换消息并处理文件
    processed_messages = []
    
    # 定义一个内部函数来处理添加文件链接
    def add_file_links_to_message(message_dict: Dict, files: List[Dict[str, str]]) -> Dict:
        """将文件信息添加到消息中，使用JSON格式
        
        Args:
            message_dict: 消息字典
            files: 文件信息列表，每个文件包含path和可选的name、password
            
        Returns:
            Dict: 更新后的消息字典
        """
        if files:
            # 直接添加files字段，与MCP工具结构兼容
            message_dict["content"] += "\n\n---\n\n" + json.dumps(files, ensure_ascii=False)
        return message_dict
    
    # 定义一个内部函数来处理直接的文件信息，返回JSON格式
    def get_file_info_json(file_infos: List) -> List[Dict[str, str]]:
        """从直接文件信息获取JSON格式的文件列表
        
        Args:
            file_infos: 文件信息列表
            
        Returns:
            List[Dict[str, str]]: 文件信息列表，JSON格式
        """
        files = []
        for file_info in file_infos:
            file_data = {
                "path": file_info.path,
                "name": file_info.filename
            }
            # 如果文件信息中包含密码，添加到结果中
            if hasattr(file_info, 'password') and file_info.password:
                file_data["password"] = file_info.password
            
            files.append(file_data)
        return files

    # 基本消息结构
    message_dict = {"role": msg.role, "content": msg.content}
    
    # 处理assistant角色的工具调用
    if msg.role == "assistant" and msg.tool_calls:
        message_dict["tool_calls"] = msg.tool_calls
        # 当有工具调用时，content可以为空字符串
        if not message_dict["content"]:
            message_dict["content"] = ""
    
    # 处理tool角色的工具响应
    if msg.role == "tool":
        if msg.tool_call_id:
            message_dict["tool_call_id"] = msg.tool_call_id
        if msg.name:
            message_dict["name"] = msg.name
        # 确保tool角色必须有tool_call_id和name
        if "tool_call_id" not in message_dict or "name" not in message_dict:
            return []
    
    # 如果消息包含文件ID
    if msg.file_ids:
        file_urls = get_file_references(msg.file_ids, session_id)
        message_dict = add_file_links_to_message(message_dict, file_urls)
    
    # 如果消息包含直接的文件信息
    if msg.file_infos:
        # 记录 pages 信息到 redis（用于后续 cost_check，不进入工具参数）
        try:
            store_session_file_pages(session_id, msg.file_infos)
            store_session_file_urls(session_id, msg.file_infos)
        except Exception:
            pass
        # DEBUG：打印前端传入的 path/url，便于确认 oss->http 替换是否可用
        try:
            v = (os.getenv("DEBUG") or "").strip().lower()
            if v in {"1", "true", "yes", "y", "on"}:
                pairs = []
                for fi in msg.file_infos:
                    p = getattr(fi, "path", None) if not isinstance(fi, dict) else fi.get("path")
                    u = getattr(fi, "url", None) if not isinstance(fi, dict) else fi.get("url")
                    if p:
                        pairs.append({"path": p, "url": u})
                _dbg(f"file_infos(path/url) session_id={session_id} pairs={pairs}")
        except Exception:
            pass
        file_urls = get_file_info_json(msg.file_infos)
        message_dict = add_file_links_to_message(message_dict, file_urls)
    
    processed_messages.append(message_dict)
    
    # 返回完整的会话历史
    return validate_and_fix_messages(processed_messages)

# 合并后的通用LLM流式推理生成器
async def llm_stream_generator(qa_id: str, session_id: str, first_round: bool = False, instructions: Optional[str] = None, language: Optional[str] = None) -> AsyncGenerator:
    """
    通用LLM流式推理生成器。
    Args:
        qa_id: 问答ID
        session_id: 会话ID
        first_round: 是否为首轮
    Yields:
        dict: 流式输出内容
    """
    try:
        if first_round:
            _dbg(f"llm_stream_generator start first_round qa_id={qa_id} session_id={session_id}")
            yield {"type": "task", "id": qa_id}

        openai_client = get_openai_client()
        tools = await get_tools()

        # 完全依赖流式响应
        while True:
            # 使用流式请求 - 异步客户端
            from openai.types.chat import ChatCompletionStreamOptionsParam
            
            # 准备发送给API的消息
            request_messages = get_session_history(session_id).copy()
            
            # 获取指令：优先使用前端传递的指令，否则使用配置文件中的默认指令
            if not instructions:
                instructions = Config.get_default_instructions() or ""

            if language:
                language_instruction = f"- If the user does not specify a language, respond in {LANGUAGE_CODE_TO_ENGLISH.get(language, f"{language} language")}."
                instructions = f"{instructions}\n{language_instruction}" if instructions else language_instruction
            
            # 如果有指令则添加系统提示词
            if instructions:
                request_messages.insert(0, {"role": "system", "content": instructions})
            
            _dbg(
                f"openai.create(stream) qa_id={qa_id} session_id={session_id} "
                f"model={Config.OPENAI_MODEL} msgs={len(request_messages)} tools={len(tools)}"
            )
            response = await openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=request_messages,
                tools=tools,
                parallel_tool_calls=False,
                stream=True,
                stream_options=ChatCompletionStreamOptionsParam(include_usage=True)  # 使用类型化对象
            )
            _dbg(f"openai.create(stream) returned qa_id={qa_id}")
            
            full_content = ""
            finish_reason = None
            tool_calls_data = []
            yield_content = False
            usage_info = None  # 初始化usage_info变量，用于存储token统计信息
            
            # 收集流式响应内容
            async for item in collect_stream_content(response):
                if isinstance(item, tuple):
                    if len(item) == 4:
                        full_content, finish_reason, tool_calls_data, usage_info = item
                        full_content = await fix_link_in_markdown(full_content, session_id)
                else:
                    if not yield_content:
                        # 第一次消息通知
                        yield {
                            "type": "stream_start"
                        }
                        yield_content = True
                    
                    yield item
            
            # 如果需要调用工具
            if finish_reason == 'tool_calls' and tool_calls_data:
                _dbg(f"finish_reason=tool_calls qa_id={qa_id} tool_calls={len(tool_calls_data)}")
                if yield_content:
                    # 停止当前流
                    yield {
                        "type": "stream_end",
                        "content": full_content
                    }
                
                # 转换工具调用格式并创建消息
                tool_calls = []
                for tc_data in tool_calls_data:
                    tc_function = tc_data["function"]
                    if tc_data["id"] and tc_function["name"]:
                        tool_calls.append({
                            'id': tc_data["id"],
                            'function': {
                                'name': tc_function["name"],
                                'arguments': tc_function["arguments"]
                            }
                        })
                
                # 创建助手消息
                append_session_history(session_id, {
                    "role": "assistant",
                    "content": full_content or "",
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function", 
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"]
                            }
                        } for tc in tool_calls
                    ]
                })

                # 只输出第一个type=tool_start，其余工具调用信息存入redis队列
                from .state import redis_client
                if len(tool_calls) > 1:
                    queue_key = f"qa:{qa_id}:tool_queue"
                    for tc in tool_calls[1:]:
                        redis_client.rpush(queue_key, json.dumps(tc, ensure_ascii=False))
                        redis_client.expire(queue_key, 3600)

                tc = tool_calls[0]
                tool_name = tc["function"]["name"]
                args = safe_json_loads(tc["function"]["arguments"])
                
                # === 成本检查：在返回 tool_start 之前检查是否允许 ===
                from .tasks import check_tool_cost
                agent_task_id = get_qa_state(f"{qa_id}:agent_task_id") or qa_id
                use_advanced_model = get_qa_state(f"{qa_id}:use_advanced_model")
                area = get_qa_state(f"{qa_id}:area")
                # 汇总 pages：按 files[].path 从 session_file_pages:{session_id} 取
                pages_total = None
                try:
                    files = args.get("files", []) if isinstance(args, dict) else []
                    total = 0
                    hit = False
                    for f in files:
                        if not isinstance(f, dict):
                            continue
                        p = f.get("path")
                        if not p:
                            continue
                        v = get_session_file_pages(session_id, p)
                        if v:
                            total += int(v)
                            hit = True
                    pages_total = total if hit else None
                except Exception:
                    pages_total = None

                # package_files：纯打包下载链接，不做成本校验
                if tool_name != "package_files":
                    _dbg(f"cost_check start qa_id={qa_id} agent_task_id={agent_task_id} tool={tool_name} pages_total={pages_total}")
                    t_cost = time.monotonic()
                    cost_check_result = await check_tool_cost(
                        agent_task_id,
                        tool_name,
                        args,
                        pages=pages_total,
                        use_advanced_model=use_advanced_model,
                        area=area
                    )
                    _dbg(f"cost_check end qa_id={qa_id} tool={tool_name} allow={cost_check_result.allow} elapsed_ms={int((time.monotonic()-t_cost)*1000)}")
                    
                    if not cost_check_result.allow:
                        # 成本检查拒绝：清空工具队列，返回错误
                        redis_client.delete(f"qa:{qa_id}:tool_queue")
                        # 为所有 tool_calls 添加 tool message，避免 OpenAI API 报错
                        for rejected_tc in tool_calls:
                            append_session_history(session_id, {
                                "role": "tool",
                                "tool_call_id": rejected_tc["id"],
                                "content": cost_check_result.message
                            })
                        set_qa_state(qa_id, {"status": "finished", "content": cost_check_result.message, "session_id": session_id})
                        yield cost_check_result.get_error_response(tool_name)
                        return
                
                # === 成本检查通过，继续正常流程 ===
                args.pop("files", None)
                args.pop("latex_code", None)
                _dbg(f"tool_start emit qa_id={qa_id} tool={tool_name}")
                yield {
                    "type": "tool_start",
                    "content": json.dumps({
                        "id": tc["id"],
                        "function": {
                            "name": tool_name,
                            "arguments": args
                        }
                    })
                }

                set_qa_state(qa_id, {"status": "tool_calling", "tool_call_args": tc, "session_id": session_id})
                import asyncio
                _dbg(f"tool_task_async schedule qa_id={qa_id} tool={tool_name}")
                asyncio.create_task(tool_task_async(qa_id, session_id, tc))
                return
                
            else:
                # 如果不需要调用工具，直接结束流
                stream_end_data = {
                    "type": "stream_end",
                    "content": full_content
                }
                
                # 如果有使用统计信息，添加到输出中
                if usage_info:
                    stream_end_data["usage"] = usage_info
                
                yield stream_end_data
                
                # 更新会话历史
                append_session_history(session_id, {
                    "role": "assistant",
                    "content": full_content
                })

                set_qa_state(qa_id, {"status": "finished", "content": "task finished", "session_id": session_id})
                yield {
                    "type": "task_end"
                }
                break

    except Exception as e:
        _dbg(f"llm_stream_generator exception qa_id={qa_id}: {str(e)}")
        set_qa_state(qa_id, {"status": "finished", "content": f"LLM异常: {str(e)}", "session_id": session_id})
        yield {"type": "error", "content": f"LLM异常: {str(e)}"}



@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    session_id: Optional[str] = Header(None, alias="Session-ID")
):
    """
    多轮 LLM+工具调用主入口。
    - 初始化会话，写入首轮 user 消息，流式输出 LLM 内容。
    - 遇到工具调用时断流，type=tool_start，状态写入 redis 并异步调度工具。
    - 正常结束时 type=stream_end，附带 usage。
    - 仅负责首轮，后续全部通过 /api/chat/{id} 轮询接口自动衔接。
    - type 字段：task（首轮任务id）、stream_start、stream_end、tool_start、error。
    """
    try:
        t0 = time.monotonic()
        headers = {
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no"
        }
        if not session_id:
            session_id = str(uuid4())
            headers["Set-Session-ID"] = session_id
        qa_id = str(uuid4())
        # area：用于测试环境实时切换 API host（按 session 生效）
        from .state import get_session_meta, set_session_meta
        effective_area = None
        if request.area is not None:
            # 允许前端传空字符串表示清空/恢复默认
            effective_area = request.area.strip() or None
            set_session_meta(session_id, {"area": effective_area})
        else:
            effective_area = (get_session_meta(session_id) or {}).get("area")
        _dbg(
            f"/api/chat enter qa_id={qa_id} session_id={session_id} "
            f"content_len={len(request.content or '')} "
            f"file_ids={len(request.file_ids or [])} file_infos={len(request.file_infos or [])} "
            f"has_instructions={bool(request.instructions)} language={request.language} task_id={request.task_id} "
            f"use_advanced_model={request.use_advanced_model} enable_web_search={request.enable_web_search} area={effective_area}"
        )
        # 取session_id下的完整history，追加本轮user消息
        history = get_session_history(session_id) or []
        # 创建一个用户消息
        user_message = Message(
            role="user",
            content=request.content,
            file_ids=request.file_ids,
            file_infos=request.file_infos
        )
        # 处理消息
        processed_messages = await process_message(session_id, user_message)
        history.extend(processed_messages)
        set_session_history(session_id, history)
        # 记录 agent_task_id（优先使用前端传入的 task_id，否则回退 qa_id）
        agent_task_id = request.task_id or qa_id
        set_qa_state(f"{qa_id}:agent_task_id", agent_task_id)
        set_qa_state(f"{qa_id}:instructions", request.instructions)
        set_qa_state(f"{qa_id}:language", request.language)
        set_qa_state(f"{qa_id}:area", effective_area)
        # 存储AI生成文档的前端参数
        set_qa_state(f"{qa_id}:use_advanced_model", request.use_advanced_model)
        set_qa_state(f"{qa_id}:enable_web_search", request.enable_web_search)
        # 只调用llm_stream_generator
        _dbg(f"/api/chat start streaming qa_id={qa_id} elapsed_ms={int((time.monotonic()-t0)*1000)}")
        return StreamingResponse(
            ndjson_stream(llm_stream_generator)(qa_id, session_id, True, instructions=request.instructions, language=request.language),
            media_type="application/x-ndjson",
            headers=headers
        )
    except Exception as e:
        error_msg = str(e)
        _dbg(f"/api/chat error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"LightPDF Agent处理错误: {error_msg}")

@app.get("/api/chat/{id}")
async def chat_poll(id: str = Path(..., description="/api/chat接口返回的task id")):
    """
    轮询接口，自动衔接工具调用和LLM流式输出，支持多轮嵌套。

    状态机与type说明：
    - tool_calling：工具调用中，返回 type=tool_chunk，前端可据此显示"工具处理中"。
    - tool_call_end_ready：工具调用完成，先返回 type=tool_end（或 tool_call_end_message），如无异常则自动继续LLM流式推理。
    - finished：流程结束，返回 type=stream_end，附带 usage。
    - 任何异常均写入 finished 并输出 type=error。
    """
    try:
        async def poll_result():
            try:
                state = get_qa_state(id)
                if state:
                    session_id = state.get("session_id")
                    _dbg(f"/api/chat/{{id}} poll id={id} status={state.get('status')} session_id={session_id}")
                    if state.get("status") == "tool_call_end_ready":
                        tool_result = state.get("tool_call_end_message", {})
                        yield tool_result

                        if tool_result.get("type") == "error":
                            return

                        # 检查redis队列是否还有未处理工具调用
                        queue_key = f"qa:{id}:tool_queue"
                        next_tool_call = redis_client.lpop(queue_key)
                        if next_tool_call:
                            tc = json.loads(next_tool_call)
                            tool_name = tc["function"]["name"]
                            args = safe_json_loads(tc["function"]["arguments"])
                            
                            # === 成本检查：在返回 tool_start 之前检查是否允许 ===
                            from .tasks import check_tool_cost
                            agent_task_id = get_qa_state(f"{id}:agent_task_id") or id
                            use_advanced_model = get_qa_state(f"{id}:use_advanced_model")
                            area = get_qa_state(f"{id}:area")
                            # 汇总 pages：按 files[].path 从 session_file_pages:{session_id} 取
                            pages_total = None
                            try:
                                files = args.get("files", []) if isinstance(args, dict) else []
                                total = 0
                                hit = False
                                for f in files:
                                    if not isinstance(f, dict):
                                        continue
                                    p = f.get("path")
                                    if not p:
                                        continue
                                    v = get_session_file_pages(session_id, p)
                                    if v:
                                        total += int(v)
                                        hit = True
                                pages_total = total if hit else None
                            except Exception:
                                pages_total = None

                            # package_files：纯打包下载链接，不做成本校验
                            if tool_name != "package_files":
                                _dbg(f"cost_check(start) poll id={id} agent_task_id={agent_task_id} tool={tool_name} pages_total={pages_total}")
                                t_cost = time.monotonic()
                                cost_check_result = await check_tool_cost(
                                    agent_task_id,
                                    tool_name,
                                    args,
                                    pages=pages_total,
                                    use_advanced_model=use_advanced_model,
                                    area=area
                                )
                                _dbg(f"cost_check(end) poll id={id} tool={tool_name} allow={cost_check_result.allow} elapsed_ms={int((time.monotonic()-t_cost)*1000)}")
                                
                                if not cost_check_result.allow:
                                    # 成本检查拒绝：为当前及队列中剩余的 tool_calls 添加 tool message
                                    # 先处理当前的 tc
                                    append_session_history(session_id, {
                                        "role": "tool",
                                        "tool_call_id": tc["id"],
                                        "content": cost_check_result.message
                                    })
                                    # 处理队列中剩余的 tool_calls
                                    while True:
                                        remaining_tc = redis_client.lpop(queue_key)
                                        if not remaining_tc:
                                            break
                                        remaining_tc = json.loads(remaining_tc)
                                        append_session_history(session_id, {
                                            "role": "tool",
                                            "tool_call_id": remaining_tc["id"],
                                            "content": cost_check_result.message
                                        })
                                    set_qa_state(id, {"status": "finished", "content": cost_check_result.message, "session_id": session_id})
                                    yield cost_check_result.get_error_response(tool_name)
                                    return
                            
                            # === 成本检查通过，继续正常流程 ===
                            args.pop("files", None)
                            args.pop("latex_code", None)
                            _dbg(f"tool_start emit poll id={id} tool={tool_name}")
                            yield {
                                "type": "tool_start",
                                "content": json.dumps({
                                    "id": tc["id"],
                                    "function": {
                                        "name": tool_name,
                                        "arguments": args
                                    }
                                })
                            }

                            set_qa_state(id, {"status": "tool_calling", "tool_call_args": tc, "session_id": session_id})
                            import asyncio
                            _dbg(f"tool_task_async schedule poll id={id} tool={tool_name}")
                            asyncio.create_task(tool_task_async(id, session_id, tc))
                            return

                        instructions = get_qa_state(f"{id}:instructions")
                        language = get_qa_state(f"{id}:language")
                        # 队列已空，恢复LLM流式（允许其根据工具结果决定是否调用 package_files）
                        async for chunk in llm_stream_generator(id, session_id, False, instructions=instructions, language=language):
                            yield chunk
                    elif state.get("status") == "finished":
                        content = state.get("content", "task finished")
                        yield {
                            "type": "error",
                            "content": content
                        }
                    else:
                        yield {"type": "tool_chunk"}
                else:
                    _dbg(f"/api/chat/{{id}} poll id={id} state not found")
                    raise Exception("非法id状态")
            except Exception as e:
                _dbg(f"/api/chat/{{id}} poll exception id={id}: {str(e)}")
                set_qa_state(id, {"status": "finished", "content": f"轮询异常: {str(e)}"})
                yield {"type": "error", "content": f"轮询异常: {str(e)}"}
        return StreamingResponse(
            ndjson_stream(poll_result)(),
            media_type="application/x-ndjson"
        )
    except Exception as e:
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=f"轮询问答任务时出错: {error_msg}") 