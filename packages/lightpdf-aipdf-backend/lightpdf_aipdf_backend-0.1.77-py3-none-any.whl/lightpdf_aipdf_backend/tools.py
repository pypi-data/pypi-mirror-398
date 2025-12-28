import os
import json
from typing import List, Dict, Any
from fastapi import HTTPException

from .state import get_mcp_session, get_session_file_url
from .utils import extract_response_content, safe_json_loads

def _dbg(msg: str):
    v = (os.getenv("DEBUG") or "").strip().lower()
    if v not in {"1", "true", "yes", "y", "on"}:
        return
    try:
        import sys
        print(f"[backend][tools] {msg}", file=sys.stderr, flush=True)
    except Exception:
        pass

async def get_tools() -> List[Dict]:
    """从MCP client获取工具列表
    
    Returns:
        List[Dict]: 工具列表
        
    Raises:
        HTTPException: MCP会话未初始化时抛出
    """
    mcp_session = get_mcp_session()
    if not mcp_session:
        raise HTTPException(status_code=500, detail="MCP session not initialized")
    
    tools_result = await mcp_session.list_tools()
    tools = []
    
    for tool in tools_result.tools:
        tool_dict = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        }
        tools.append(tool_dict)
    return tools

def format_tool_response(response_dict: Dict[str, Any]) -> str:
    """格式化工具响应，提取可能包含的Markdown内容
    
    Args:
        response_dict: 工具响应字典
        
    Returns:
        str: 格式化后的响应
    """
    # 准备结果JSON对象
    result = {"isError": False, "content": []}
    
    # 使用辅助函数提取内容
    content_text = extract_response_content(response_dict)
    
    # 首先尝试处理已知的JSON格式内容
    if isinstance(content_text, str):
        try:
            # 检查是否是JSON字符串
            if content_text.strip().startswith(('{', '[')):
                json_content = json.loads(content_text)
                # 处理特定格式的JSON对象
                if isinstance(json_content, dict) and 'content' in json_content:
                    result["content"] = json_content["content"]
                    result["isError"] = json_content.get("isError", False)
                    return json.dumps(result, ensure_ascii=False)
        except json.JSONDecodeError:
            # JSON解析失败，继续处理为普通文本
            pass
    
    # 处理不同类型的内容
    if isinstance(content_text, list):
        # 列表类型：处理列表中的每一项
        processed_content = []
        for item in content_text:
            if isinstance(item, dict) and "text" in item:
                # 对于包含text字段的字典，保留完整内容
                processed_content.append({
                    "type": item.get("type", "text"),
                    "text": safe_json_loads(item["text"]),
                    "annotations": item.get("annotations")
                })
            else:
                # 对于其他项，直接添加
                processed_content.append(item)
        result["content"] = processed_content
    elif isinstance(content_text, str):
        # 字符串类型
        result["content"] = [{"type": "text", "text": safe_json_loads(content_text), "annotations": None}]
    else:
        # 其他类型
        result["content"] = [{"type": "text", "text": content_text, "annotations": None}]
    
    return json.dumps(result, ensure_ascii=False)

async def process_tool_path(tool_args: Dict, *, session_id: str | None = None) -> Dict:
    """处理工具调用参数中的文件路径
    
    Args:
        tool_args: 工具调用参数
        
    Returns:
        Dict: 处理后的参数
    """
    # 如果前端提供了 file_infos.path(oss://) 对应的直链 url，这里在调用工具前做一次兜底替换：
    # - 避免某些能力不支持 oss:// 但支持 http(s) 直链
    if session_id and isinstance(tool_args, dict):
        # 1) files: [{path, ...}]
        files = tool_args.get("files")
        if isinstance(files, list):
            for f in files:
                if not isinstance(f, dict):
                    continue
                p = f.get("path")
                if not (isinstance(p, str) and p):
                    continue
                # 仅对非 http(s) 的 path 做替换尝试（典型为 oss://...）
                if p.startswith(("http://", "https://")):
                    continue
                u = get_session_file_url(session_id, p)
                if u:
                    f["path"] = u
                    _dbg(f"resolved files[].path from {p} -> {u}")
                elif p.startswith(("oss://", "oss_id://")):
                    _dbg(f"no mapping for files[].path={p}")

        # 2) file_path: "oss://..."
        fp = tool_args.get("file_path")
        if isinstance(fp, str) and fp and not fp.startswith(("http://", "https://")):
            u = get_session_file_url(session_id, fp)
            if u:
                tool_args["file_path"] = u
                _dbg(f"resolved file_path from {fp} -> {u}")
            elif fp.startswith(("oss://", "oss_id://")):
                _dbg(f"no mapping for file_path={fp}")

    if 'file_path' in tool_args and tool_args['file_path']:
        file_path = tool_args['file_path']
        
        # 检查是否为OSS路径或URL，如果是则使用原始路径
        if file_path.startswith("oss_id://") or file_path.startswith(("http://", "https://", "oss://")):
            return tool_args
        
        # 非OSS路径的处理
        print(f"警告: 文件路径不是OSS格式: {file_path}")
    
    return tool_args 