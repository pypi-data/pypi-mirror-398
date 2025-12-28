import json
import httpx
import os
import sys
import time
from typing import Optional, List
from dataclasses import dataclass
from .state import set_qa_state, get_qa_state
from .config import Config
# debug helper (only when DEBUG=1/true/yes/on)
def _debug_enabled() -> bool:
    v = (os.getenv("DEBUG") or "").strip().lower()
    return v in {"1", "true", "yes", "y", "on"}


def _dbg(msg: str):
    if not _debug_enabled():
        return
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[backend][{ts}] {msg}", file=sys.stderr, flush=True)


# 默认类型（用于未映射场景）
DEFAULT_TOOL_TYPE = 0
DEFAULT_CONVERT_TYPE = 0

# 工具名称到任务类型的映射（除 convert_document 外的固定值）
# 参考：01、轻闪PDF-接入&常量说明.md
TOOL_TYPE_MAP = {
    # OCR 识别
    "ocr_document": 20,

    # 文档翻译
    "translate_pdf": 54,

    # ChatPDF / 摘要
    "summarize_document": 100,  # embedding

    # AI 生成（AIPDF）
    "create_pdf": 28,
    "create_word": 28,
    "create_excel": 28,

    # PDF 工具集
    "protect_pdf": 60,
    "unlock_pdf": 61,
    "merge_pdfs": 62,
    "split_pdf": 63,
    "compress_pdf": 64,
    "rotate_pdf": 65,
    "extract_images": 66,
    "add_text_watermark": 69,
    "add_image_watermark": 69,
    "remove_margin": 71,  # crop
    "delete_pdf_pages": 72,
    "restrict_printing": 60,  # protect 相关

    # 特殊格式处理
    "remove_watermark": 18,  # doc-repair
    "flatten_pdf": 36,
    "add_page_numbers": 37,  # number-pdf
    "resize_pdf": 38,
    "repair_pdf": 39,
    "curve_pdf": 41,
    "double_layer_pdf": 42,
    "replace_text": 43,
    "extract_pdf_tables": 44,

    # 图片处理（按最新映射表）
    # ExternalWatermark（图片去水印/去Logo）
    "remove_image_watermark": 94,
    "remove_image_logo": 98,
    # remove-sticker（图片去贴纸）
    "remove_image_sticker": 96,
    # TextRemover（图片文字去除）
    "remove_image_text": 97,
}

# 转换任务映射表 (source_ext, target_ext) -> type
CONVERT_TYPE_MAP = {
    # PDF -> others
    ("pdf", "docx"): 1, ("pdf", "doc"): 1,
    ("pdf", "xlsx"): 2, ("pdf", "xls"): 2,
    ("pdf", "pptx"): 3, ("pdf", "ppt"): 3,
    ("pdf", "jpg"): 4, ("pdf", "jpeg"): 4, ("pdf", "png"): 4, ("pdf", "gif"): 4, ("pdf", "bmp"): 4, ("pdf", "wmf"): 4, ("pdf", "emf"): 4,
    ("pdf", "html"): 5,
    ("pdf", "txt"): 6,
    ("pdf", "epub"): 7,
    ("pdf", "md"): 51,
    ("pdf", "rtf"): 78,
    ("pdf", "svg"): 82,
    ("pdf", "tiff"): 83, ("pdf", "tif"): 83,
    ("pdf", "csv"): 84,
    ("pdf", "azw3"): 85,
    ("pdf", "pdfa"): 8, ("pdf", "pdf/a"): 8,
    ("pdf", "odt"): 88,

    # -> PDF
    ("doc", "pdf"): 10, ("docx", "pdf"): 10,
    ("xls", "pdf"): 11, ("xlsx", "pdf"): 11,
    ("ppt", "pdf"): 12, ("pptx", "pdf"): 12,
    ("jpg", "pdf"): 13, ("jpeg", "pdf"): 13, ("png", "pdf"): 13, ("gif", "pdf"): 13, ("bmp", "pdf"): 13, ("webp", "pdf"): 13, ("heic", "pdf"): 13,
    ("dwg", "pdf"): 14, ("dxf", "pdf"): 14,
    ("epub", "pdf"): 16,
    ("mobi", "pdf"): 17,
    ("ofd", "pdf"): 19,
    ("caj", "pdf"): 25,
    ("md", "pdf"): 52,
    ("svg", "pdf"): 53,
    ("tiff", "pdf"): 58, ("tif", "pdf"): 58,
    ("odt", "pdf"): 59,
    ("ods", "pdf"): 75,
    ("odp", "pdf"): 76,
    ("txt", "pdf"): 77,
    ("rtf", "pdf"): 79,
    ("eps", "pdf"): 86,
    ("azw3", "pdf"): 87,
    ("pdfa", "pdf"): 89, ("pdf/a", "pdf"): 89,
    ("html", "pdf"): 103, ("htm", "pdf"): 103,

    # 图片互转
    ("heic", "jpg"): 81, ("heic", "png"): 81,
    ("webp", "png"): 81,
    ("png", "webp"): 81,
}


