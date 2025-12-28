"""LightPDF Agent FastMCP Server模块"""
import asyncio
import os
import sys
import argparse
from typing import List, Optional, Literal, Annotated

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# FastMCP相关导入
from fastmcp import FastMCP, Context

# Pydantic导入用于参数描述
from pydantic import Field

# 本地导入
from ..models.schemas import FileObject
from ..utils.common import Logger
from .adapter import (
    process_tool_call_adapter, generate_operation_config,
    create_pdf_adapter, create_word_adapter, create_excel_adapter, merge_pdfs_adapter, package_files_adapter,
    remove_image_watermark_adapter, remove_image_logo_adapter, remove_image_sticker_adapter, remove_image_text_adapter
)

# 创建FastMCP实例
mcp = FastMCP(
    name="LightPDF_AI_tools",
    instructions="LightPDF Document Processing Tools powered by FastMCP."
)

# ==================== 文档转换工具 ====================

@mcp.tool
async def convert_document(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of files to convert, each containing path and optional password")],
    format: Annotated[
        Literal[
            "pdf", "pdfa", "pdf/a",
            "docx", "doc",
            "xlsx", "xls",
            "pptx", "ppt",
            "jpg", "jpeg", "png", "gif", "bmp", "wmf", "emf", "tiff", "tif", "svg", "webp",
            "html", "txt", "csv", "md", "rtf", "tex",
            "epub", "odt", "azw3", "eps",
        ],
        Field(
            ...,
            description=(
                "Target output format. NOTE: supported conversions depend on input file type (by extension). "
                "Direct image-to-image conversions are NOT generally supported (e.g. PNG↔JPG/JPEG will fail), "
                "except: HEIC→(JPG/JPEG/PNG), WEBP→PNG, PNG→WEBP."
            ),
        ),
    ],
    pdfa_format: Annotated[Optional[int], Field(description="Only effective when format is 'pdfa' (or 'pdf/a'). PDF/A profile selector (0-7). Mapping: 0=pdf/a-1a, 1=pdf/a-1b, 2=pdf/a-2a, 3=pdf/a-3a, 4=pdf/a-2b, 5=pdf/a-2u, 6=pdf/a-3b, 7=pdf/a-3u", ge=0, le=7)] = 0,
    merge_all: Annotated[int, Field(description="Special merge option (0 or 1). Only effective in specific scenarios: PDF→Image (1=merge all pages into one long image), Image→PDF (1=merge all images into single PDF), PDF→Excel (1=merge all pages into one sheet). Default 0=no merge", ge=0, le=1)] = 0,
    one_page_per_sheet: Annotated[bool, Field(description="Only effective when converting Excel to PDF. If true, each sheet fits into single PDF page")] = False,
    has_formula: Annotated[bool, Field(description="Indicates if the source PDF contains mathematical formulas. When set to true, applies formula-aware conversion optimization. Only effective when converting PDF to Word (docx) or PowerPoint (pptx) formats. Default false")] = False,
    image_quality: Annotated[Optional[int], Field(description="Image quality setting (0-200). Higher values = better quality but larger file size. Only effective when converting PDF to image formats (jpg, jpeg, png, gif, bmp, wmf, emf, tiff, tif, svg). If not specified, uses default value 100", ge=0, le=200)] = None
) -> Annotated[str, "JSON formatted result report with converted file download URLs and conversion details"]:
    """
    Document format conversion tool supporting various file formats including PDFs, Office documents, images, and text files.

    **FROM PDF - Supported output formats when converting from PDF:**
    - Documents: DOCX/DOC, XLSX/XLS, PPTX/PPT, HTML, TXT, CSV, MD (Markdown), RTF, TEX (LaTeX), ODT, EPUB, AZW3 (Kindle eBook)
    - Images: JPG, JPEG, PNG, GIF, BMP, WMF, EMF, TIFF/TIF, SVG
    - Archival: PDF/A (use format='pdfa' or 'pdf/a')
    
    **TO PDF - Supported input formats that can be converted to PDF:**
    - Documents: DOC/DOCX, XLS/XLSX, PPT/PPTX, HTML/HTM, TXT, MD, RTF, ODT, TEX (LaTeX), AZW3 (Kindle eBook)
    - Images: JPG (includes .jpeg files), PNG, GIF, BMP, HEIC, SVG, TIFF (includes .tif files), WEBP, EPS (Encapsulated PostScript)
    - Graphics: CAD (DWG), DXF, ODG (OpenDocument Graphics)
    - Office: ODS (OpenDocument Spreadsheet), ODP (OpenDocument Presentation)
    - eBook: EPUB, MOBI
    - Special: CAJ, OFD
    
    **Image format conversions - Direct image-to-image conversions (only these are supported):**
    - HEIC → JPG / JPEG / PNG
    - WEBP → PNG
    - PNG → WEBP
    - NOT supported: PNG ↔ JPG/JPEG, JPG/JPEG → PNG, and most other image↔image conversions.
    
    Use cases:
    - When sharing documents via email and recipients need specific formats (e.g., converting PDF to Word for editing)
    - When uploading files to websites or online platforms that only accept certain formats
    - When you need to extract and edit text content from PDFs for quick revisions
    - When creating presentations or social media content from existing PDF materials
    - When archiving documents in standardized formats for long-term storage compliance
    - When converting PDFs with mathematical formulas to Word or PowerPoint for better formula preservation and editing

    Important Notes:
    - PDF to PDF conversion is not supported, EXCEPT PDF → PDF/A.
    - PDF/A output is only supported when the input file is a PDF (i.e., PDF → PDF/A). Use format='pdfa' (or 'pdf/a') and optionally set pdfa_format (0-7) to choose the PDF/A profile.
    - If your source file is not a PDF but you need PDF/A, convert it to PDF first, then convert that PDF to PDF/A (two-step conversion).
    - Only entire files can be converted.
    - For HTML to PDF, both local HTML files and any web page URL are supported
    - For content-based PDF creation from LaTeX code, use create_pdf tool instead
    - For extracting embedded images from PDFs, use extract_images tool instead
    - For text recognition from scanned/image PDFs, use ocr_document tool instead
    - For IMAGE files to TEXT formats (JPG/PNG/GIF/BMP → TXT/DOCX/XLSX/PPTX), use ocr_document tool instead
    - PDF to TXT conversion here extracts existing text; for scanned documents use ocr_document tool instead
    - PDF to image conversion creates images of PDF pages; extract_images gets embedded images
    - Formula conversion optimization (has_formula=true) is only effective when converting PDF to Word or PowerPoint
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始转换 {len(files)} 个文件到 {format} 格式...")
    
    # 构建操作配置
    extra_params = {
        "merge_all": merge_all,
        "one_page_per_sheet": one_page_per_sheet
    }

    # PDF/A 参数（接口底层为 pdf-to-pdfa + args.format）
    if format in ("pdfa", "pdf/a"):
        extra_params = {
            "args": {"format": str(pdfa_format if pdfa_format is not None else 0)}
        }
    
    # 处理image_quality参数
    # 如果是PDF转图片格式且没有指定image_quality，默认使用100
    image_formats = {"jpg", "jpeg", "png", "gif", "bmp", "wmf", "emf", "tiff", "tif", "svg"}
    if format in image_formats and image_quality is None:
        image_quality = 100
    
    # 添加image_quality参数（如果有值）
    if image_quality is not None:
        extra_params["image_quality"] = image_quality
        extra_params["image-quality"] = image_quality
    
    # 处理has_formula参数
    # 仅当目标格式为Word或PPT，且has_formula为True时，添加provider="formula"
    if has_formula and format in ("docx", "pptx"):
        extra_params["provider"] = "formula"
        await logger.log("info", f"检测到文档包含公式，启用公式优化转换模式")
    
    operation_config = generate_operation_config(
        operation_type="convert",
        format_value=format,
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "转换完成")
    return result

@mcp.tool
async def add_page_numbers(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to add page numbers to")],
    start_num: Annotated[int, Field(description="Starting page number", ge=1)] = 1,
    position: Annotated[Literal["1", "2", "3", "4", "5", "6"], Field(description="Page number position: 1(top-left), 2(top-center), 3(top-right), 4(bottom-left), 5(bottom-center), 6(bottom-right)")] = "5",
    margin: Annotated[Literal[10, 30, 60], Field(description="Page number margin distance from page edges in points (pt). Options: 10=close, 30=medium, 60=far")] = 30
) -> Annotated[str, "JSON formatted result report with PDF files containing added page numbers"]:
    """
    Add sequential page numbers to PDF documents. This tool automatically adds page numbers to each page of the PDF at the specified position with customizable starting number, position, and margin.
    
    Use cases:
    - When submitting academic papers or legal documents that require numbered pages for reference
    - When preparing multi-section reports where readers need to navigate between different parts
    - When printing large documents that may get mixed up and need proper ordering
    - When creating training manuals or handbooks where page citations are essential
    
    Note: This adds new page numbers to the document. It does not modify existing page numbers. For documents that already have page numbers, consider using replace_text to modify them instead.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始为 {len(files)} 个PDF文件添加页码...")
    
    # 构建操作配置
    extra_params = {
        "start_num": start_num,
        "position": position,
        "margin": margin
    }
    
    operation_config = generate_operation_config(
        operation_type="convert",
        format_value="number-pdf",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "页码添加完成")
    return result

