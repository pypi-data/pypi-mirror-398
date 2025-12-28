import os
import json
import urllib.parse
from fastapi import UploadFile
import oss2
import asyncio
from typing import List, Dict, Any
import hashlib

from .models import FileInfo
from .state import store_file_info, get_session_files
from .oss_config import fetch_oss_config, get_oss_client
from .utils import safe_json_loads

MAX_BATCH_SIZE = 10  # 每批次最多处理的文件数

async def _upload_file_to_oss(file: UploadFile, oss_bucket: oss2.Bucket, object_key: str, content_type: str, oss_config: Dict[str, Any]) -> Dict[str, Any]:
    """上传单个文件到OSS
    
    Args:
        file: 要上传的文件
        oss_bucket: OSS客户端
        object_key: 对象键
        content_type: 文件类型
        oss_config: OSS配置信息，包含回调参数
        
    Returns:
        Dict[str, Any]: 上传结果，包含回调响应数据
        
    Raises:
        ValueError: 上传失败时抛出
    """
    # 分块大小 8MB（阿里云OSS推荐值）
    part_size = 8 * 1024 * 1024
    
    try:
        # 处理回调参数
        headers = {'Content-Type': content_type}
        
        # 如果配置中包含回调URL，添加回调参数
        callback_info = oss_config.get('callback', {})
        if callback_info:
            callback_dict = {}
            
            # 从配置中获取回调URL
            callback_url = callback_info.get("url")
            if callback_url:
                callback_dict['callbackUrl'] = callback_url
                callback_dict['callbackBody'] = callback_info.get("body", 
                    'bucket=${bucket}&object=${object}&size=${size}&mimeType=${mimeType}')
                callback_dict['callbackBodyType'] = callback_info.get("type", 
                    'application/x-www-form-urlencoded')
                
                # 回调参数是json格式，并且base64编码
                callback_param = json.dumps(callback_dict).strip()
                base64_callback_body = oss2.utils.b64encode_as_string(callback_param)
                
                # 处理回调变量
                filename = file.filename or "unknown_file"
                callback_var_params = {"x:filename": filename}
                callback_var_param_json = json.dumps(callback_var_params).strip()
                encoded_callback_var = oss2.utils.b64encode_as_string(callback_var_param_json)
                headers['x-oss-callback-var'] = encoded_callback_var
                
                # 回调参数编码后放在header中传给OSS
                headers['x-oss-callback'] = base64_callback_body
        
        # 初始化分块上传
        upload_id = oss_bucket.init_multipart_upload(object_key, headers=headers).upload_id
        parts = []
        
        # 分块上传
        part_number = 1
        while True:
            chunk = await file.read(part_size)
            if not chunk:
                break
                
            # 上传分块
            etag = oss_bucket.upload_part(object_key, upload_id, part_number, chunk).etag
            parts.append(oss2.models.PartInfo(part_number, etag))
            part_number += 1
        
        # 完成分块上传，使用回调参数
        result = oss_bucket.complete_multipart_upload(object_key, upload_id, parts, headers=headers)
        
        # 返回结果
        response_data = {}
        
        # 处理回调响应
        if result.status == 200:
            # 尝试解析回调响应
            try:
                response_content = result.resp.read()
                if response_content:
                    response_data = safe_json_loads(response_content.decode('utf-8'))
            except Exception:
                pass
        
        return {
            "status": result.status,
            "object_key": object_key,
            "response_data": response_data
        }
        
    except Exception as e:
        # 尝试取消上传（如果已经初始化）
        try:
            if 'upload_id' in locals():
                oss_bucket.abort_multipart_upload(object_key, upload_id)
        except Exception:
            pass
            
        # 重新抛出原始异常
        raise ValueError(f"OSS上传过程中发生错误: {str(e)}")