def _infer_ext_from_path(path: str) -> Optional[str]:
    """根据路径推断扩展名"""
    if not path:
        return None
    base = path.rsplit("/", 1)[-1]
    if "." not in base:
        return None
    return base.rsplit(".", 1)[-1].lower()


def get_convert_task_type(files: list, target_format: str) -> Optional[int]:
    """根据输入文件和目标格式确定转换任务类型"""
    target = (target_format or "").lower()
    source_ext = None
    if files:
        # 取第一个文件的扩展名
        first = files[0]
        if isinstance(first, dict):
            source_ext = _infer_ext_from_path(first.get("path") or first.get("name") or "")
        elif isinstance(first, str):
            source_ext = _infer_ext_from_path(first)
    if not source_ext:
        return DEFAULT_CONVERT_TYPE
    return CONVERT_TYPE_MAP.get((source_ext, target), DEFAULT_CONVERT_TYPE)


@dataclass
class CostCheckResult:
    """成本检查结果"""
    allow: bool
    message: str = ""
    
    def get_error_response(self, tool_name: str) -> dict:
        """生成成本拒绝的错误响应"""
        error_message = self.message or "操作被拒绝，请检查您的账户余额"
        return {
            "type": "error",
            "content": json.dumps({
                "isError": True,
                "content": [{"type": "text", "text": error_message, "function": tool_name, "annotations": None}]
            }, ensure_ascii=False)
        }


def get_tool_task_type(tool_name: str) -> Optional[int]:
    """获取工具对应的任务类型"""
    return TOOL_TYPE_MAP.get(tool_name, DEFAULT_TOOL_TYPE)


async def check_tool_cost(
    agent_task_id: str,
    tool_name: str,
    arguments: dict,
    pages: Optional[int] = None,
    use_advanced_model: Optional[bool] = None,
    area: Optional[str] = None
) -> CostCheckResult:
    """
    调用成本检查接口，检查是否允许调用该工具。
    
    接口文档：POST /internal/batch-check-task
    
    Args:
        session_id: 会话ID（作为 agent_task_id）
        tool_name: 工具名称
        arguments: 工具参数
        
    Returns:
        CostCheckResult: 检查结果，包含 allow（是否允许）和 message（提示信息）
    """
    # 如果未配置业务 API，直接允许
    cost_check_url = Config.get_lightpdf_api_url_for_area("/internal/batch-check-task", area=area)
    if not cost_check_url:
        return CostCheckResult(allow=True)
    
    # 获取工具对应的任务类型
    task_type: Optional[int] = None

    if tool_name == "convert_document":
        target_format = arguments.get("format")
        files = arguments.get("files", [])
        task_type = get_convert_task_type(files, target_format)
    else:
        task_type = get_tool_task_type(tool_name)

    if task_type in (None, DEFAULT_TOOL_TYPE):
        # 未映射（None）或映射为0时（默认值），打印原始信息并放行
        try:
            print(f"[cost-check] unmapped task_type={task_type} tool={tool_name} args={arguments}")
        except Exception:
            pass
        return CostCheckResult(allow=True)
    
    # 计算任务数量（根据 files 参数中的文件数，默认为 1）
    files = arguments.get("files", [])
    task_count = len(files) if files else 1
    
    try:
        headers = {"Content-Type": "application/json"}
        if Config.LIGHTPDF_API_TOKEN:
            headers["Authorization"] = f"Bearer {Config.LIGHTPDF_API_TOKEN}"

        task_obj = {
            "type": task_type,
            "count": task_count,
            **({"pages": int(pages)} if pages is not None else {}),
            **({"use_advanced_model": bool(use_advanced_model)} if use_advanced_model is not None else {}),
        }

        payload = {
            "agent_task_id": agent_task_id,
            "product_id": Config.LIGHTPDF_PRODUCT_ID,
            "tasks": [
                task_obj
            ]
        }
        print(f"[cost-check] request headers={headers} payload={payload}")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                cost_check_url,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                # 调试日志：打印成本检查返回
                try:
                    debug_data = response.json()
                except Exception:
                    debug_data = response.text
                print(f"[cost-check] status=200 response={debug_data}")

                result = debug_data if isinstance(debug_data, dict) else response.json()
                data = result.get("data", {})
                total_allowed = data.get("total_allowed", False)
                
                if not total_allowed:
                    # 查找具体哪个任务被拒绝
                    results = data.get("results", [])
                    denied_types = [r for r in results if not r.get("allowed", False)]
                    return CostCheckResult(
                        allow=False,
                        message=denied_types[0].get("reason", "操作被拒绝，请检查您的账户余额")
                    )
                
                return CostCheckResult(allow=True)
            else:
                # 接口异常时，默认允许（避免影响正常使用）
                print(f"成本检查接口返回异常状态码: {response.status_code}")
                return CostCheckResult(allow=True)
                
    except httpx.TimeoutException:
        # 超时时默认允许
        print("成本检查接口超时")
        return CostCheckResult(allow=True)
    except Exception as e:
        # 其他异常时默认允许
        print(f"成本检查接口调用失败: {str(e)}")
        return CostCheckResult(allow=True)


