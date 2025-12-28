from dataclasses import dataclass
import json
import asyncio
import sys
from typing import List, Dict, AsyncGenerator, Any, Tuple, TypedDict, Optional
import urllib.parse
import os
import logging

from .state import get_openai_client, get_user_session, create_user_session, update_user_session, get_mcp_session, redis_client
from .models import Message
from .file_handler import get_file_references
from .tools import get_tools, format_tool_response, process_tool_path
from .utils import validate_and_fix_messages, extract_response_content, safe_json_loads
from .config import Config

# 设置日志记录器
logger = logging.getLogger(__name__)

def _dbg(msg: str):
    v = (os.getenv("DEBUG") or "").strip().lower()
    if v not in {"1", "true", "yes", "y", "on"}:
        return
    try:
        print(f"[backend][chat_handler] {msg}", file=sys.stderr, flush=True)
    except Exception:
        pass

# 类型定义
@dataclass
class ToolCallFunction:
    """工具调用函数类型"""
    name: str
    arguments: str

@dataclass
class ToolCall:
    """工具调用类型"""
    id: str
    function: ToolCallFunction

class ToolResponseContent(TypedDict, total=False):
    """工具响应内容类型"""
    content: Optional[str]
    text: Optional[str]
    markdown: Optional[str]
    result: Optional[Dict[str, Any]]

class YieldMessage(TypedDict, total=False):
    """消息响应类型"""
    type: str
    step_type: Optional[str]
    content: str

class ToolResponseMessage(TypedDict):
    """工具响应消息类型"""
    role: str
    tool_call_id: str
    name: str
    content: str

LANGUAGE_CODE_TO_ENGLISH = {
    "en": "English",
    "zh": "Simplified Chinese",
    "tw": "Traditional Chinese",
    "pt": "Portuguese",
    "es": "Spanish",
    "it": "Italian",
    "fr": "French",
    "ja": "Japanese",
    "nl": "Dutch",
    "de": "German",
    "el": "Greek",
    "cs": "Czech",
    "pl": "Polish",
    "hu": "Hungarian",
    "tr": "Turkish",
    "fi": "Finnish",
    "da": "Danish",
    "no": "Norwegian",
    "sv": "Swedish",
    "sl": "Slovenian",
    "ar": "Arabic",
    "ko": "Korean",
}

def create_error_response(tool_call_id: str, tool_name: str, error_msg: str) -> Tuple[ToolResponseMessage, YieldMessage]:
    """创建错误响应
    
    Args:
        tool_call_id: 工具调用ID
        tool_name: 工具名称
        error_msg: 错误信息
        
    Returns:
        Tuple[ToolResponseMessage, YieldMessage]: 工具响应消息和前端显示消息
    """
    # API消息使用原始错误内容
    tool_response_message = {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": tool_name,
        "content": f"Error: {error_msg}"
    }
    
    # 前端显示使用格式化的错误摘要
    error_response = json.dumps({
        "isError": True,
        "content": [{"type": "text", "text": f"工具 {tool_name} 调用失败：{error_msg}", "annotations": None}]
    })
    
    yield_message = {
        "type": "error",
        "content": error_response
    }
    
    return tool_response_message, yield_message

