"""PDF文档转换模块"""
import os
import httpx

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Set

from ..utils.common import BaseResult, Logger, FileHandler, BaseApiClient, require_api_key

class InputFormat(str, Enum):
    """支持的输入文件格式"""
    PDF = "pdf"
    WORD = "docx"
    EXCEL = "xlsx"
    PPT = "pptx"
    JPG = "jpg"
    PNG = "png"
    GIF = "gif"
    BMP = "bmp"
    CAD = "dwg"
    DXF = "dxf"
    CAJ = "caj"
    OFD = "ofd"
    HTML = "html"
    MARKDOWN = "md"
    RTF = "rtf"
    ODG = "odg"  # OpenDocument Graphics
    ODS = "ods"  # OpenDocument Spreadsheet
    ODP = "odp"  # OpenDocument Presentation
    ODT = "odt"  # OpenDocument Text
    TXT = "txt"  # Plain Text
    TEX = "tex"  # LaTeX
    HEIC = "heic"  # High Efficiency Image Container
    SVG = "svg"  # Scalable Vector Graphics
    TIFF = "tiff"  # Tagged Image File Format
    WEBP = "webp"  # WebP Image Format
    EPS = "eps"  # Encapsulated PostScript
    EPUB = "epub"  # eBook
    MOBI = "mobi"  # eBook
    AZW3 = "azw3"  # Amazon Kindle eBook format

class OutputFormat(str, Enum):
    """支持的输出文件格式"""
    PDF = "pdf"
    WORD = "docx"
    DOC = "doc"
    EXCEL = "xlsx"
    XLS = "xls"
    PPT = "pptx"
    PPT_LEGACY = "ppt"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    BMP = "bmp"
    WMF = "wmf"
    EMF = "emf"
    WEBP = "webp"  # WebP Image Format
    SVG = "svg"  # Scalable Vector Graphics
    HTML = "html"
    TEXT = "txt"
    EPUB = "epub"
    CSV = "csv"
    MARKDOWN = "md"  # Markdown
    RTF = "rtf"  # Rich Text Format
    TEX = "tex"  # LaTeX
    TIFF = "tiff"  # Tagged Image File Format
    TIF = "tif"  # TIFF alias
    ODT = "odt"
    AZW3 = "azw3"  # Amazon Kindle eBook format

# 文件扩展名到输入格式的映射
INPUT_EXTENSIONS = {
    ".pdf": InputFormat.PDF,
    ".docx": InputFormat.WORD,
    ".doc": InputFormat.WORD,
    ".xlsx": InputFormat.EXCEL,
    ".xls": InputFormat.EXCEL,  # Excel旧格式（与xlsx统一处理为EXCEL）
    ".pptx": InputFormat.PPT,
    ".ppt": InputFormat.PPT,
    ".jpg": InputFormat.JPG,
    ".jpeg": InputFormat.JPG,  # JPEG和JPG统一使用JPG格式
    ".png": InputFormat.PNG,
    ".gif": InputFormat.GIF,
    ".bmp": InputFormat.BMP,
    ".dwg": InputFormat.CAD,
    ".dxf": InputFormat.DXF,
    ".caj": InputFormat.CAJ,
    ".ofd": InputFormat.OFD,
    ".html": InputFormat.HTML,
    ".htm": InputFormat.HTML,
    ".md": InputFormat.MARKDOWN,
    ".rtf": InputFormat.RTF,
    ".odg": InputFormat.ODG,
    ".ods": InputFormat.ODS,
    ".odp": InputFormat.ODP,
    ".odt": InputFormat.ODT,
    ".txt": InputFormat.TXT,
    ".tex": InputFormat.TEX,
    ".heic": InputFormat.HEIC,
    ".svg": InputFormat.SVG,
    ".tiff": InputFormat.TIFF,
    ".tif": InputFormat.TIFF,  # TIFF的另一种扩展名
    ".webp": InputFormat.WEBP,
    ".eps": InputFormat.EPS,
    ".epub": InputFormat.EPUB,
    ".mobi": InputFormat.MOBI,
    ".azw3": InputFormat.AZW3,
}