def format_tool_call_aggregate_result(yield_messages: list) -> dict:
    """
    聚合多个工具调用的yield_message，返回统一格式。
    Args:
        yield_messages: 所有工具的yield_message列表
    Returns:
        dict: 聚合后的主消息
    """
    if len(yield_messages) == 1:
        return yield_messages[0]
    return {
        "type": "tool_end",
        "results": yield_messages
    }

# AI文档生成工具列表
AI_DOCUMENT_TOOLS = {"create_pdf", "create_word", "create_excel"}

def inject_frontend_params(qa_id: str, tool_name: str, arguments: str) -> str:
    """
    为AI文档生成工具注入前端设置的参数。
    
    Args:
        qa_id: 问答ID，用于获取前端参数
        tool_name: 工具名称
        arguments: 原始参数JSON字符串
        
    Returns:
        str: 注入参数后的JSON字符串
    """
    # package_files：为 zip 文件名注入本地化（基于当前对话 area）
    if tool_name == "package_files":
        try:
            args = json.loads(arguments) if arguments else {}
            area = get_qa_state(f"{qa_id}:area")
            # hk 使用英文，其它使用中文
            zip_name = "Batch-Download" if area == "hk" else "批量下载"
            # 统一覆盖（避免 LLM 随机命名导致多语言不一致）
            args["filename"] = zip_name
            return json.dumps(args, ensure_ascii=False)
        except Exception:
            return arguments

    if tool_name not in AI_DOCUMENT_TOOLS:
        return arguments
    
    try:
        args = json.loads(arguments) if arguments else {}
        
        # 获取前端设置的参数
        use_advanced_model = get_qa_state(f"{qa_id}:use_advanced_model")
        enable_web_search = get_qa_state(f"{qa_id}:enable_web_search")
        language = get_qa_state(f"{qa_id}:language")
        
        # 注入参数（前端参数始终覆盖 AI 生成的参数）
        if use_advanced_model is not None:
            args["use_advanced_model"] = use_advanced_model
        if enable_web_search is not None:
            args["enable_web_search"] = enable_web_search
        if language is not None:
            args["language"] = language  # 前端 language 始终覆盖 AI 推导的值
            
        return json.dumps(args, ensure_ascii=False)
    except Exception:
        return arguments

# 异步工具调用任务（单工具版）
async def tool_task_async(qa_id: str, session_id: str, tool_call: dict) -> tuple:
    """
    工具调用任务（异步版，单工具）。
    Args:
        qa_id: 问答ID
        session_id: 会话ID
        tool_call: 单个工具调用参数
    Returns:
        tuple: (tool_response_message, yield_message)
    """
    from .chat_handler import handle_tool_call
    from .state import append_session_history, get_session_history
    try:
        tool_name_dbg = None
        try:
            tool_name_dbg = tool_call.get("function", {}).get("name")
        except Exception:
            tool_name_dbg = None
        _dbg(f"tool_task_async start qa_id={qa_id} session_id={session_id} tool={tool_name_dbg}")
        t0 = time.monotonic()
        history = get_session_history(session_id)
        api_messages = history.copy()
        from .chat_handler import ToolCall, ToolCallFunction
        
        tool_name = tool_call["function"]["name"]
        original_arguments = tool_call["function"]["arguments"]
        
        # 为AI文档生成工具注入前端参数
        injected_arguments = inject_frontend_params(qa_id, tool_name, original_arguments)
        
        tc_obj = ToolCall(
            id=tool_call.get("id"),
            function=ToolCallFunction(
                name=tool_name,
                arguments=injected_arguments
            )
        )
        tool_response_message, yield_message = await handle_tool_call(tc_obj, api_messages, session_id)
        append_session_history(session_id, tool_response_message)
        set_qa_state(qa_id, {"status": "tool_call_end_ready", "tool_call_end_message": yield_message, "session_id": session_id})
        _dbg(
            f"tool_task_async end qa_id={qa_id} tool={tool_name} "
            f"yield_type={yield_message.get('type') if isinstance(yield_message, dict) else None} "
            f"elapsed_ms={int((time.monotonic()-t0)*1000)}"
        )
        return tool_response_message, yield_message
    except Exception as e:
        _dbg(f"tool_task_async exception qa_id={qa_id}: {str(e)}")
        error_result = {"type": "error", "step_type": "end", "content": f"工具调用异常: {str(e)}"}
        set_qa_state(qa_id, {"status": "finished", "content": f"工具调用异常: {str(e)}", "session_id": session_id})
        return None, error_result