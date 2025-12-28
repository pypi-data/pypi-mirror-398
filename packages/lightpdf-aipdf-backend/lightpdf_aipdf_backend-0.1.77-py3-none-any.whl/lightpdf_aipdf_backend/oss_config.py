import oss2
import httpx
import json
from typing import Dict, Any, List
from .config import Config

async def fetch_oss_config(filenames: List[str]) -> Dict[str, Any]:
    """从API获取OSS配置，每次都重新获取
    
    Args:
        filenames: 要上传的文件名列表，最多10个
    
    Returns:
        Dict[str, Any]: OSS配置信息，直接返回API接口返回的数据
    
    Raises:
        ValueError: 如果API请求失败或文件名超过10个
    """
    # 检查文件名数量
    if len(filenames) > 10:
        raise ValueError("一次最多只能获取10个文件的配置")
        
    # API配置
    OSS_AUTH_URL = Config.get_api_url("/authorizations/oss")
    TASK_TYPE = "104"  # 任务类型

    # 准备请求数据
    headers = {}
    params = {
        "task_type": TASK_TYPE,
        "filenames": json.dumps(filenames)
    }
    
    # 发送请求
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                OSS_AUTH_URL,
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                raise ValueError(f"OSS authorization API failed with status {response.status_code}: {response.text}")
            
            result = response.json()
            if result.get("status") != 200:
                raise ValueError(f"OSS authorization API returned error: {result.get('message')}")
            
            # 直接返回API返回的data部分
            data = result.get("data", {})
            
            return data
    except Exception as e:
        raise ValueError(f"Failed to fetch OSS configuration: {str(e)}")

async def get_oss_client(config: Dict[str, Any]) -> oss2.Bucket:
    """获取OSS客户端
    
    Args:
        config: OSS配置信息
        
    Returns:
        oss2.Bucket: OSS客户端
        
    Raises:
        ValueError: 如果配置信息不完整
    """
    try:
        # 获取认证信息
        credential = config.get("credential", {})
        
        # 创建认证对象
        auth = oss2.StsAuth(
            credential.get("access_key_id"),
            credential.get("access_key_secret"),
            credential.get("security_token")
        )
        
        # 创建Bucket对象
        bucket = oss2.Bucket(
            auth,
            f"https://{config.get('endpoint')}",
            config.get("bucket")
        )
        
        return bucket
    except KeyError as e:
        raise ValueError(f"OSS configuration is incomplete: missing {str(e)}")
