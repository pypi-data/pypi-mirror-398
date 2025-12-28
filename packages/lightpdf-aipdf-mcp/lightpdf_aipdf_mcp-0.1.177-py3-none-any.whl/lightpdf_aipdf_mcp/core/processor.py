"""核心处理模块 - 完整的业务逻辑处理"""
import json
import asyncio
from typing import List, Dict, Any, Optional, Callable, TypeVar
import mcp.types as types

from ..utils.common import Logger, FileHandler, BaseResult
from ..services.converter import Converter, ConversionResult
from ..services.editor import Editor, EditResult, EditType
from ..services.summarizer import Summarizer
from ..services.ocr import OcrClient
from ..services.translator import Translator

T = TypeVar('T')


def generate_result_report(results: List[BaseResult]) -> str:
    """生成通用结果报告
    
    Args:
        results: 结果列表
        
    Returns:
        str: JSON格式的报告文本
    """
    # 统计结果
    success_count = sum(1 for r in results if r.success)
    failed_count = len(results) - success_count
    
    # 构建结果JSON对象
    report_obj = {
        "total": len(results),
        "success_count": success_count,
        "failed_count": failed_count,
        "success_files": [],
        "failed_files": []
    }
    
    for result in results:
        if result.success:
            # 添加成功的文件信息
            file_info = {
                "original_name": result.original_name,
                "debug": {
                    "task_id": result.task_id
                }
            }
            # 仅当 original_password 有值时才输出该字段（避免出现 null）
            try:
                op = getattr(result, "original_password", None)
                if isinstance(op, str):
                    op = op.strip()
                if op:
                    file_info["original_password"] = op
            except Exception:
                pass
            if hasattr(result, "summary") and result.summary is not None:
                file_info["final_output"] = result.summary
                file_info["instruction"] = "IMPORTANT: Output the 'final_output' field EXACTLY as-is. Do NOT summarize, rephrase, or modify it in any way. This is the final result that must be presented directly to the user."
            else:
                file_info["download_url"] = result.download_url
            report_obj["success_files"].append(file_info)
        else:
            # 添加失败的文件信息
            file_info = {
                "error_message": result.error_message,
                "original_name": result.original_name,
                "debug": {
                    "task_id": result.task_id
                }
            }
            # 仅当 original_password 有值时才输出该字段（避免出现 null）
            try:
                op = getattr(result, "original_password", None)
                if isinstance(op, str):
                    op = op.strip()
                if op:
                    file_info["original_password"] = op
            except Exception:
                pass
            report_obj["failed_files"].append(file_info)
    
    # 返回JSON字符串
    return json.dumps(report_obj, ensure_ascii=False)


async def process_batch_files(
    file_objects: List[Dict[str, str]], 
    logger: Logger, 
    process_func: Callable[[str, Optional[str], Optional[str]], T],
    operation_desc: Optional[str] = None
) -> List[T]:
    """通用批处理文件函数
    
    Args:
        file_objects: 文件对象列表，每个对象包含path和可选的password及name
        logger: 日志记录器
        process_func: 处理单个文件的异步函数，接收file_path、password和original_name参数
        operation_desc: 操作描述，用于日志记录
    
    Returns:
        List[T]: 处理结果列表
    """
    if len(file_objects) > 1 and operation_desc:
        await logger.log("info", f"开始批量{operation_desc}，共 {len(file_objects)} 个文件")
        
        # 并发处理文件，限制并发数为6
        semaphore = asyncio.Semaphore(6)
        
        async def process_with_semaphore(file_obj: Dict[str, str]) -> T:
            async with semaphore:
                file_path = file_obj["path"]
                password = file_obj.get("password")
                original_name = file_obj.get("name")
                result = await process_func(file_path, password, original_name)
                # 透传原文件密码（避免在后续链式步骤丢失）
                try:
                    if isinstance(result, BaseResult) and password and not getattr(result, "original_password", None):
                        result.original_password = password
                except Exception:
                    pass
                return result
        
        # 创建任务列表
        tasks = [process_with_semaphore(file_obj) for file_obj in file_objects]
        return await asyncio.gather(*tasks)
    else:
        # 单文件处理
        file_path = file_objects[0]["path"]
        password = file_objects[0].get("password")
        original_name = file_objects[0].get("name")
        result = await process_func(file_path, password, original_name)
        try:
            if isinstance(result, BaseResult) and password and not getattr(result, "original_password", None):
                result.original_password = password
        except Exception:
            pass
        return [result]


async def process_conversion_file(
    file_path: str, 
    format: str, 
    converter: Converter, 
    extra_params: Optional[Dict[str, Any]] = None, 
    password: Optional[str] = None,
    original_name: Optional[str] = None
) -> ConversionResult:
    """处理单个文件转换"""
    is_page_numbering = format == "number-pdf"
    
    if is_page_numbering and extra_params:
        # 对于添加页码，使用add_page_numbers方法
        return await converter.add_page_numbers(
            file_path, 
            extra_params.get("start_num", 1),
            extra_params.get("position", "5"),
            extra_params.get("margin", 30),
            password,
            original_name
        )
    else:
        # 处理extra_params
        if extra_params is None:
            extra_params = {}
        
        # 直接传递 merge_all 参数（如有）
        # 其它逻辑交由 converter.convert_file 处理
        return await converter.convert_file(file_path, format, extra_params, password, original_name)