@mcp.tool
async def remove_watermark(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to remove watermarks from")]
) -> Annotated[str, "JSON formatted result report with watermark-free PDF files"]:
    """
    Remove watermarks from PDF files. This tool uses specialized algorithms to detect and remove overlay elements such as text or image watermarks.
    
    Use cases:
    - When you need to remove "DRAFT", "SAMPLE", or company watermarks before sharing documents
    - When reusing templates or documents that contain outdated branding or watermarks
    - When preparing clean versions of documents for professional presentation or redistribution
    - When processing scanned documents that have unwanted background text or stamps
    
    Note: This is specifically for watermarks and overlay elements, not regular document text. For editing or deleting normal document text content, use replace_text instead.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始为 {len(files)} 个PDF文件去除水印...")
    
    # 构建操作配置
    operation_config = generate_operation_config(
        operation_type="convert",
        format_value="doc-repair"
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "水印去除完成")
    return result

# ==================== PDF编辑工具 ====================

@mcp.tool
async def compress_pdf(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to compress")],
    image_quantity: Annotated[int, Field(description="Image quality, 1-100, lower values result in higher compression", ge=1, le=100)] = 60
) -> Annotated[str, "JSON formatted result report containing success/failure counts, file information, and download URLs or error messages"]:
    """
    Reduce PDF file size by optimizing images and removing redundant data. This tool compresses PDF files to make them smaller for easier sharing, faster uploading, and reduced storage usage.
    
    Use cases:
    - When email systems reject your PDF attachments due to size limits (typically 25MB or less)
    - When uploading documents to online platforms with strict file size restrictions  
    - When sending documents to clients in regions with slow internet connections
    - When storing large volumes of documents on limited server space or cloud storage
    
    Note: Compression is lossy for images but lossless for text. Original image quality cannot be restored after compression.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始压缩 {len(files)} 个PDF文件...")
    
    # 构建操作配置
    extra_params = {
        "image_quantity": image_quantity
    }
    
    operation_config = generate_operation_config(
        operation_type="edit",
        edit_type="compress",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF压缩完成")
    return result

@mcp.tool
async def merge_pdfs(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to merge (must be at least two)", min_length=2)]
) -> Annotated[str, "JSON formatted result report with merged PDF file download URL"]:
    """
    Merge multiple PDF files into a single PDF file. You must provide at least two files in the 'files' array, otherwise the operation will fail.
    
    Use cases:
    - When combining multiple documents for email sharing or easier file management
    - When collecting reports from different departments for a unified presentation
    - When consolidating invoices, receipts, or contracts for accounting or record keeping
    - When creating project portfolios or complete documentation packages
    """
    logger = Logger(ctx, collect_info=False)
    if len(files) < 2:
        await logger.log("error", "合并PDF至少需要两个文件")
        return '{"total": 0, "success_count": 0, "failed_count": 1, "success_files": [], "failed_files": [{"error_message": "合并PDF至少需要两个文件"}]}'
    
    await logger.log("info", f"开始合并 {len(files)} 个PDF文件...")
    
    # 使用特殊的合并适配器
    result = await merge_pdfs_adapter(logger, files)
    
    await logger.log("info", "PDF合并完成")
    return result


@mcp.tool
async def package_files(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of files to package into a single zip (must be at least two)", min_length=2)],
    filename: Annotated[Optional[str], Field(description="Optional zip filename, e.g. 'packaged'")] = None
) -> Annotated[str, "JSON formatted result report with packaged zip download URL"]:
    """
    Package multiple output files into a single ZIP file and return one download URL.
    Use this when a workflow generates multiple files and you want to deliver a single zip to the user.
    Note: If FileObject.name is provided, it will be used to set custom filenames inside the zip (custom_filenames).
    """
    logger = Logger(ctx, collect_info=False)
    if len(files) < 2:
        await logger.log("error", "打包至少需要两个文件")
        return '{"total": 0, "success_count": 0, "failed_count": 1, "success_files": [], "failed_files": [{"error_message": "打包至少需要两个文件"}]}'

    await logger.log("info", f"开始打包 {len(files)} 个文件...")
    result = await package_files_adapter(logger, files, filename)
    await logger.log("info", "文件打包完成")
    return result

# ==================== 图片处理工具 ====================

@mcp.tool
async def remove_image_watermark(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of image files to remove watermarks from")]
) -> Annotated[str, "JSON formatted result report with processed image download URLs"]:
    """
    Remove watermarks from images. This tool removes common overlay elements such as text watermarks, stamps, or unwanted marks from pictures.
    
    Use cases:
    - When you need to clean product photos or social media images before publishing
    - When removing "SAMPLE", "DRAFT", or branding overlays from images
    - When preparing images for presentations, documentation, or printing
    - When cleaning scanned photos that contain stamps or overlaid marks
    
    Note: This is for removing watermark-like overlays. For PDF watermark removal, use remove_watermark instead.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始处理 {len(files)} 张图片（AI去水印）...")
    return await remove_image_watermark_adapter(logger, files)


@mcp.tool
async def remove_image_logo(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of image files to remove logos from")]
) -> Annotated[str, "JSON formatted result report with processed image download URLs"]:
    """
    Remove logos from images.
    
    Use cases:
    - When you need a clean version of an image without branding marks
    - When preparing assets for internal review or reuse
    - When removing corner logos on screenshots or scanned images
    
    Note: If a logo is blended into the background or overlaps important content, results may vary.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始处理 {len(files)} 张图片（去Logo）...")
    return await remove_image_logo_adapter(logger, files)


@mcp.tool
async def remove_image_sticker(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of image files to remove stickers from")]
) -> Annotated[str, "JSON formatted result report with processed image download URLs"]:
    """
    Remove stickers from images.
    
    Use cases:
    - When cleaning photos with emojis, stickers, or decorative overlays
    - When restoring a clean version for printing or archiving
    - When preparing product images that contain promotional stickers
    
    Note: Large stickers that cover key details may not be fully restorable.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始处理 {len(files)} 张图片（去贴纸）...")
    return await remove_image_sticker_adapter(logger, files)


@mcp.tool
async def remove_image_text(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of image files to remove text from")]
) -> Annotated[str, "JSON formatted result report with processed image download URLs"]:
    """
    Remove text from images.
    
    Use cases:
    - When removing captions, subtitles, or embedded text from screenshots
    - When cleaning scanned documents or photos that contain unwanted labels
    - When preparing images for reuse without annotations
    
    Note: If text overlaps complex backgrounds, results may vary.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始处理 {len(files)} 张图片（去文字）...")
    return await remove_image_text_adapter(logger, files)

# ==================== 水印工具 ====================

@mcp.tool
async def add_text_watermark(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to add text watermarks to")],
    text: Annotated[str, Field(..., description="Watermark text content", min_length=1)],
    position: Annotated[Literal["topleft", "top", "topright", "left", "center", "right", "bottomleft", "bottom", "bottomright", "diagonal", "reverse-diagonal"], Field(description="Text watermark position")] = "center",
    opacity: Annotated[float, Field(description="Opacity, 0.0-1.0", ge=0.0, le=1.0)] = 1.0,
    range: Annotated[str, Field(description="Page range to apply watermark. Format: '1,3,5-7' for specific pages, '1-10' for range, or empty string for all pages")] = "",
    layout: Annotated[Literal["on", "under"], Field(description="Layout position: on top of content(on) or under content(under)")] = "on",
    font_family: Annotated[Optional[str], Field(description="Font family name, e.g. 'Arial', 'Times New Roman', 'Helvetica'. If not specified, uses system default")] = None,
    font_size: Annotated[Optional[int], Field(description="Font size in points (pt), e.g. 12, 18, 24. If not specified, uses automatic sizing", ge=1)] = None,
    font_color: Annotated[Optional[str], Field(description="Font color, e.g. '#ff0000' for red")] = None
) -> Annotated[str, "JSON formatted result report with text watermarked PDF files"]:
    """
    Add custom text watermarks to PDF documents for branding, copyright protection, or document identification. This tool overlays text on PDF pages with full control over appearance and positioning.
    
    Use cases:
    - When adding company branding or contact information to everyday business documents
    - When marking documents with "DRAFT", "CONFIDENTIAL", or copyright notices for sharing
    - When adding tracking identifiers or version numbers for document management
    - When branding presentation materials or reports before client meetings
    
    Note: This adds visible text overlays to the document. For invisible metadata, consider using document properties instead. To remove watermarks, use remove_watermark tool.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始为 {len(files)} 个PDF文件添加文本水印...")
    
    # 构建操作配置
    extra_params = {
        "text": text,
        "position": position,
        "opacity": opacity,
        "range": range,
        "layout": layout
    }
    
    # 添加可选参数
    if font_family:
        extra_params["font_family"] = font_family
    if font_size:
        extra_params["font_size"] = font_size
    if font_color:
        extra_params["font_color"] = font_color
    
    operation_config = generate_operation_config(
        operation_type="edit",
        edit_type="add_text_watermark",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "文本水印添加完成")
    return result

@mcp.tool
async def add_image_watermark(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to add image watermarks to")],
    image_url: Annotated[str, Field(..., description="Complete URL of the watermark image. Must include protocol (http:// or https://). Supports common formats: JPG, PNG, GIF, BMP, SVG", min_length=1)],
    position: Annotated[Literal["topleft", "top", "topright", "left", "center", "right", "bottomleft", "bottom", "bottomright", "diagonal", "reverse-diagonal"], Field(description="Image watermark position")] = "center",
    opacity: Annotated[float, Field(description="Opacity, 0.0-1.0", ge=0.0, le=1.0)] = 0.7,
    range: Annotated[str, Field(description="Page range to apply watermark. Format: '1,3,5-7' for specific pages, '1-10' for range, or empty string for all pages")] = "",
    layout: Annotated[Literal["on", "under"], Field(description="Layout position: on top of content(on) or under content(under)")] = "on"
) -> Annotated[str, "JSON formatted result report with image watermarked PDF files"]:
    """
    Add image watermarks (logos, stamps, signatures) to PDF documents for professional branding or document authentication. This tool overlays images on PDF pages with precise positioning and transparency control.
    
    Use cases:
    - When branding company documents with logos before sending to external clients or partners
    - When adding official seals or stamps to certificates, licenses, or formal approvals
    - When inserting signature images to authorize documents without physical signing
    - When marking quality control documents with inspection badges or compliance stamps
    
    Note: Image must be accessible via URL. For local images, upload them to a web-accessible location first. To remove image watermarks, use remove_watermark tool.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始为 {len(files)} 个PDF文件添加图片水印...")
    
    # 构建操作配置
    extra_params = {
        "image_url": image_url,
        "position": position,
        "opacity": opacity,
        "range": range,
        "layout": layout
    }
    
    operation_config = generate_operation_config(
        operation_type="edit",
        edit_type="add_image_watermark",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "图片水印添加完成")
    return result

@mcp.tool
async def unlock_pdf(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to decrypt, each must contain password")]
) -> Annotated[str, "JSON formatted result report with decrypted PDF files (password removed)"]:
    """
    Remove password protection from PDF files to make them freely accessible. This tool decrypts password-protected PDFs.
    
    Use cases:
    - When you need to access your own password-protected files but frequently forget the passwords
    - When archiving old company documents that have various passwords from different periods
    - When integrating protected PDFs into automated systems that cannot handle password prompts
    - When consolidating documents from multiple sources that each require different access credentials
    
    Note: Only use this tool on documents you own or have explicit permission to unlock. Original password must be provided in the FileObject.
    
    Related tools: Use protect_pdf to add password protection, or restrict_printing to limit specific permissions.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始解密 {len(files)} 个PDF文件...")
    
    # 构建操作配置
    operation_config = generate_operation_config(
        operation_type="edit",
        edit_type="decrypt"
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF解密完成")
    return result

@mcp.tool
async def protect_pdf(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to encrypt")],
    password: Annotated[str, Field(..., description="New password to set", min_length=1)]
) -> Annotated[str, "JSON formatted result report with password-protected PDF files"]:
    """
    Add password protection to PDF files. This sets a user password required to open and view the PDF document.
    
    Use cases:
    - When sharing sensitive business documents or reports that require access control
    - When sending confidential files via email to prevent unauthorized viewing
    - When distributing internal HR documents or employee information within the organization
    - When complying with industry regulations that require password protection for certain document types
    
    Note: This is different from restrict_printing which allows viewing but restricts specific actions like printing. Use protect_pdf to prevent unauthorized access, use restrict_printing to control usage permissions.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始加密 {len(files)} 个PDF文件...")
    
    # 构建操作配置
    extra_params = {
        "password": password
    }
    
    operation_config = generate_operation_config(
        operation_type="edit",
        edit_type="encrypt",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF加密完成")
    return result

@mcp.tool
async def split_pdf(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to split")],
    split_type: Annotated[Literal["every", "page", "bookmark"], Field(..., description="Split type: 'every' (split each page into a separate file), 'page' (split by page ranges), or 'bookmark' (split by PDF bookmarks/outlines/table of contents/headings)")],
    pages: Annotated[str, Field(description="Page ranges to extract when split_type='page'. Format: '1,3,5-7' for specific pages, '1-10' for range. Leave empty for all pages. Required and only valid when split_type is 'page'")] = "",
    merge_all: Annotated[Literal[0, 1], Field(description="Whether to merge results into a single PDF file: 1=yes, 0=no (will return a zip package of multiple files). Only valid when split_type is 'page'")] = 0
) -> Annotated[str, "JSON formatted result report with split PDF files or zip package"]:
    """
    Split PDF documents to extract specific pages or page ranges. You can split by individual pages, page ranges, or document bookmarks.
    
    Use cases:
    - When you need to share only specific pages from a large document via email
    - When creating samples or previews from larger documents for clients or colleagues
    - When removing confidential sections before sharing documents externally
    - When organizing documents by extracting relevant sections for different purposes
    
    Note: This extracts and keeps specified pages. For permanently removing unwanted pages from the original document, use delete_pdf_pages instead.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始拆分 {len(files)} 个PDF文件...")
    
    # 构建操作配置
    extra_params = {
        "split_type": split_type,
        "pages": pages,
        "merge_all": merge_all
    }
    
    operation_config = generate_operation_config(
        operation_type="edit",
        edit_type="split",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF拆分完成")
    return result

@mcp.tool
async def rotate_pdf(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to rotate")],
    angle: Annotated[Literal[90, 180, 270, -90], Field(description="Rotation angle in degrees. 90=clockwise 90°, -90=counter-clockwise 90°, 180=flip upside down, 270=counter-clockwise 90° (same as -90)")] = 90,
    pages: Annotated[str, Field(description="Page range to rotate. Use 'all' for all pages, or specify like '1-3', '1,3,5'")] = "all",
    rotates: Annotated[Optional[List[dict]], Field(description="Advanced option: List of rotation operations for different page ranges. If provided, overrides angle/pages parameters. Each dict must contain: {'angle': 90|180|270|-90, 'pages': 'all'|'1-3'|...}. Example: [{'angle': 90, 'pages': '1-3'}, {'angle': 180, 'pages': '5,7'}]")] = None
) -> Annotated[str, "JSON formatted result report with rotated PDF files"]:
    """
    Rotate PDF pages by specified angles to correct orientation or adjust viewing angle.
    
    Simple usage: Just provide angle (90/180/270/-90) and pages ('all' or '1-3') parameters.
    Advanced usage: Use rotates parameter for applying different rotations to different page ranges.
    
    Use cases:
    - When you receive scanned documents where some pages are sideways or upside down
    - When combining documents with mixed orientations that need to be standardized
    - When preparing documents for specific printing or viewing requirements
    - When fixing scanning errors where pages were fed incorrectly into the scanner
    
    Simple example: angle=90, pages='all' rotates all pages clockwise 90 degrees.
    Advanced example: rotates=[{"angle": 90, "pages": "1-3"}, {"angle": 180, "pages": "5,7"}]
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始旋转 {len(files)} 个PDF文件...")
    
    # 如果没有提供 rotates，从简单参数构建
    if rotates is None:
        rotates = [{"angle": angle, "pages": pages}]
    
    # 构建操作配置
    extra_params = {
        "rotates": rotates
    }
    
    operation_config = generate_operation_config(
        operation_type="edit",
        edit_type="rotate",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF旋转完成")
    return result

# ==================== AI功能工具 ====================

@mcp.tool
async def translate_pdf(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to translate")],
    target: Annotated[Literal["ar", "bg", "cz", "da", "de", "el", "en", "es", "fi", "fr", "hbs", "hi", "hu", "id", "it", "ja", "ko", "ms", "nl", "no", "pl", "pt", "ru", "sl", "sv", "th", "tr", "vi", "zh", "zh-tw"], Field(..., description="Target language. Must be specified")],
    source: Annotated[Literal["auto", "ar", "bg", "cz", "da", "de", "el", "en", "es", "fi", "fr", "hbs", "hi", "hu", "id", "it", "ja", "ko", "ms", "nl", "no", "pl", "pt", "ru", "sl", "sv", "th", "tr", "vi", "zh", "zh-tw"], Field(description="Source language. Supports 'auto' for automatic detection")] = "auto",
    output_type: Annotated[Literal["mono", "dual"], Field(description="Output type: 'mono' for target language only, 'dual' for source/target bilingual output")] = "mono"
) -> Annotated[str, "JSON formatted result report with translated PDF files in target language"]:
    """
    Translate only the text in a PDF file into a specified target language and output a new PDF file. All non-text elements (such as images, tables, and layout) will remain unchanged.
    
    Use cases:
    - When expanding business to international markets and need localized documentation
    - When submitting research papers to foreign journals or conferences
    - When collaborating with overseas partners who require documents in their native language
    - When complying with local regulations that mandate documents in specific languages
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始翻译 {len(files)} 个PDF文件...")
    
    # 构建操作配置
    extra_params = {
        "source": source,
        "target": target,
        "output_type": output_type
    }
    
    operation_config = generate_operation_config(
        operation_type="translate",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF翻译完成")
    return result

@mcp.tool
async def ocr_document(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of files to be recognized. Supports: PDF, PPT, PPTX, XLS, XLSX, DOC, DOCX, JPEG, JPG, PNG, GIF, BMP")],
    format: Annotated[Literal["pdf", "docx", "pptx", "xlsx", "txt"], Field(description="Output format, supports pdf/docx/pptx/xlsx/txt, default is pdf")] = "pdf",
    language: Annotated[str, Field(description="Languages/types to recognize, separated by commas. Available options include: English, ChinesePRC, ChineseTraditional, Japanese, Korean, French, German, Spanish, Portuguese, Russian, Arabic, Digits, Symbols. Example: 'English,Digits,ChinesePRC'")] = "English,Digits,ChinesePRC"
) -> Annotated[str, "JSON formatted result report with OCR-processed files in specified format"]:
    """
    Perform OCR (Optical Character Recognition) on documents and images to recognize and extract text into various output formats.

    Supported input file types:
    - Documents: PDF, PPT, PPTX, XLS, XLSX, DOC, DOCX
    - Images: JPEG, JPG, PNG, GIF, BMP
    
    Supported output formats:
    - Documents: PDF, DOCX, PPTX, XLSX
    - Plain Text: TXT
    
    Use cases:
    - When you receive scanned documents that need to be edited or have text copied from them
    - When converting image-based PDFs to searchable and editable text documents
    - When processing printed receipts, invoices, or forms for digital record keeping
    - When digitizing handwritten notes or historical documents for database entry
    
    Note: Use this tool for scanned documents, image-based PDFs, or image files where text needs to be recognized. For regular PDF text extraction, use convert_document PDF-to-TXT conversion instead.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始OCR识别 {len(files)} 个文件...")
    
    # 构建操作配置
    extra_params = {
        "format": format,
        "language": language
    }
    
    operation_config = generate_operation_config(
        operation_type="ocr",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "OCR识别完成")
    return result

@mcp.tool
async def summarize_document(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of files to summarize")],
    prompt: Annotated[str, Field(..., description="User's requirement or instruction for the summary", min_length=1)],
    language: Annotated[Literal["af","am","ar","as","az","ba","be","bg","bn","bo","br","bs","ca","cs","cy","da","de","el","en","es","et","eu","fa","fi","fo","fr","gl","gu","ha","haw","he","hi","hr","ht","hu","hy","id","is","it","ja","jw","ka","kk","km","kn","ko","la","lb","ln","lo","lt","lv","mg","mi","mk","ml","mn","mr","ms","mt","my","ne","nl","nn","no","oc","pa","pl","ps","pt","ro","ru","sa","sd","si","sk","sl","sn","so","sq","sr","su","sv","sw","ta","te","tg","th","tk","tl","tr","tt","uk","ur","uz","vi","yi","yo","zh"], Field(..., description="The language in which the summary should be generated")]
) -> Annotated[str, "JSON formatted result report with document summary in the 'summary' field"]:
    """
    Summarize the content of documents and generate a concise abstract based on the user's prompt. The tool extracts and condenses the main ideas or information from the document(s) according to the user's requirements.
    
    Use cases:
    - When you need quick overviews of lengthy reports or documents for meetings or reviews
    - When creating executive summaries from detailed business reports or proposals
    - When processing multiple documents and need to extract key information quickly
    - When preparing meeting agendas or abstracts based on extensive documentation
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始摘要 {len(files)} 个文件...")
    
    # 构建操作配置
    extra_params = {
        "prompt": prompt,
        "language": language
    }
    
    operation_config = generate_operation_config(
        operation_type="summarize",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "文档摘要完成")
    return result

@mcp.tool
async def create_pdf(
    ctx: Context,
    prompt: Annotated[str, Field(..., description="A text-only description or instruction of what PDF content to generate", min_length=1)],
    filename: Annotated[str, Field(..., description="The filename for the generated PDF", min_length=1)],
    language: Annotated[Literal["zh", "en", "de", "es", "fr", "jp", "pt", "tw", "ar", "cz", "dk", "fi", "gr", "hu", "it", "nl", "no", "pl", "se", "tr"], Field(..., description="The language for the generated PDF content")],
    enable_web_search: Annotated[bool, Field(description="Whether to enable web search to gather additional information for content generation")] = False,
    use_advanced_model: Annotated[bool, Field(description="Whether to use advanced AI model for higher quality content generation. Advanced model produces better results but may take longer")] = False
) -> Annotated[str, "JSON formatted result report with generated PDF download URL and file information"]:
    """
    Generate PDF documents from text-only instructions or descriptions. The tool creates PDFs based on written prompts such as 'create a business report', 'generate meeting minutes', etc. Only accepts plain text input - no file uploads or multimedia content supported.
    
    Use cases:
    - When you need to quickly create professional documents like reports, proposals, or letters
    - When generating meeting minutes, project plans, or business documentation from written notes
    - When creating standardized documents or templates for repeated business use
    - When producing training materials or documentation based on specific content requirements
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始根据提示生成PDF：{prompt[:50]}...")
    
    # 使用PDF创建适配器
    result = await create_pdf_adapter(logger, prompt, filename, language, enable_web_search, use_advanced_model)
    
    await logger.log("info", "PDF生成完成")
    return result

@mcp.tool
async def create_word(
    ctx: Context,
    prompt: Annotated[str, Field(..., description="A text-only description or instruction of what Word document content to generate", min_length=1)],
    filename: Annotated[str, Field(..., description="The filename for the generated Word document", min_length=1)],
    language: Annotated[Literal["zh", "en", "de", "es", "fr", "jp", "pt", "tw", "ar", "cz", "dk", "fi", "gr", "hu", "it", "nl", "no", "pl", "se", "tr"], Field(..., description="The language for the generated Word document content")],
    enable_web_search: Annotated[bool, Field(description="Whether to enable web search to gather additional information for content generation")] = False,
    use_advanced_model: Annotated[bool, Field(description="Whether to use advanced AI model for higher quality content generation. Advanced model produces better results but may take longer")] = False
) -> Annotated[str, "JSON formatted result report with generated Word document download URL and file information"]:
    """
    Generate editable Word documents from text descriptions. This tool creates DOCX files with structured content, formatting, and layouts based on your written instructions.
    
    Use cases:
    - When you need collaborative documents that team members can edit and comment on
    - When creating document templates that will be customized for different clients or projects
    - When producing draft documents that require extensive revision and track changes
    - When generating structured documents with complex formatting for further development
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始根据提示生成Word文档：{prompt[:50]}...")
    
    # 使用Word创建适配器
    result = await create_word_adapter(logger, prompt, filename, language, enable_web_search, use_advanced_model)
    
    await logger.log("info", "Word文档生成完成")
    return result

@mcp.tool
async def create_excel(
    ctx: Context,
    prompt: Annotated[str, Field(..., description="A text-only description or instruction of what Excel document content to generate", min_length=1)],
    filename: Annotated[str, Field(..., description="The filename for the generated Excel document", min_length=1)],
    language: Annotated[Literal["zh", "en", "de", "es", "fr", "jp", "pt", "tw", "ar", "cz", "dk", "fi", "gr", "hu", "it", "nl", "no", "pl", "se", "tr"], Field(..., description="The language for the generated Excel document content")],
    enable_web_search: Annotated[bool, Field(description="Whether to enable web search to gather additional information for content generation")] = False,
    use_advanced_model: Annotated[bool, Field(description="Whether to use advanced AI model for higher quality content generation. Advanced model produces better results but may take longer")] = False
) -> Annotated[str, "JSON formatted result report with generated Excel document download URL and file information"]:
    """
    Generate Excel spreadsheets with data tables, formulas, and charts from text descriptions. This tool creates XLSX files optimized for data analysis and calculations.
    
    Use cases:
    - When you need data analysis spreadsheets with formulas and calculations for financial modeling
    - When creating inventory tracking systems or budget templates from written specifications
    - When generating charts and graphs for presentations based on data requirements
    - When producing automated calculation templates for recurring business processes
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始根据提示生成Excel文档：{prompt[:50]}...")
    
    # 使用Excel创建适配器
    result = await create_excel_adapter(logger, prompt, filename, language, enable_web_search, use_advanced_model)
    
    await logger.log("info", "Excel文档生成完成")
    return result

# ==================== 专业工具 ====================

@mcp.tool
async def remove_margin(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to remove margins from")]
) -> Annotated[str, "JSON formatted result report with margin-cropped PDF files"]:
    """
    Remove white margins and empty spaces from PDF pages by automatically cropping to content boundaries. This tool intelligently detects and removes unnecessary white space around the actual document content.
    
    Use cases:
    - When scanned documents have excessive white borders that waste screen space on mobile devices
    - When preparing documents for printing on different paper sizes to maximize content area
    - When optimizing PDFs for e-readers or tablets where screen real estate is limited
    - When reducing file sizes by eliminating unnecessary white space around content
    
    Note: This tool crops white space, not content. All text, images, and graphics are preserved. For resizing page dimensions, use resize_pdf instead.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始去除 {len(files)} 个PDF文件的白边...")
    
    # 构建操作配置
    operation_config = generate_operation_config(
        operation_type="edit",
        edit_type="remove_margin"
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF白边去除完成")
    return result

@mcp.tool
async def extract_images(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to extract images from")],
    format: Annotated[Literal["bmp", "png", "gif", "tif", "jpg"], Field(description="Extracted image format")] = "png"
) -> Annotated[str, "JSON formatted result report with extracted image files in zip package"]:
    """
    Extract embedded image resources from PDF files. This tool finds and extracts actual image files (photos, logos, graphics) that are embedded within the PDF document, saving them as separate image files.
    
    Use cases:
    - When updating websites or marketing materials and need to extract logos or graphics from PDFs
    - When building presentations and need to reuse images, charts, or diagrams from existing documents
    - When creating marketing materials and need product photos or graphics from PDF catalogs
    - When preparing reports and need to extract specific images or charts from source documents
    
    Note: This is different from convert_document PDF-to-image conversion, which converts entire PDF pages into image format. Use convert_document if you want to convert PDF pages to images, use extract_images if you want to get embedded pictures from the PDF.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始从 {len(files)} 个PDF文件提取图片...")
    
    # 构建操作配置
    extra_params = {
        "format": format
    }
    
    operation_config = generate_operation_config(
        operation_type="edit",
        edit_type="extract_image",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "图片提取完成")
    return result

@mcp.tool
async def flatten_pdf(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to flatten")]
) -> Annotated[str, "JSON formatted result report with flattened PDF files (non-editable content)"]:
    """
    Flatten PDF files (convert editable elements such as form fields, annotations, and layers into non-editable static content). This preserves the visual appearance while making interactive elements non-functional.
    
    Use cases:
    - When finalizing contract forms that should no longer be editable after completion
    - When archiving interactive documents where form functionality is no longer needed
    - When preparing PDFs for printing systems that don't handle form fields properly
    - When securing documents by preventing further modifications to interactive elements
    
    Note: For converting text characters to vector curves/outlines, use curve_pdf instead. Flattening affects form fields and annotations, while curving affects text editability.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始展平 {len(files)} 个PDF文件...")
    
    # 构建操作配置
    operation_config = generate_operation_config(
        operation_type="convert",
        format_value="flatten-pdf"
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF展平完成")
    return result

@mcp.tool
async def repair_pdf(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to repair")]
) -> Annotated[str, "JSON formatted result report with repaired PDF files"]:
    """
    Repair corrupted or damaged PDF files to restore readability and functionality.
    
    Use cases:
    - When important documents become corrupted during file transfer or storage system failures
    - When legacy PDFs from old systems no longer open in modern PDF viewers
    - When recovering critical business documents from damaged storage media
    - When fixing PDFs that display incorrectly due to missing fonts or broken formatting
    
    Note: This tool attempts to fix structural corruption and basic display issues. It cannot recover completely destroyed content or fix complex formatting problems. For removing unwanted elements like watermarks, use remove_watermark instead.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始修复 {len(files)} 个PDF文件...")
    
    # 构建操作配置
    operation_config = generate_operation_config(
        operation_type="convert",
        format_value="pdf-repair"
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF修复完成")
    return result

@mcp.tool
async def curve_pdf(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to convert to curves")]
) -> Annotated[str, "JSON formatted result report with curve-converted PDF files"]:
    """
    Convert PDF text characters to vector curves (outlines), making text unselectable and unsearchable while maintaining exact visual appearance. This is commonly used for font protection and preventing text extraction.
    
    Use cases:
    - When sending design files to printing companies that require font outlines for accurate reproduction
    - When protecting proprietary fonts from being extracted or copied by competitors
    - When creating final artwork files where text should not be accidentally edited
    - When preparing documents for professional publication where font licensing is a concern
    
    Note: This specifically converts text to curves. For making form fields and annotations non-editable, use flatten_pdf instead.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始转曲 {len(files)} 个PDF文件...")
    
    # 构建操作配置
    operation_config = generate_operation_config(
        operation_type="convert",
        format_value="curve-pdf"
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF转曲完成")
    return result

@mcp.tool
async def double_layer_pdf(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to convert to double layer")],
    language: Annotated[str, Field(..., description="Language of the text in the document using ISO 639-1 standard language codes (e.g., 'en' for English, 'zh' for Chinese, 'ja' for Japanese, 'es' for Spanish)", min_length=2, max_length=2)]
) -> Annotated[str, "JSON formatted result report with double-layer PDF files"]:
    """
    Convert scanned PDF to double-layer PDF, adding a text layer beneath the original image while preserving exact visual appearance. This makes scanned documents searchable and selectable without changing how they look.
    
    Use cases:
    - When digitizing historical documents for archives that need to be searchable but preserve original appearance
    - When processing scanned contracts or legal documents that must remain visually identical but searchable
    - When creating accessible versions of image-based PDFs for screen readers and search engines
    - When building digital libraries where scanned books need text search functionality
    
    Note: This adds a text layer to image-based PDFs. For extracting text from scanned documents into editable formats, use ocr_document instead.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始转换 {len(files)} 个PDF文件为双层PDF...")
    
    # 构建操作配置
    extra_params = {
        "language": language
    }
    
    operation_config = generate_operation_config(
        operation_type="convert",
        format_value="double-pdf",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF双层转换完成")
    return result

@mcp.tool
async def delete_pdf_pages(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to delete pages from")],
    range: Annotated[str, Field(..., description="Page range to delete. Format: '1,3,5-7' for specific pages and ranges, '1-10' for continuous range, '5' for single page", min_length=1)]
) -> Annotated[str, "JSON formatted result report with page-deleted PDF files"]:
    """
    Delete unwanted pages from PDF files. Use this when you want to permanently remove specific pages from the document.
    
    Use cases:
    - When scanned documents contain blank pages that waste storage space and confuse readers
    - When removing confidential sections from reports before sharing with external parties
    - When cleaning up multi-page documents that have duplicate or error pages from scanning
    - When preparing documents for printing where certain pages should not be included
    
    Note: This is different from split_pdf which extracts and keeps wanted pages. Use delete_pdf_pages when you know which pages to remove, use split_pdf when you know which pages to keep.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始删除 {len(files)} 个PDF文件的指定页面...")
    
    # 构建操作配置
    extra_params = {
        "range": range
    }
    
    operation_config = generate_operation_config(
        operation_type="edit",
        edit_type="pdf-delete-page",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF页面删除完成")
    return result

@mcp.tool
async def restrict_printing(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to restrict printing")],
    password: Annotated[str, Field(..., description="New permission password to set", min_length=1)]
) -> Annotated[str, "JSON formatted result report with print-restricted PDF files"]:
    """
    Restrict PDF printing permissions while allowing viewing. This sets an owner password that prevents users from printing the document.
    
    Use cases:
    - When sharing copyrighted training materials that should be viewed but not printed for distribution
    - When sending confidential business plans for review where hard copies pose security risks
    - When distributing digital-only content that loses value if printed and shared physically
    - When complying with licensing agreements that restrict printing of certain materials
    
    Note: This is different from protect_pdf which requires a password to open the document. Use restrict_printing to control usage permissions while allowing viewing, use protect_pdf to prevent unauthorized access entirely.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始限制 {len(files)} 个PDF文件的打印权限...")
    
    # 构建操作配置
    extra_params = {
        "password": password,
        "provider": "printpermission"
    }
    
    operation_config = generate_operation_config(
        operation_type="edit",
        edit_type="encrypt",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF打印权限限制完成")
    return result

@mcp.tool
async def resize_pdf(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to resize")],
    page_size: Annotated[Optional[str], Field(description="Target page size. Standard sizes: 'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'letter', 'legal', 'tabloid'. Custom size: 'width,height' in points (e.g., '595,842' for A4). If not set, page size will not be changed")] = None,
    resolution: Annotated[Optional[int], Field(description="Image resolution (dpi), e.g., 72. If not set, resolution will not be changed", ge=1)] = None
) -> Annotated[str, "JSON formatted result report with resized PDF files"]:
    """
    Resize PDF pages. You can specify the target page size (a0/a1/a2/a3/a4/a5/a6/letter) and/or the image resolution (dpi, e.g., 72). If not set, the corresponding property will not be changed.
    
    Use cases:
    - When preparing documents for printing on specific paper sizes required by clients or printers
    - When optimizing PDFs for mobile viewing by adjusting page dimensions and image quality
    - When meeting publication requirements that specify exact page dimensions or resolution
    - When standardizing document collections that have mixed page sizes from different sources
    
    Note: This changes the actual page dimensions and image resolution. For removing white space around content without changing page size, use remove_margin instead.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始调整 {len(files)} 个PDF文件的大小...")
    
    # 构建操作配置
    extra_params = {}
    if page_size:
        extra_params["page_size"] = page_size
    if resolution:
        extra_params["resolution"] = resolution
    
    operation_config = generate_operation_config(
        operation_type="convert",
        format_value="resize-pdf",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF大小调整完成")
    return result

@mcp.tool
async def replace_text(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to replace text in")],
    old_text: Annotated[str, Field(..., description="The text to be replaced or deleted", min_length=1)],
    new_text: Annotated[str, Field(description="The replacement text. If empty, the old_text will be deleted")]
) -> Annotated[str, "JSON formatted result report with text-modified PDF files"]:
    """
    Replace, edit, or delete regular document text content in PDF files. Use this for modifying normal text within the document body, such as correcting names, dates, or other content. When new_text is empty, the specified text will be permanently deleted.
    
    Use cases:
    - When correcting typos, dates, or contact information in existing documents
    - When updating company names, addresses, or other details across multiple documents
    - When removing sensitive information like phone numbers or confidential data before sharing
    - When standardizing terminology or formatting across a collection of documents
    
    Note: This is for regular document text content only. For removing watermarks, security overlays, or branding elements, use remove_watermark instead.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始替换 {len(files)} 个PDF文件中的文本...")
    
    # 构建操作配置
    extra_params = {
        "old_text": old_text,
        "new_text": new_text
    }
    
    operation_config = generate_operation_config(
        operation_type="convert",
        format_value="pdf-replace-text",
        extra_params=extra_params
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "文本替换完成")
    return result

@mcp.tool
async def extract_pdf_tables(
    ctx: Context,
    files: Annotated[List[FileObject], Field(..., description="List of PDF files to extract tables from")]
) -> Annotated[str, "JSON formatted result report with extracted table data in Excel format"]:
    """
    Extract all tables from PDF files and convert them to Excel format. This tool identifies table structures within PDF documents and converts them to structured Excel spreadsheets, preserving the original table layout and data.
    
    Use cases:
    - When analyzing financial reports where data needs to be processed in spreadsheet applications
    - When converting research paper tables into editable format for meta-analysis or data compilation
    - When processing invoices or receipts where tabular data needs to be imported into accounting systems
    - When extracting survey results or form data from PDFs for statistical analysis
    
    Note: This tool is specifically designed for table extraction. For general PDF to Excel conversion, use convert_document with format='xlsx' instead.
    """
    logger = Logger(ctx, collect_info=False)
    await logger.log("info", f"开始从 {len(files)} 个PDF文件中提取表格...")
    
    # 构建操作配置
    operation_config = generate_operation_config(
        operation_type="convert",
        format_value="pdf-extract-table"
    )
    
    # 调用适配器
    result = await process_tool_call_adapter(logger, files, operation_config)
    
    await logger.log("info", "PDF表格提取完成")
    return result

# ==================== 启动逻辑 ====================

def main():
    """应用主入口"""
    # 打印版本号
    try:
        import importlib.metadata
        version = importlib.metadata.version("lightpdf-aipdf-mcp")
        print(f"LightPDF AI-PDF FastMCP Server v{version}", file=sys.stderr)
    except Exception:
        print("LightPDF AI-PDF FastMCP Server (FastMCP版本)", file=sys.stderr)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="LightPDF AI-PDF FastMCP Server")
    # 重要：默认应为 stdio（用于 MCP 客户端）。只有显式指定端口时才启动 HTTP/SSE 服务。
    parser.add_argument("-p", "--port", type=int, default=0, help="指定服务器端口号（>0 时启动 HTTP；配合 --sse 启动 SSE）。默认 0 表示 stdio 模式")
    parser.add_argument("--sse", action="store_true", help="使用SSE传输模式（需要配合--port）")
    args = parser.parse_args()
    
    if args.port and args.port > 0:
        if args.sse:
            print(f"启动SSE服务器，端口号：{args.port}", file=sys.stderr)
            mcp.run(transport="sse", host="0.0.0.0", port=args.port)
        else:
            print(f"启动HTTP服务器，端口号：{args.port}", file=sys.stderr)
            mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port)
    else:
        print("启动stdio服务器", file=sys.stderr)
        mcp.run()  # 默认使用stdio

def cli_main():
    try:
        main()
    except KeyboardInterrupt:
        print("服务器被用户中断", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"服务器发生错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    cli_main() 