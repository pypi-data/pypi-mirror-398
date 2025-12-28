from typing import List, Optional, Dict
from pydantic import BaseModel, field_validator

class FileInfoSimple(BaseModel):
    """简化的文件信息模型，用于直接引用不上传的文件"""
    filename: str
    path: str
    password: Optional[str] = None
    url: Optional[str] = None
    # 可选：PDF页数（由前端提供，用于成本检查等业务逻辑；不参与MCP工具参数）
    pages: Optional[int] = None

class FileInfo(FileInfoSimple):
    """文件信息模型"""
    file_id: str
    content_type: str

class Message(BaseModel):
    """聊天消息模型"""
    role: str
    content: str
    file_ids: Optional[List[str]] = None
    file_infos: Optional[List[FileInfoSimple]] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

class ChatRequest(BaseModel):
    """聊天请求模型"""
    content: str
    task_id: Optional[str] = None
    file_ids: Optional[List[str]] = None
    file_infos: Optional[List[FileInfoSimple]] = None
    instructions: Optional[str] = None
    language: Optional[str] = None
    area: Optional[str] = None
    # AI生成PDF/Word/Excel 前端直接设置的参数
    use_advanced_model: Optional[bool] = None  # 是否使用高级模型
    enable_web_search: Optional[bool] = None   # 是否启用联网搜索
    
    @field_validator('language', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """空字符串视为 None"""
        if v == '':
            return None
        return v