async def process_edit_file(
    file_path: str, 
    edit_type: str, 
    editor: Editor, 
    extra_params: Dict[str, Any] = None,
    password: Optional[str] = None,
    original_name: Optional[str] = None
) -> EditResult:
    """处理单个文件编辑"""
    if edit_type == "decrypt":
        return await editor.decrypt_pdf(file_path, password, original_name)
    elif edit_type == "add_text_watermark":
        return await editor.add_text_watermark(
            file_path=file_path,
            text=extra_params.get("text", "文本水印"),
            position=extra_params.get("position", "center"),
            opacity=extra_params.get("opacity", 1.0),
            range=extra_params.get("range", ""),
            layout=extra_params.get("layout", "on"),
            font_family=extra_params.get("font_family"),
            font_size=extra_params.get("font_size"),
            font_color=extra_params.get("font_color"),
            password=password,
            original_name=original_name
        )
    elif edit_type == "add_image_watermark":
        return await editor.add_image_watermark(
            file_path=file_path,
            image_url=extra_params.get("image_url"),
            position=extra_params.get("position", "center"),
            opacity=extra_params.get("opacity", 0.7),
            range=extra_params.get("range", ""),
            layout=extra_params.get("layout", "on"),
            password=password,
            original_name=original_name
        )
    elif edit_type == "encrypt":
        return await editor.encrypt_pdf(
            file_path=file_path,
            password=extra_params.get("password", ""),
            provider=extra_params.get("provider", ""),
            original_password=password,
            original_name=original_name
        )
    elif edit_type == "compress":
        return await editor.compress_pdf(
            file_path=file_path,
            image_quantity=extra_params.get("image_quantity", 60),
            password=password,
            original_name=original_name
        )
    elif edit_type == "split":
        return await editor.split_pdf(
            file_path=file_path,
            pages=extra_params.get("pages", ""),
            password=password,
            split_type=extra_params.get("split_type", "page"),
            merge_all=extra_params.get("merge_all", 1),
            original_name=original_name
        )
    elif edit_type == "merge":
        # 对于合并操作，我们需要特殊处理，因为它需要处理多个文件
        return EditResult(
            success=False, 
            file_path=file_path, 
            error_message="合并操作需要使用特殊处理流程",
            original_name=original_name
        )
    elif edit_type == "rotate":
        # 从extra_params获取旋转参数列表
        rotation_arguments = extra_params.get("rotates", [])
        
        # 验证旋转参数列表
        if not rotation_arguments:
            return EditResult(
                success=False, 
                file_path=file_path, 
                error_message="旋转操作需要至少提供一个旋转参数",
                original_name=original_name
            )
        
        # 构建angle_params字典: {"90": "2-4,6-8", "180": "all"}
        angle_params = {}
        for arg in rotation_arguments:
            angle = str(arg.get("angle", 90))
            pages = arg.get("pages", "all") or "all"  # 确保空字符串转为"all"
            angle_params[angle] = pages
        
        # 直接调用rotate_pdf方法，传入角度参数字典
        return await editor.rotate_pdf(
            file_path=file_path,
            angle_params=angle_params,
            password=password,
            original_name=original_name
        )
    elif edit_type == "remove_margin":
        # 直接调用remove_margin方法，不需要额外参数
        return await editor.remove_margin(
            file_path=file_path,
            password=password,
            original_name=original_name
        )
    elif edit_type == "extract_image":
        # 调用extract_images方法提取图片
        return await editor.extract_images(
            file_path=file_path,
            format=extra_params.get("format", "png"),
            password=password,
            original_name=original_name
        )
    elif edit_type == "pdf-delete-page":
        # 调用delete_pages方法删除页面
        return await editor.delete_pages(
            file_path=file_path,
            range=extra_params.get("range", ""),
            password=password,
            original_name=original_name
        )
    else:
        return EditResult(
            success=False, 
            file_path=file_path, 
            error_message=f"不支持的编辑类型: {edit_type}",
            original_name=original_name
        )


