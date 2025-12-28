import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # 中台 API（MCP 工具调用使用）
    API_ENDPOINT = os.getenv("API_ENDPOINT", "aw.aoscdn.com/tech")
    
    # LightPDF 业务 API（成本控制等业务逻辑使用）
    LIGHTPDF_API_ENDPOINT = os.getenv("LIGHTPDF_API_ENDPOINT", "aw.aoscdn.com/app/lightpdf/v2")
    LIGHTPDF_API_TOKEN = os.getenv("LIGHTPDF_API_TOKEN", "")  # API 认证 Token
    LIGHTPDF_PRODUCT_ID = int(os.getenv("LIGHTPDF_PRODUCT_ID", "227"))  # 产品ID
    
    @classmethod
    def get_api_url(cls, path: str = "") -> str:
        """获取中台 API 的完整 URL"""
        endpoint = cls.API_ENDPOINT.rstrip("/")
        if not endpoint.startswith("http"):
            endpoint = f"https://{endpoint}"
        return f"{endpoint}{path}"

    @classmethod
    def _apply_area_host(cls, endpoint: str, area: str | None) -> str:
        """
        在测试环境中按 area 动态切换 host：
        - 默认：devaw.aoscdn.com / aw.aoscdn.com
        - area == "hk"：devgw.aoscdn.com / gw.aoscdn.com
        """
        if not endpoint or area != "hk":
            return endpoint
        out = endpoint
        # 测试环境
        out = out.replace("devaw.aoscdn.com", "devgw.aoscdn.com")
        # 生产/预发（如果存在）
        out = out.replace("aw.aoscdn.com", "gw.aoscdn.com")
        return out

    @classmethod
    def get_api_url_for_area(cls, path: str = "", area: str | None = None) -> str:
        """获取中台 API 的完整 URL（按 area 动态选择 endpoint）"""
        endpoint = cls._apply_area_host(cls.API_ENDPOINT, area).rstrip("/")
        if not endpoint.startswith("http"):
            endpoint = f"https://{endpoint}"
        return f"{endpoint}{path}"
    
    @classmethod
    def get_lightpdf_api_url(cls, path: str = "") -> str:
        """获取 LightPDF 业务 API 的完整 URL"""
        if not cls.LIGHTPDF_API_ENDPOINT:
            return ""
        endpoint = cls.LIGHTPDF_API_ENDPOINT.rstrip("/")
        if not endpoint.startswith("http"):
            endpoint = f"https://{endpoint}"
        return f"{endpoint}{path}"

    @classmethod
    def get_lightpdf_api_url_for_area(cls, path: str = "", area: str | None = None) -> str:
        """获取 LightPDF 业务 API 的完整 URL（按 area 动态选择 endpoint）"""
        if not cls.LIGHTPDF_API_ENDPOINT:
            return ""
        endpoint = cls._apply_area_host(cls.LIGHTPDF_API_ENDPOINT, area).rstrip("/")
        if not endpoint.startswith("http"):
            endpoint = f"https://{endpoint}"
        return f"{endpoint}{path}"
    
    # 模型价格配置
    MODEL_PRICES: Dict[str, Dict[str, Any]] = {
        'gpt-4o-mini': {
            'input': 0.150,    # 输入价格
            'output': 0.600,   # 输出价格
            'cached': 0.075,   # 缓存价格
            'currency': '$',    # 美元
            'divisor': 1000000  # 每百万token
        },
        'gpt-4.1-nano': {
            'input': 0.10,     # 输入价格
            'output': 0.40,    # 输出价格
            'cached': 0.025,   # 缓存价格
            'currency': '$',    # 美元
            'divisor': 1000000  # 每百万token
        },
        'gpt-4.1-mini': {
            'input': 0.40,     # 输入价格
            'output': 1.60,    # 输出价格
            'cached': 0.10,   # 缓存价格
            'currency': '$',    # 美元
            'divisor': 1000000  # 每百万token
        },
        'qwen-max': {
            'input': 0.0024,   # 输入价格
            'output': 0.0096,  # 输出价格
            'currency': '¥',    # 人民币
            'divisor': 1000     # 每千token
        },
        'qwen-plus': {
            'input': 0.0008,   # 输入价格
            'output': 0.002,   # 输出价格
            'currency': '¥',    # 人民币
            'divisor': 1000     # 每千token
        },
        'qwen-turbo': {
            'input': 0.0003,   # 输入价格
            'output': 0.0006,  # 输出价格
            'currency': '¥',    # 人民币
            'divisor': 1000     # 每千token
        },
        'qwen-long': {
            'input': 0.0005,   # 输入价格
            'output': 0.002,   # 输出价格
            'currency': '¥',    # 人民币
            'divisor': 1000     # 每千token
        }
    }
    
    @classmethod
    def validate(cls):
        """验证关键配置项"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("Missing OpenAI API Key")
            
    @classmethod
    def get_model_price(cls, model_name: str) -> Dict[str, Any]:
        """获取指定模型的价格配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 价格配置信息
        """
        return cls.MODEL_PRICES.get(model_name, cls.MODEL_PRICES['gpt-4o-mini'])
        
    @classmethod
    def get_default_instructions(cls) -> str:
        """从配置文件读取默认指令
        
        Returns:
            str: 默认指令内容，如果文件不存在或读取失败则返回空字符串
        """
        try:
            if os.path.exists(".instructions"):
                with open(".instructions", 'r', encoding='utf-8') as f:
                    return f.read().strip()
            return ""
        except Exception as e:
            print(f"读取默认指令文件失败: {str(e)}")
            return ""