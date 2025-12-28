"""FastMCP适配层 - 连接FastMCP和现有业务逻辑"""
import json
import os
from typing import List, Dict, Any, Optional
from urllib.request import url2pathname

from fastmcp import Context
from ..utils.common import Logger, FileHandler, BaseResult
from ..models.schemas import FileObject


def convert_file_objects(files: List[FileObject]) -> List[Dict[str, str]]:
    """转换FastMCP文件对象为原有格式"""
    file_objects = []
    for file_obj in files:
        converted = {"path": file_obj.path}
        
        # 处理file://协议
        if file_obj.path.startswith("file://"):
            converted["path"] = url2pathname(file_obj.path.removeprefix('file:'))
        
        if file_obj.password:
            converted["password"] = file_obj.password
        if file_obj.name:
            converted["name"] = file_obj.name
            
        file_objects.append(converted)
    
    return file_objects


def generate_operation_config(
    operation_type: str,
    format_value: Optional[str] = None,
    extra_params: Optional[Dict[str, Any]] = None,
    edit_type: Optional[str] = None
) -> Dict[str, Any]:
    """生成操作配置字典"""
    config = {}
    
    # 设置操作类型
    if operation_type == "convert":
        config["is_edit_operation"] = False
        if format_value:
            config["format"] = format_value
    elif operation_type == "edit":
        config["is_edit_operation"] = True
        if edit_type:
            config["edit_type"] = edit_type
    elif operation_type == "translate":
        config["is_translate_operation"] = True
    elif operation_type == "ocr":
        config["is_ocr_operation"] = True
    elif operation_type == "summarize":
        config["is_summarize_operation"] = True
    
    # 设置额外参数
    if extra_params:
        config["extra_params"] = extra_params
    
    return config


async def process_tool_call_adapter(
    logger: Logger,
    file_objects: List[FileObject], 
    operation_config: Dict[str, Any]
) -> str:
    """适配原有的process_tool_call函数"""
    from ..core.processor import process_tool_call
    
    # 转换文件对象格式
    converted_files = convert_file_objects(file_objects)
    
    # 调用原有函数
    result = await process_tool_call(logger, converted_files, operation_config)
    
    # 返回文本内容
    return result.text


async def create_document_adapter(
    logger: Logger,
    prompt: str,
    filename: str,
    language: str,
    document_type: str,
    enable_web_search: bool = False,
    use_advanced_model: bool = False
) -> str:
    """通用文档创建适配器"""
    from ..services.create_pdf import DocumentCreator
    from ..utils.common import FileHandler
    
    # 创建file_handler
    file_handler = FileHandler(logger)
    
    # 创建文档创建器
    document_creator = DocumentCreator(logger, file_handler)
    
    # 根据文档类型调用相应方法
    if document_type == "pdf":
        result = await document_creator.create_pdf_from_prompt(
            prompt=prompt,
            language=language,
            enable_web_search=enable_web_search,
            use_advanced_model=use_advanced_model,
            original_name=filename
        )
    elif document_type == "word":
        result = await document_creator.create_word_from_prompt(
            prompt=prompt,
            language=language,
            enable_web_search=enable_web_search,
            use_advanced_model=use_advanced_model,
            original_name=filename
        )
    elif document_type == "excel":
        result = await document_creator.create_excel_from_prompt(
            prompt=prompt,
            language=language,
            enable_web_search=enable_web_search,
            use_advanced_model=use_advanced_model,
            original_name=filename
        )
    else:
        # 创建错误结果
        from ..services.create_pdf import CreatePdfResult
        result = CreatePdfResult(
            success=False,
            file_path="",
            error_message=f"不支持的文档类型: {document_type}",
            original_name=filename
        )
    
    # 生成报告
    from ..core.processor import generate_result_report
    return generate_result_report([result])


async def create_pdf_adapter(
    logger: Logger,
    prompt: str,
    filename: str,
    language: str,
    enable_web_search: bool = False,
    use_advanced_model: bool = False
) -> str:
    """适配PDF创建功能"""
    return await create_document_adapter(logger, prompt, filename, language, "pdf", enable_web_search, use_advanced_model)


async def merge_pdfs_adapter(
    logger: Logger,
    files: List[FileObject]
) -> str:
    """适配PDF合并功能"""
    from ..services.editor import Editor
    from ..utils.common import FileHandler
    
    # 创建file_handler
    file_handler = FileHandler(logger)
    
    # 创建编辑器
    editor = Editor(logger, file_handler)
    
    # 转换文件对象
    file_paths = [file_obj.path for file_obj in files]
    passwords = [file_obj.password for file_obj in files if file_obj.password]
    original_names = [file_obj.name for file_obj in files if file_obj.name]
    
    # 处理file://协议
    for i, path in enumerate(file_paths):
        if path.startswith("file://"):
            file_paths[i] = url2pathname(path.removeprefix('file:'))
    
    # 使用第一个非空密码
    password = passwords[0] if passwords else None
    
    # 合并文件名
    merged_name = None
    if original_names:
        if len(original_names) == 1:
            merged_name = original_names[0]
        else:
            merged_name = f"{original_names[0]}_{original_names[1]}_等"
    
    # 调用合并方法
    result = await editor.merge_pdfs(file_paths, password, merged_name)
    
    # 生成报告
    from ..core.processor import generate_result_report
    return generate_result_report([result])