async def _process_single_file(file: UploadFile, oss_bucket: oss2.Bucket, oss_config: Dict[str, Any], session_id: str) -> FileInfo:
    """处理单个文件的上传
    
    Args:
        file: 要上传的文件
        oss_bucket: OSS客户端
        oss_config: OSS配置
        session_id: 会话ID
    
    Returns:
        FileInfo: 文件信息
    """
    filename = file.filename or "unknown_file"
    content_type = file.content_type or "application/octet-stream"
    resource_id = "error"
    oss_path: str = ""
    oss_url: str | None = None
    
    try:
        # 获取对象键和OSS路径
        object_key = oss_config.get("objects", {}).get(filename, "")
        # 如果API未提供对象键，使用文件名作为临时键
        if not object_key:
            # 使用文件名的哈希作为临时对象键
            hash_obj = hashlib.md5(filename.encode())
            temp_key = hash_obj.hexdigest()
            object_key = f"temp_{temp_key}"
        
        # 上传文件
        upload_result = await _upload_file_to_oss(file, oss_bucket, object_key, content_type, oss_config)
        
        # 从回调响应中提取信息
        if upload_result["status"] == 200:
            response_data = upload_result.get("response_data", {})
            if response_data and "data" in response_data:
                data = response_data["data"]
                # 提取resource_id
                if "resource_id" in data:
                    resource_id = data["resource_id"]
                
                # 回调通常会同时返回：
                # - uri: oss://...（适合多数后端任务）
                # - url: https://...（直链，适合需要直接读取字节的能力，如图片获取尺寸/生成mask）
                if isinstance(data.get("uri"), str) and data.get("uri"):
                    oss_path = data["uri"]
                if isinstance(data.get("url"), str) and data.get("url") and data["url"].startswith(("http://", "https://")):
                    oss_url = data["url"]
                # 兜底：如果没有 uri，则用 url 作为 path
                if not oss_path and oss_url:
                    oss_path = oss_url
                
                # 使用回调返回的type作为content_type
                if "type" in data:
                    content_type = data["type"]
                
                # 创建文件信息
                file_info = FileInfo(
                    file_id=resource_id,  # 使用resource_id作为文件ID
                    filename=filename,
                    content_type=content_type,
                    path=oss_path,
                    url=oss_url
                )
                
                # 存储文件信息到会话
                store_file_info(session_id, file_info)
                
                return file_info
        
        raise ValueError(f"OSS上传失败: {upload_result}")
    except Exception as e:
        # 单个文件处理失败，返回错误信息
        return FileInfo(
            file_id="error",
            filename=filename,
            content_type=content_type,
            path=f"Error: {str(e)}"
        )

async def handle_batch_file_upload(files: List[UploadFile], session_id: str) -> List[FileInfo]:
    """批量处理文件上传请求，按照每10个文件获取一次OSS配置，并并行上传
    
    Args:
        files: 要上传的文件列表
        session_id: 会话ID
        
    Returns:
        List[FileInfo]: 文件信息对象列表
    """
    results = []
    total_files = len(files)
    
    # 按照每MAX_BATCH_SIZE个文件分组处理
    for i in range(0, total_files, MAX_BATCH_SIZE):
        batch = files[i:i+MAX_BATCH_SIZE]
        
        # 获取所有文件名
        filenames = [f.filename or f"unknown_file_{j}" for j, f in enumerate(batch)]
        
        try:
            # 为这批文件获取OSS配置
            oss_config = await fetch_oss_config(filenames)
            
            # 获取OSS客户端
            oss_bucket = await get_oss_client(oss_config)
            
            # 并行处理文件上传
            tasks = [_process_single_file(file, oss_bucket, oss_config, session_id) for file in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=False)
            
            # 添加到结果列表
            results.extend(batch_results)
        except Exception as e:
            # 整批文件处理失败
            for file in batch:
                filename = file.filename or "unknown_file"
                results.append(FileInfo(
                    file_id="error",
                    filename=filename,
                    content_type=file.content_type or "application/octet-stream",
                    path=f"Error: OSS配置获取失败 - {str(e)}"
                ))
    
    return results

def get_file_references(file_ids: list[str], session_id: str) -> List[Dict[str, str]]:
    """获取文件引用链接
    
    Args:
        file_ids: 文件ID列表
        session_id: 会话ID
        
    Returns:
        List[Dict[str, str]]: 文件信息列表，JSON格式
    """
    file_urls = []
    session_files = get_session_files(session_id)
    
    for file_id in file_ids:
        if file_id in session_files:
            file_info = session_files[file_id]
            # 提取文件路径和密码(如果有)
            path = file_info.path
            # 创建与get_file_info_json相同结构的数据
            file_data = {
                "path": path,
                "name": file_info.filename
            }
            # 如果文件信息中包含密码，添加到结果中
            if hasattr(file_info, 'password') and file_info.password:
                file_data["password"] = file_info.password
            
            file_urls.append(file_data)
    
    return file_urls 