async def handle_tool_call(tool_call: ToolCall, api_messages: List[Dict], session_id: Optional[str] = None) -> Tuple[ToolResponseMessage, YieldMessage]:
    """处理单个工具调用
    
    Args:
        tool_call: 工具调用对象
        api_messages: API消息列表
    
    Returns:
        Tuple[ToolResponseMessage, YieldMessage]: 工具响应消息和yield消息
    """
    tool_name = tool_call.function.name
    
    try:
        tool_args = safe_json_loads(tool_call.function.arguments)
        tool_args = await process_tool_path(tool_args, session_id=session_id)

        # 1. 调用工具并获取响应
        mcp_session = get_mcp_session()
        # area 仅用于成本检查（backend 侧）；工具调用不做 area 路由
        if isinstance(tool_args, dict):
            # 打印调用前实际传给 MCP 的地址（仅 DEBUG）
            try:
                file_path = tool_args.get("file_path")
                files = tool_args.get("files")
                paths = []
                if isinstance(file_path, str) and file_path:
                    paths.append(file_path)
                if isinstance(files, list):
                    for f in files:
                        if isinstance(f, dict) and isinstance(f.get("path"), str) and f.get("path"):
                            paths.append(f.get("path"))
                if paths:
                    _dbg(f"call_tool tool={tool_name} resolved_paths={paths}")
            except Exception:
                pass
        tool_response = await mcp_session.call_tool(tool_name, tool_args if tool_args else None)
        
        # 获取原始响应内容用于API消息
        original_response = tool_response.model_dump()
        
        # 获取格式化后的摘要用于前端显示
        formatted_response = format_tool_response(original_response)
        
        # 2. 解析格式化后的JSON响应并创建消息
        try:
            response_obj = json.loads(formatted_response)
            is_error = response_obj.get("isError", False)
            
            # 在 text 对象中添加 function 字段
            if response_obj.get("content") and isinstance(response_obj["content"], list):
                for item in response_obj["content"]:
                    if item.get("type") == "text" and isinstance(item.get("text"), dict):
                        item["text"]["function"] = {
                            "id": tool_call.id,
                            "name": tool_name,
                            "arguments": tool_args.get("format")
                        }

                        if session_id:
                            queue_key = f"qa:{session_id}:tool_result"
                            success_files = item["text"].get("success_files", [])
                            if success_files:
                                for file in success_files:
                                    file_url = file.get("download_url")
                                    if file_url:
                                        redis_client.rpush(queue_key, file_url)
                                        redis_client.expire(queue_key, 3600)
            
            # 3. 使用辅助函数提取响应内容
            response_content = extract_response_content(original_response)
            
            # 4. 创建响应消息
            tool_response_message: ToolResponseMessage = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": response_content
            }
            
            # 前端显示使用格式化的摘要
            yield_message: YieldMessage = {
                "type": "tool_end" if not is_error else "error",
                "content": json.dumps(response_obj, ensure_ascii=False)
            }
            
        except json.JSONDecodeError:
            # 如果无法解析为JSON，保留原始格式
            tool_response_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": original_response.get('content', json.dumps(original_response, ensure_ascii=False))
            }
            
            yield_message = {
                "type": "tool_end",
                "content": formatted_response
            }
        
    except Exception as e:
        # 5. 使用辅助函数创建错误响应
        error_msg = str(e)
        tool_response_message, yield_message = create_error_response(tool_call.id, tool_name, error_msg)
    
    return tool_response_message, yield_message

def calculate_token_price(model_name: str, prompt_tokens: int, completion_tokens: int) -> Dict[str, str]:
    """计算token价格
    
    Args:
        model_name: 模型名称
        prompt_tokens: 输入token数量
        completion_tokens: 输出token数量
        
    Returns:
        Dict[str, str]: 价格信息
    """
    # 获取模型价格配置
    prices = Config.get_model_price(model_name)
    
    # 计算价格
    input_price = (prompt_tokens * prices['input']) / prices['divisor']
    output_price = (completion_tokens * prices['output']) / prices['divisor']
    total_price = input_price + output_price
    
    return {
        'input_price': f"{input_price:.6f}",
        'output_price': f"{output_price:.6f}",
        'total_price': f"{total_price:.6f}",
        'currency': prices['currency']
    }