async def package_files_adapter(
    logger: Logger,
    files: List[FileObject],
    filename: Optional[str] = None
) -> str:
    """适配文件打包功能（返回zip链接）"""
    from ..services.archiver import Archiver
    from ..utils.common import FileHandler
    from ..core.processor import generate_result_report

    file_handler = FileHandler(logger)
    archiver = Archiver(logger, file_handler)

    file_paths = [file_obj.path for file_obj in files]
    original_names = [file_obj.name for file_obj in files if file_obj.name]
    # 可选：压缩包内自定义文件名（key 支持 resource_id 或 url）
    custom_filenames: Dict[str, str] = {}
    for f in files:
        if not f or not f.name or not f.path:
            continue
        base = os.path.basename(f.name)
        stem, _ext = os.path.splitext(base)
        custom_name = stem or base
        if not custom_name:
            continue
        if file_handler.is_oss_id(f.path):
            key = f.path.split("oss_id://", 1)[1]
            custom_filenames[key] = custom_name
        elif file_handler.is_url(f.path):
            custom_filenames[f.path] = custom_name

    # 处理file://协议
    for i, path in enumerate(file_paths):
        if path.startswith("file://"):
            file_paths[i] = url2pathname(path.removeprefix('file:'))

    pkg_name = filename
    if not pkg_name:
        if original_names:
            pkg_name = f"{original_names[0]}_zip.zip" if len(original_names) > 1 else f"{original_names[0]}.zip"
        else:
            pkg_name = "results.zip"

    # archive 接口本身不保证支持 filename，这里仅作为 original_name 传递用于结果展示
    result = await archiver.package_files(file_paths, pkg_name, custom_filenames=custom_filenames or None)
    return generate_result_report([result])


async def remove_image_watermark_adapter(logger: Logger, files: List[FileObject]) -> str:
    """适配：图片去水印"""
    from ..services.image_processor import ImageProcessor
    from ..utils.common import FileHandler
    from ..core.processor import generate_result_report

    file_handler = FileHandler(logger)
    processor = ImageProcessor(logger, file_handler)
    pairs = [(f.path, f.name) for f in files if getattr(f, "path", None)]
    results = await processor.remove_image_watermark(pairs)
    return generate_result_report(results)


async def remove_image_logo_adapter(logger: Logger, files: List[FileObject]) -> str:
    """适配：去除Logo（占位实现）"""
    from ..services.image_processor import ImageProcessor
    from ..utils.common import FileHandler
    from ..core.processor import generate_result_report

    file_handler = FileHandler(logger)
    processor = ImageProcessor(logger, file_handler)
    pairs = [(f.path, f.name) for f in files if getattr(f, "path", None)]
    results = await processor.remove_image_logo(pairs)
    return generate_result_report(results)


async def remove_image_sticker_adapter(logger: Logger, files: List[FileObject]) -> str:
    """适配：去除贴纸"""
    from ..services.image_processor import ImageProcessor
    from ..utils.common import FileHandler
    from ..core.processor import generate_result_report

    file_handler = FileHandler(logger)
    processor = ImageProcessor(logger, file_handler)
    pairs = [(f.path, f.name) for f in files if getattr(f, "path", None)]
    results = await processor.remove_image_sticker(pairs)
    return generate_result_report(results)


async def remove_image_text_adapter(logger: Logger, files: List[FileObject]) -> str:
    """适配：去除文字（占位实现）"""
    from ..services.image_processor import ImageProcessor
    from ..utils.common import FileHandler
    from ..core.processor import generate_result_report

    file_handler = FileHandler(logger)
    processor = ImageProcessor(logger, file_handler)
    pairs = [(f.path, f.name) for f in files if getattr(f, "path", None)]
    results = await processor.remove_image_text(pairs)
    return generate_result_report(results)


async def create_word_adapter(
    logger: Logger,
    prompt: str,
    filename: str,
    language: str,
    enable_web_search: bool = False,
    use_advanced_model: bool = False
) -> str:
    """适配Word文档创建功能"""
    return await create_document_adapter(logger, prompt, filename, language, "word", enable_web_search, use_advanced_model)


async def create_excel_adapter(
    logger: Logger,
    prompt: str,
    filename: str,
    language: str,
    enable_web_search: bool = False,
    use_advanced_model: bool = False
) -> str:
    """适配Excel文档创建功能"""
    return await create_document_adapter(logger, prompt, filename, language, "excel", enable_web_search, use_advanced_model)