# 输入格式到可用输出格式的映射
FORMAT_CONVERSION_MAP = {
    InputFormat.PDF: {
        OutputFormat.WORD,   # PDF转Word
        OutputFormat.DOC,    # PDF转DOC
        OutputFormat.EXCEL,  # PDF转Excel
        OutputFormat.XLS,    # PDF转XLS
        OutputFormat.PPT,    # PDF转PPT
        OutputFormat.PPT_LEGACY,  # PDF转PPT
        OutputFormat.JPG,    # PDF转JPG
        OutputFormat.JPEG,   # PDF转JPEG
        OutputFormat.PNG,    # PDF转PNG
        OutputFormat.GIF,    # PDF转GIF
        OutputFormat.BMP,    # PDF转BMP
        OutputFormat.WMF,    # PDF转WMF
        OutputFormat.EMF,    # PDF转EMF
        OutputFormat.SVG,    # PDF转SVG
        OutputFormat.TIFF,   # PDF转TIFF
        OutputFormat.TIF,    # PDF转TIF
        OutputFormat.HTML,   # PDF转HTML
        OutputFormat.TEXT,   # PDF转文本
        OutputFormat.EPUB,   # PDF转EPUB
        OutputFormat.CSV,    # PDF转CSV
        OutputFormat.MARKDOWN,  # PDF转Markdown
        OutputFormat.RTF,    # PDF转RTF
        OutputFormat.TEX,    # PDF转LaTeX
        OutputFormat.AZW3,   # PDF转AZW3
        OutputFormat.ODT,    # PDF转ODT
    },
    InputFormat.WORD: {OutputFormat.PDF},    # Word转PDF（含doc/docx）
    InputFormat.EXCEL: {OutputFormat.PDF},   # Excel转PDF（含xls/xlsx）
    InputFormat.PPT: {OutputFormat.PDF},     # PPT转PDF（含ppt/pptx）
    InputFormat.JPG: {OutputFormat.PDF},     # JPG/JPEG转PDF (统一处理)
    InputFormat.PNG: {
        OutputFormat.PDF,    # PNG转PDF
        OutputFormat.WEBP,   # PNG转WEBP (用户要求)
    },
    InputFormat.GIF: {OutputFormat.PDF},     # GIF转PDF
    InputFormat.BMP: {OutputFormat.PDF},     # BMP转PDF
    InputFormat.CAD: {OutputFormat.PDF},     # CAD转PDF
    InputFormat.DXF: {OutputFormat.PDF},     # DXF转PDF
    InputFormat.CAJ: {OutputFormat.PDF},     # CAJ转PDF
    InputFormat.OFD: {OutputFormat.PDF},     # OFD转PDF
    InputFormat.HTML: {OutputFormat.PDF},    # HTML转PDF
    # 新增格式转换支持
    InputFormat.MARKDOWN: {OutputFormat.PDF},  # Markdown转PDF
    InputFormat.RTF: {OutputFormat.PDF},       # RTF转PDF
    InputFormat.ODG: {OutputFormat.PDF},       # ODG转PDF
    InputFormat.ODS: {OutputFormat.PDF},       # ODS转PDF
    InputFormat.ODP: {OutputFormat.PDF},       # ODP转PDF
    InputFormat.ODT: {OutputFormat.PDF},       # ODT转PDF
    InputFormat.TXT: {OutputFormat.PDF},       # TXT转PDF
    InputFormat.TEX: {OutputFormat.PDF},    # TEX转PDF（通过provider参数控制输出格式）
    InputFormat.HEIC: {
        OutputFormat.PDF,    # HEIC转PDF
        OutputFormat.JPG,    # HEIC转JPG (用户要求)
        OutputFormat.JPEG,   # HEIC转JPEG (用户要求)
        OutputFormat.PNG,    # HEIC转PNG (用户要求)
    },
    InputFormat.SVG: {OutputFormat.PDF},       # SVG转PDF
    InputFormat.TIFF: {OutputFormat.PDF},      # TIFF转PDF
    InputFormat.WEBP: {
        OutputFormat.PDF,    # WEBP转PDF
        OutputFormat.PNG,    # WEBP转PNG (用户要求)
    },
    InputFormat.EPS: {OutputFormat.PDF},       # EPS转PDF
    InputFormat.EPUB: {OutputFormat.PDF},      # EPUB转PDF
    InputFormat.MOBI: {OutputFormat.PDF},      # MOBI转PDF
    InputFormat.AZW3: {OutputFormat.PDF},      # AZW3转PDF
}

# 扩展FileHandler类的方法
def get_input_format(file_path: str) -> Optional[InputFormat]:
    """根据文件路径获取输入格式"""
    ext = FileHandler.get_file_extension(file_path)
    return INPUT_EXTENSIONS.get(ext)