async def process_tool_call(
    logger: Logger, 
    file_objects: List[Dict[str, str]], 
    operation_config: Dict[str, Any]
) -> types.TextContent:
    """通用工具调用处理函数
    
    Args:
        logger: 日志记录器
        file_objects: 文件对象列表，每个对象包含path和可选的password
        operation_config: 操作配置，包括操作类型、格式、参数等
        
    Returns:
        types.TextContent: 包含处理结果的文本内容
    """
    file_handler = FileHandler(logger)
    editor = Editor(logger, file_handler)
    extra_params = operation_config.get("extra_params", {})

    # 新增：摘要操作分支
    if operation_config.get("is_summarize_operation"):
        summarizer = Summarizer(logger, file_handler)

        results = await process_batch_files(
            file_objects,
            logger,
            lambda file_path, password, original_name: summarizer.summarize_pdf(
                file_path=file_path,
                prompt=extra_params.get("prompt", "Give me a summary of the document."),
                language=extra_params.get("language", "en"),
                password=password,
                original_name=original_name
            ),
            "PDF摘要"
        )
        report_msg = generate_result_report(results)

    # 新增：OCR操作分支
    elif operation_config.get("is_ocr_operation"):
        ocr_client = OcrClient(logger, file_handler)

        results = await process_batch_files(
            file_objects,
            logger,
            lambda file_path, password, original_name: ocr_client.ocr_document(
                file_path=file_path,
                format=extra_params.get("format", "pdf"),
                language=extra_params.get("language", "English,Digits,ChinesePRC"),
                password=password,
                original_name=original_name
            ),
            "文档OCR识别"
        )
        report_msg = generate_result_report(results)

    # 新增：翻译操作分支
    elif operation_config.get("is_translate_operation"):
        translator = Translator(logger, file_handler)

        results = await process_batch_files(
            file_objects,
            logger,
            lambda file_path, password, original_name: translator.translate_pdf(
                file_path=file_path,
                source=extra_params.get("source", "auto"),
                target=extra_params.get("target"),
                output_type=extra_params.get("output_type", "mono"),
                password=password,
                original_name=original_name
            ),
            "PDF翻译"
        )

        report_msg = generate_result_report(results)

    # 根据操作类型选择不同的处理逻辑
    elif operation_config.get("is_edit_operation"):
        # 编辑操作
        edit_type = operation_config.get("edit_type", "")

        # 获取操作描述
        edit_map = {
            "decrypt": "解密", 
            "add_text_watermark": "添加文本水印", 
            "add_image_watermark": "添加图片水印", 
            "encrypt": "加密", 
            "compress": "压缩", 
            "split": "拆分", 
            "merge": "合并", 
            "rotate": "旋转",
            "remove_margin": "去除白边",
            "pdf-delete-page": "删除页面"
        }
        operation_desc = f"PDF{edit_map.get(edit_type, edit_type)}"

        # 处理文件
        results = await process_batch_files(
            file_objects, 
            logger,
            lambda file_path, password, original_name: process_edit_file(
                file_path, edit_type, editor, extra_params, password, original_name
            ),
            operation_desc
        )

        # 生成报告
        report_msg = generate_result_report(results)

    else:
        # 转换操作
        converter = Converter(logger, file_handler)
        format = operation_config.get("format", "")

        # 特殊处理：PDF 转 LaTeX（TEX）仍走 editor 的 oss://pdf2tex
        # PDF 转 Markdown 改为直接使用转换接口：format='md'
        if format == "tex":
            oss_url, operation_desc = ("oss://pdf2tex", "PDF转LaTeX")
            results = await process_batch_files(
                file_objects,
                logger,
                lambda file_path, password, original_name: editor.edit_pdf(
                    file_path,
                    edit_type=EditType.EDIT,
                    extra_params={"pages": [{"url": oss_url, "oss_file": ""}]},
                    password=password,
                    original_name=original_name
                ),
                operation_desc
            )
            report_msg = generate_result_report(results)

        elif format == "pdf":
            # TXT -> PDF 等也统一使用转换接口处理（不再需要 oss://txt2pdf 特殊分支）
            results = await process_batch_files(
                file_objects,
                logger,
                lambda file_path, password, original_name: process_conversion_file(
                    file_path, format, converter, extra_params, password, original_name
                ),
                f"转换为 {format} 格式"
            )

            report_msg = generate_result_report(results)

        else:
            # 获取操作描述
            if format == "doc-repair":
                operation_desc = "去除水印"
            elif format == "number-pdf":
                operation_desc = "添加页码"
            elif format == "flatten-pdf":
                operation_desc = "展平PDF"
            elif format == "pdf-replace-text":
                operation_desc = "替换文本"
            elif format == "pdf-repair":
                operation_desc = "修复PDF"
            elif format == "curve-pdf":
                operation_desc = "PDF转曲"
            elif format == "double-pdf":
                operation_desc = "转换为双层PDF"
            elif format == "pdf-delete-page":
                operation_desc = "删除PDF页面"
            else:
                operation_desc = f"转换为 {format} 格式"

            # 处理文件
            results = await process_batch_files(
                file_objects,
                logger,
                lambda file_path, password, original_name: process_conversion_file(
                    file_path, format, converter, extra_params, password, original_name
                ),
                operation_desc
            )

            # 生成报告
            report_msg = generate_result_report(results)

    # 如果全部失败，记录错误
    if not any(r.success for r in results):
        await logger.error(report_msg)

    return types.TextContent(type="text", text=report_msg) 