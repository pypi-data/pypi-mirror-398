import json
from typing import Dict, List, AsyncGenerator, Any

def validate_and_fix_messages(messages: List[Dict]) -> List[Dict]:
    """验证并修复消息格式，确保工具调用和响应的匹配
    
    Args:
        messages: 消息列表
        
    Returns:
        List[Dict]: 修复后的消息列表
    """
    if not messages:
        return []
    
    fixed_messages = []
    tool_call_ids = {}  # 用于跟踪工具调用ID及其对应的工具名称
    
    for msg in messages:
        # 检查assistant角色的工具调用
        if msg["role"] == "assistant" and "tool_calls" in msg:
            # 存储工具调用ID和对应的工具名称
            for tool_call in msg["tool_calls"]:
                tool_call_ids[tool_call["id"]] = tool_call["function"]["name"]
        
        # 处理tool角色的响应，确保有对应的tool_call_id和name
        if msg["role"] == "tool":
            if "tool_call_id" not in msg or not msg["tool_call_id"]:
                continue
                
            if "name" not in msg or not msg["name"]:
                # 如果能找到对应的工具调用，自动填充name
                if msg["tool_call_id"] in tool_call_ids:
                    msg["name"] = tool_call_ids[msg["tool_call_id"]]
                else:
                    continue
        
        fixed_messages.append(msg)
    
    return fixed_messages

def extract_response_content(response_dict: Dict[str, Any]) -> str:
    """从工具响应中提取有效内容
    
    Args:
        response_dict: 工具响应字典
        
    Returns:
        str: 提取的内容
    """
    # 如果有 content 字段，优先使用它
    if 'content' in response_dict:
        return response_dict['content']
    # 如果有 text 字段，使用它
    elif 'text' in response_dict:
        return response_dict['text']
    # 如果有结果字段，检查是否包含Markdown或文本内容
    elif 'result' in response_dict and isinstance(response_dict['result'], dict):
        result_data = response_dict['result']
        if 'markdown' in result_data:
            return result_data['markdown']
        elif 'text' in result_data:
            return result_data['text']
        elif 'content' in result_data:
            return result_data['content']
    
    # 如果没有提取到内容，返回序列化的完整响应
    return json.dumps(response_dict, ensure_ascii=False)

async def async_generator_to_json_stream(generator: AsyncGenerator) -> AsyncGenerator:
    """将异步生成器转换为JSON流
    
    Args:
        generator: 异步生成器
        
    Yields:
        bytes: JSON流
    """
    async for item in generator:
        yield json.dumps(item, ensure_ascii=False).encode('utf-8') + b'\n'

def safe_json_loads(s):
    """安全解析JSON字符串，失败时返回原文"""
    try:
        return json.loads(s or "{}")
    except Exception:
        return s 