def get_available_output_formats(input_format: InputFormat) -> Set[OutputFormat]:
    """获取指定输入格式支持的输出格式"""
    return FORMAT_CONVERSION_MAP.get(input_format, set())

# 为FileHandler类注入方法
FileHandler.get_input_format = staticmethod(get_input_format)
FileHandler.get_available_output_formats = staticmethod(get_available_output_formats)

@dataclass
class ConversionResult(BaseResult):
    """转换结果数据类"""
    pass

class Converter(BaseApiClient):
    """PDF文档转换器"""
    def __init__(self, logger: Logger, file_handler: FileHandler):
        super().__init__(logger, file_handler)
        self.api_base_url = f"https://{self.api_endpoint}/tasks/document/conversion"
        self.api_wkhtmltopdf_url = f"https://{self.api_endpoint}/tasks/document/wkhtmltopdf"

    async def add_page_numbers(self, file_path: str, start_num: int = 1, position: str = "5", margin: int = 30, password: str = None, original_name: Optional[str] = None) -> ConversionResult:
        """为PDF文档添加页码
        
        Args:
            file_path: 要添加页码的PDF文件路径
            start_num: 起始页码，整数类型，默认为1
            position: 页码显示位置，字符串类型，可选值1-6（左上/上中/右上/左下/下中/右下），默认为5（下中）
            margin: 页码显示的边距，整数类型，可选值10/30/60，默认为30
            password: 文档密码，如果文档受密码保护，则需要提供（可选）
            original_name: 原始文件名（可选）
            
        Returns:
            ConversionResult: 转换结果
        """
        # 验证输入文件是否为PDF
        input_format = self.file_handler.get_input_format(file_path)
        if input_format != InputFormat.PDF:
            await self.logger.error(f"添加页码功能仅支持PDF文件，当前文件格式为: {self.file_handler.get_file_extension(file_path)}")
            return ConversionResult(success=False, file_path=file_path, error_message="添加页码功能仅支持PDF文件", original_name=original_name)
        
        # 验证参数
        valid_positions = {"1", "2", "3", "4", "5", "6"}
        valid_margins = {10, 30, 60}
        
        # 验证position参数
        if position not in valid_positions:
            error_msg = f"无效的页码位置值: {position}。有效值为: 1(左上), 2(上中), 3(右上), 4(左下), 5(下中), 6(右下)"
            await self.logger.error(error_msg)
            return ConversionResult(success=False, file_path=file_path, error_message=error_msg, original_name=original_name)
        
        # 验证margin参数
        if margin not in valid_margins:
            error_msg = f"无效的页码边距值: {margin}。有效值为: 10, 30, 60"
            await self.logger.error(error_msg)
            return ConversionResult(success=False, file_path=file_path, error_message=error_msg, original_name=original_name)
        
        # 验证start_num是否为正整数
        if not isinstance(start_num, int) or start_num < 1:
            error_msg = f"起始页码必须是正整数，当前值为: {start_num}"
            await self.logger.error(error_msg)
            return ConversionResult(success=False, file_path=file_path, error_message=error_msg, original_name=original_name)
        
        # 构建API参数
        extra_params = {
            "start_num": start_num,
            "position": position,
            "margin": margin
        }
        
        # 记录操作描述
        await self.logger.log("info", f"正在为PDF添加页码（起始页码: {start_num}, 位置: {position}, 边距: {margin}）...")
        
        # 调用convert_file方法处理API请求
        return await self.convert_file(file_path, "number-pdf", extra_params, password, original_name)
        
    # 定义需要PDF输入格式的操作和其描述
    PDF_ONLY_OPERATIONS = {
        "doc-repair": "去除水印",
        "number-pdf": "添加页码", 
        "flatten-pdf": "展平PDF",
        "resize-pdf": "调整PDF大小",
        "pdf-replace-text": "替换文本",
        "pdf-repair": "修复PDF",
        "curve-pdf": "PDF转曲",
        "double-pdf": "双层PDF转换",
        "pdf-delete-page": "PDF页面删除",
        "pdf-extract-table": "提取PDF表格"
    }
    
    async def _validate_pdf_format(self, file_path: str, format: str, input_format: Optional[InputFormat], original_name: Optional[str] = None) -> Optional[ConversionResult]:
        """验证PDF格式操作的输入格式
        
        Args:
            file_path: 文件路径
            format: 目标格式
            input_format: 输入格式
            original_name: 原始文件名
            
        Returns:
            ConversionResult: 如果验证失败返回错误结果，否则返回None
        """
        if format in self.PDF_ONLY_OPERATIONS and input_format != InputFormat.PDF:
            operation_name = self.PDF_ONLY_OPERATIONS[format]
            error_msg = f"{operation_name}功能仅支持PDF文件"
            await self.logger.error(error_msg)
            return ConversionResult(success=False, file_path=file_path, error_message=error_msg, original_name=original_name)
        return None
    
    def _get_operation_description(self, format: str, input_format: Optional[InputFormat], output_format: Optional[OutputFormat], is_remote_path: bool) -> str:
        """获取操作描述
        
        Args:
            format: 目标格式
            input_format: 输入格式
            output_format: 输出格式
            is_remote_path: 是否为远程路径
            
        Returns:
            str: 操作描述
        """
        # 首先检查是否为PDF专用操作
        if format in self.PDF_ONLY_OPERATIONS:
            return self.PDF_ONLY_OPERATIONS[format]

        # PDF/A
        if format == "pdfa":
            return "转换为 PDF/A"
        
        # 其他格式转换操作
        if is_remote_path:
            return f"转换为 {output_format.value.upper()} 格式"
        else:
            if input_format:
                return f"将 {input_format.value.upper()} 转换为 {output_format.value.upper()} 格式"
            else:
                return f"转换为 {output_format.value.upper()} 格式"

    @require_api_key
    async def convert_file(self, file_path: str, format: str, extra_params: dict = None, password: str = None, original_name: Optional[str] = None) -> ConversionResult:
        """转换单个文件
        
        Args:
            file_path: 要转换的文件路径
            format: 目标格式
            extra_params: 额外的API参数，例如去除水印
            password: 文档密码，如果文档受密码保护，则需要提供（可选）
            original_name: 原始文件名（可选）
            
        Returns:
            ConversionResult: 转换结果
        """
        # 特殊格式：输出均为PDF的操作（包含 PDF_ONLY_OPERATIONS 以及 PDF/A）
        is_pdfa = format in ("pdfa", "pdf/a")
        is_special_operation = (format in self.PDF_ONLY_OPERATIONS) or is_pdfa
        actual_output_format = "pdf" if is_special_operation else format

        # 暂不支持 PDF/A -> PDF（本质为 PDF -> PDF）
        # 以及任何 PDF -> PDF 的转换：直接拦截，避免走到后端报错
        try:
            ext_guess = self.file_handler.get_file_extension(file_path)
        except Exception:
            ext_guess = ""
        if actual_output_format == "pdf" and ext_guess == ".pdf" and not is_special_operation:
            return ConversionResult(success=False, file_path=file_path, error_message="暂不支持 PDF/A/PDF 转 PDF（PDF→PDF 转换）", original_name=original_name)

        # 检查是否为URL或OSS路径，如果是则跳过文件格式检查
        is_remote_path = self.file_handler.is_url(file_path) or self.file_handler.is_oss_id(file_path)
        
        if not is_remote_path:
            # 只对本地文件进行格式验证
            
            # 验证输入文件格式
            input_format = self.file_handler.get_input_format(file_path)
            if not input_format and not is_special_operation:
                error_msg = f"不支持的输入文件格式: {self.file_handler.get_file_extension(file_path)}"
                await self.logger.error(error_msg)
                return ConversionResult(success=False, file_path=file_path, error_message=error_msg, original_name=original_name)

            # 验证PDF专用操作的格式
            pdf_validation_result = await self._validate_pdf_format(file_path, format, input_format, original_name)
            if pdf_validation_result is not None:
                return pdf_validation_result

            # 验证输出格式（除去特殊操作外）
            if not is_special_operation:
                try:
                    output_format = OutputFormat(format)
                except ValueError:
                    error_msg = f"不支持的输出格式: {format}"
                    await self.logger.error(error_msg)
                    return ConversionResult(success=False, file_path=file_path, error_message=error_msg, original_name=original_name)
                # 验证输入格式是否支持该输出格式（避免出现 PNG→JPG、JPG→PNG 等会调用但必失败的情况）
                allowed_outputs = self.file_handler.get_available_output_formats(input_format) if input_format else set()
                if input_format and output_format not in allowed_outputs:
                    error_msg = f"不支持的格式转换: {input_format.value.upper()} -> {output_format.value.upper()}"
                    await self.logger.error(error_msg)
                    return ConversionResult(success=False, file_path=file_path, error_message=error_msg, original_name=original_name)
            else:
                output_format = OutputFormat.PDF

        else:
            # 远程路径的情况，设置必要的变量以便后续使用
            if not is_special_operation:
                try:
                    output_format = OutputFormat(format)
                except ValueError:
                    error_msg = f"不支持的输出格式: {format}"
                    await self.logger.error(error_msg)
                    return ConversionResult(success=False, file_path=file_path, error_message=error_msg, original_name=original_name)
            else:
                output_format = OutputFormat.PDF
            
            # 对于远程路径，无法确定输入格式，但为了让后续代码能正常运行，设置一个默认值
            input_format = None

        # 验证文件
        exists = await self.file_handler.validate_file_exists(file_path)
        if not exists:
            return ConversionResult(success=False, file_path=file_path, error_message="文件不存在", original_name=original_name)

        # 获取操作描述
        # PDF/A 的展示名
        op_format = "pdfa" if is_pdfa else format
        operation_desc = self._get_operation_description(op_format, input_format, output_format, is_remote_path)
        await self.logger.log("info", f"正在{operation_desc}...")

        import httpx
        async with httpx.AsyncClient(timeout=3600.0) as client:
            task_id = None
            try:
                # 初始化extra_params（如果为None）
                if extra_params is None:
                    extra_params = {}
                
                # 如果提供了密码，将其添加到extra_params
                if password:
                    extra_params["password"] = password

                if original_name:
                    extra_params["filename"] = os.path.splitext(original_name)[0]
                
                one_page_per_sheet = extra_params.pop("one_page_per_sheet", False)
                # 仅在Excel to PDF转换时，且one_page_per_sheet=True时，才设置provider="apower"
                # 检查是否为Excel→PDF转换
                is_excel_to_pdf = format == "pdf" and (self.file_handler.get_file_extension(file_path) == ".xlsx" or self.file_handler.get_file_extension(file_path) == ".xls")
                if one_page_per_sheet and is_excel_to_pdf:
                    extra_params["provider"] = "apower"
                    await self.logger.log("info", "检测到Excel表格转PDF，启用每工作表一页模式")

                # 创建转换任务
                task_id = await self._create_task(client, file_path, format, extra_params)
                
                # 等待任务完成
                download_url = await self._wait_for_task(client, task_id, "转换")
                
                # 记录完成信息
                await self.logger.log("info", "转换完成。可通过下载链接获取结果文件。")
                return ConversionResult(
                    success=True,
                    file_path=file_path,
                    error_message=None,
                    download_url=download_url,
                    original_name=original_name,
                    task_id=task_id
                )

            except Exception as e:
                return ConversionResult(
                    success=False,
                    file_path=file_path,
                    error_message=str(e),
                    download_url=None,
                    original_name=original_name,
                    task_id=task_id
                )

    async def _create_task(self, client: httpx.AsyncClient, file_path: str, format: str, extra_params: dict = None) -> str:
        # PDF/A：底层 format 需要使用 pdf-to-pdfa，并把 profile 放在 args.format
        if format in ("pdfa", "pdf/a"):
            data = {"format": "pdf-to-pdfa"}
            if extra_params is None:
                extra_params = {}
            args = extra_params.get("args")
            if not isinstance(args, dict):
                args = {}
            if "format" not in args:
                args["format"] = "0"
            extra_params["args"] = args
        else:
            data = {"format": format}
        if extra_params:
            data.update(extra_params)

        self.api_base_url = f"https://{self.api_endpoint}/tasks/document/conversion"
        if format == "pdf":
            ext = self.file_handler.get_file_extension(file_path)
            direct_pdf_exts = {
                ".docx", ".doc",
                ".xlsx", ".xls",
                ".pptx", ".ppt",
                ".jpg", ".jpeg", ".png",
                ".gif", ".bmp",
                ".dwg", ".caj", ".ofd",
                ".dxf",
                ".epub", ".mobi",
                ".txt", ".tex", ".odt", ".md", ".rtf",
                ".odg", ".ods", ".odp",
                ".heic", ".svg", ".tiff", ".tif", ".webp", ".eps", ".azw3",
            }
            if ext in (".html", ".htm") or (file_path and file_path.startswith(("http://", "https://")) and ext not in direct_pdf_exts):
                self.api_base_url = self.api_wkhtmltopdf_url

        return await super()._create_task(
            client=client,
            file_path=file_path,
            data=data,
            response_action="转换任务"
        )