async def collect_stream_content(response: Any) -> AsyncGenerator[Dict, Tuple[str, str, List[Dict], Any]]:
    """收集流式响应内容
    
    Args:
        response: OpenAI流式响应对象
    
    Yields:
        Dict: 处理后的消息
        
    Returns:
        Tuple[str, str, List[Dict], Any]: 完整内容、完成原因、工具调用数据和usage信息
    """
    full_content = ""
    finish_reason = None
    tool_calls_data = []
    usage_info = None
    
    # 使用异步方式处理流
    try:
        # 迭代处理流
        last_chunk = None
        
        async for chunk in response:
            last_chunk = chunk  # 保存最后一个chunk，因为usage信息可能在最后
            
            # 检查usage属性
            if hasattr(chunk, 'usage') and chunk.usage:
                usage_info = chunk.usage
            
            # 检查chunk是否有choices，防止索引错误
            if not hasattr(chunk, 'choices') or not chunk.choices:
                continue
            
            # 安全获取第一个choice
            try:
                choice = chunk.choices[0]
            except IndexError:
                continue
            
            # 检查choice的finish_reason
            if hasattr(choice, 'finish_reason') and choice.finish_reason:
                finish_reason = choice.finish_reason
            
            # 如果没有delta属性，跳过
            if not hasattr(choice, 'delta'):
                continue
            
            delta = choice.delta
            
            # 处理内容
            if delta.content:
                content_piece = delta.content
                full_content += content_piece
                
                # 发送流式块
                try:
                    yield {
                        "type": "stream_chunk",
                        "content": content_piece
                    }
                except ConnectionError:
                    print("客户端连接已关闭，停止流式传输")
                    break
                except Exception as e:
                    print(f"流式传输时出错: {str(e)}")
                    break
            
            # 处理工具调用
            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    tc_index = tool_call_delta.index
                    while len(tool_calls_data) <= (tc_index or 0):
                        tool_calls_data.append({"id": None, "type": "function", "function": {"name": "", "arguments": ""}})
                    
                    tc_data = tool_calls_data[tc_index]
                    if tool_call_delta.id:
                        tc_data.update({"id": tool_call_delta.id})
                    
                    tc_function = tool_call_delta.function
                    if tc_function:
                        current_tool = tc_data["function"]
                        if tc_function.name:
                            current_tool["name"] = tc_function.name
                        if tc_function.arguments:
                            args_content = tc_function.arguments
                            current_tool["arguments"] = current_tool.get("arguments", "") + args_content
        
        # 检查最后一个chunk是否包含usage信息
        if not usage_info and last_chunk and hasattr(last_chunk, 'usage') and last_chunk.usage:
            usage_info = last_chunk.usage
        
        # 如果没有获取到usage信息，不再进行估算
        if usage_info:
            price_info = calculate_token_price(
                Config.OPENAI_MODEL,
                usage_info.prompt_tokens,
                usage_info.completion_tokens
            )
            
            # 将价格信息添加到usage中
            usage_info = {
                'prompt_tokens': usage_info.prompt_tokens,
                'completion_tokens': usage_info.completion_tokens,
                'total_tokens': usage_info.total_tokens,
                'price_info': price_info
            }
                
    except ConnectionError as e:
        print(f"处理流时连接错误: {str(e)}")
    except Exception as e:
        print(f"处理流式响应时出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    # 确保即使在异常情况下也能发送完整内容
    try:
        yield (full_content, finish_reason, tool_calls_data, usage_info)
    except ConnectionError:
        print("客户端连接已关闭，无法发送最终响应")
    except Exception as e:
        print(f"发送最终响应时出错: {str(e)}")

async def process_messages(session_id: str, messages: List[Message]) -> List[Dict]:
    """处理消息列表，包括文件处理和格式转换
    
    Args:
        session_id: 用户会话ID
        messages: 消息列表
        
    Returns:
        List[Dict]: 处理后的消息列表
    """
    # 获取或创建用户会话
    session = get_user_session(session_id)
    if not session:
        session = create_user_session(session_id)
    
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
    
    # 处理新消息
    for msg in messages:
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
                continue
        
        # 如果消息包含文件ID
        if msg.file_ids:
            file_urls = get_file_references(msg.file_ids, session_id)
            message_dict = add_file_links_to_message(message_dict, file_urls)
        
        # 如果消息包含直接的文件信息
        if msg.file_infos:
            file_urls = get_file_info_json(msg.file_infos)
            message_dict = add_file_links_to_message(message_dict, file_urls)
        
        processed_messages.append(message_dict)
    
    # 更新会话消息
    if session.messages:
        session.messages.extend(processed_messages)
    else:
        session.messages = processed_messages
    
    # 限制消息历史长度
    MAX_MESSAGES = 50  # 增加消息历史长度以保留工具调用上下文
    if len(session.messages) > MAX_MESSAGES:
        session.messages = session.messages[-MAX_MESSAGES:]
    
    # 更新会话
    update_user_session(session_id, session.messages)
    
    # 返回完整的会话历史
    return validate_and_fix_messages(session.messages)

async def generate_chat_response(session_id: str, messages: List[Dict], instructions: Optional[str] = None, language: Optional[str] = None) -> AsyncGenerator:
    """生成聊天响应
    
    Args:
        session_id: 用户会话ID
        messages: 处理后的消息列表
        instructions: 可选的系统提示词
        
    Yields:
        Dict: 响应内容
    """
    openai_client = get_openai_client()
    
    try:
        tools = await get_tools()
        api_messages = messages.copy()
        
        # 完全依赖流式响应
        while True:
            # 使用流式请求 - 异步客户端
            from openai.types.chat import ChatCompletionStreamOptionsParam
            
            # 准备发送给API的消息
            request_messages = api_messages.copy()
            
            # 获取指令：优先使用前端传递的指令，否则使用配置文件中的默认指令
            if not instructions:
                instructions = Config.get_default_instructions() or ""

            if language:
                language_instruction = f"- If the user does not specify a language, respond in {LANGUAGE_CODE_TO_ENGLISH.get(language, f"{language} language")}."
                instructions = f"{instructions}\n{language_instruction}" if instructions else language_instruction
            
            # 如果有指令则添加系统提示词
            if instructions:
                request_messages.insert(0, {"role": "system", "content": instructions})
            
            response = await openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=request_messages,
                tools=tools,
                parallel_tool_calls=False,
                stream=True,
                stream_options=ChatCompletionStreamOptionsParam(include_usage=True)  # 使用类型化对象
            )
            
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
                else:
                    if not yield_content:
                        # 第一次消息通知
                        yield {
                            "type": "stream_start",
                            "content": ""
                        }
                        yield_content = True
                    
                    yield item
            
            # 如果需要调用工具
            if finish_reason == 'tool_calls' and tool_calls_data:
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
                        tool_calls.append(type('ToolCall', (), {
                            'id': tc_data["id"],
                            'function': type('Function', (), {
                                'name': tc_function["name"],
                                'arguments': tc_function["arguments"]
                            })
                        }))
                
                # 创建助手消息
                assistant_message = {
                    "role": "assistant",
                    "content": full_content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in tool_calls
                    ]
                }
                
                # 准备API消息列表 - 不包含系统提示词
                api_messages.append(assistant_message)
                
                # 处理每个工具调用
                for tool_call in tool_calls:
                    # 发送工具调用信息
                    yield {
                        "type": "tool_call",
                        "step_type": "start",
                        "content": json.dumps({
                            "id": tool_call.id,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": safe_json_loads(tool_call.function.arguments)
                            }
                        })
                    }
                    
                    # 处理工具调用
                    tool_response_message, yield_message = await handle_tool_call(tool_call, api_messages)
                    api_messages.append(tool_response_message)
                    yield yield_message
                
                # 更新会话历史，过滤掉系统提示词
                update_user_session(session_id, api_messages)
                
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
                api_messages.append({
                    "role": "assistant",
                    "content": full_content
                })
                
                # 保存会话
                update_user_session(session_id, api_messages)

                break

    except Exception as e:
        yield {
            "type": "error",
            "content": str(e)
        } 