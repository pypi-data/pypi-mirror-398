"""PDF文档编辑模块"""
import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any

import httpx

from ..utils.common import BaseResult, Logger, FileHandler, BaseApiClient, require_api_key
from .converter import InputFormat

class EditType(str, Enum):
    """支持的PDF编辑操作类型"""
    SPLIT = "split"          # 拆分PDF
    MERGE = "merge"          # 合并PDF
    ROTATE = "rotate"        # 旋转PDF
    COMPRESS = "compress"    # 压缩PDF
    ENCRYPT = "protect"      # 加密PDF
    DECRYPT = "unlock"       # 解密PDF
    ADD_WATERMARK = "watermark"  # 添加水印
    EXTRACT_IMAGE = "extract"  # 提取图片
    EDIT = "edit"            # 编辑操作
    DELETE_PAGE = "pdf-delete-page"  # 删除页面

@dataclass
class EditResult(BaseResult):
    """编辑结果数据类"""
    pass

class Editor(BaseApiClient):
    """PDF文档编辑器"""
    def __init__(self, logger: Logger, file_handler: FileHandler):
        super().__init__(logger, file_handler)
        self.api_base_url = f"https://{self.api_endpoint}/tasks/document/pdfedit"

    async def _validate_pdf_file(self, file_path: str) -> bool:
        """验证文件是否为PDF格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 如果是PDF文件则返回True，否则返回False
        """
        # 对于URL或OSS路径，跳过文件格式检查
        if self.file_handler.is_url(file_path) or self.file_handler.is_oss_id(file_path):
            return True
            
        input_format = self.file_handler.get_input_format(file_path)
        if input_format != InputFormat.PDF:
            await self.logger.error(f"此功能仅支持PDF文件，当前文件格式为: {self.file_handler.get_file_extension(file_path)}")
            return False
        return True
    
    async def _log_operation(self, operation: str, details: str = None):
        """记录操作日志
        
        Args:
            operation: 操作描述
            details: 详细信息（可选）
        """
        log_msg = f"正在{operation}"
        if details:
            log_msg += f"（{details}）"
        log_msg += "..."
        await self.logger.log("info", log_msg)
    
    async def split_pdf(self, file_path: str, pages: str = "", password: Optional[str] = None, split_type: str = "page", merge_all: int = 1, original_name: Optional[str] = None) -> EditResult:
        """拆分PDF文件
        
        Args:
            file_path: 要拆分的PDF文件路径
            pages: 拆分页面规则，例如 "1,3,5-7" 表示提取第1,3,5,6,7页，""表示所有页面，默认为""
            password: 文档密码，如果文档受密码保护，则需要提供（可选）
            split_type: 拆分类型，可选值: "every"=每页拆分为一个文件, "page"=指定页面规则拆分，"bookmark"=按书签/大纲/目录节点拆分，默认为"page"
            merge_all: 是否合并拆分后的文件，仅在split_type="page"时有效，0=不合并，1=合并，默认为1
            original_name: 原始文件名（可选）
            
        Returns:
            EditResult: 拆分结果
        """
        # 验证输入文件是否为PDF
        if not await self._validate_pdf_file(file_path):
            return EditResult(success=False, file_path=file_path, error_message="非PDF文件", original_name=original_name)
        
        # 验证拆分类型
        valid_split_types = {"every", "page", "bookmark"}
        if split_type not in valid_split_types:
            await self.logger.error(f"无效的拆分类型: {split_type}。有效值为: every, page, bookmark")
            return EditResult(success=False, file_path=file_path, error_message=f"无效的拆分类型: {split_type}。有效值为: every, page, bookmark", original_name=original_name)
        
        # 构建API参数
        extra_params = {
            "split_type": split_type
        }
        
        # 仅在page模式下设置pages和merge_all参数
        if split_type == "page":
            extra_params["pages"] = pages
            extra_params["merge_all"] = merge_all
            
        # 记录操作描述
        operation_details = f"类型: {split_type}"
        if split_type == "page":
            operation_details += f", 页面: {pages}"
        await self._log_operation("拆分PDF文件", operation_details)
        
        # 调用edit_pdf方法处理API请求
        return await self.edit_pdf(file_path, EditType.SPLIT, extra_params, password, original_name)

    async def merge_pdfs(self, file_paths: List[str], password: Optional[str] = None, original_name: Optional[str] = None) -> EditResult:
        """合并多个PDF文件
        
        Args:
            file_paths: 要合并的PDF文件路径列表
            password: 文档密码，如果文档受密码保护，则需要提供（可选）
            original_name: 原始文件名（可选）
            
        Returns:
            EditResult: 合并结果
        """
        if len(file_paths) < 2:
            await self.logger.error("合并PDF至少需要两个文件")
            return EditResult(success=False, file_path=','.join(file_paths), error_message="合并PDF至少需要两个文件", original_name=original_name)
        
        # 验证所有文件是否都是PDF并且存在
        for pdf_file in file_paths:
            if not await self._validate_pdf_file(pdf_file):
                return EditResult(success=False, file_path=pdf_file, error_message="非PDF文件", original_name=original_name)
            
            exists = await self.file_handler.validate_file_exists(pdf_file)
            if not exists:
                return EditResult(success=False, file_path=pdf_file, error_message="文件不存在", original_name=original_name)
        
        # 记录操作描述
        await self._log_operation("合并PDF文件", f"{len(file_paths)} 个文件")
        
        # 合并PDF需要特殊处理，因为涉及多个文件
        async with httpx.AsyncClient(timeout=3600.0) as client:
            task_id = None
            try:
                # 创建合并任务
                task_id = await self._create_merge_task(client, file_paths, password, original_name)
                
                # 等待任务完成
                download_url = await self._wait_for_task(client, task_id, "合并")
                
                # 记录完成信息
                await self.logger.log("info", "PDF合并完成。可通过下载链接获取结果文件。")
                
                return EditResult(
                    success=True,
                    file_path=file_paths[0],  # 使用第一个文件路径作为参考
                    error_message=None,
                    download_url=download_url,
                    original_name=original_name,
                    task_id=task_id
                )

            except Exception as e:
                return EditResult(
                    success=False,
                    file_path=file_paths[0],
                    error_message=str(e),
                    download_url=None,
                    original_name=original_name,
                    task_id=task_id
                )

    async def rotate_pdf(self, file_path: str, angle_params: Dict[str, str], password: Optional[str] = None, original_name: Optional[str] = None) -> EditResult:
        """旋转PDF文件的页面
        
        Args:
            file_path: 要旋转的PDF文件路径
            angle_params: 旋转角度和页面范围的映射，如 {"90": "1-3", "180": "4-6"} 
            password: 文档密码，如果文档受密码保护，则需要提供（可选）
            original_name: 原始文件名（可选）
            
        Returns:
            EditResult: 旋转结果
        """
        # 验证输入文件是否为PDF
        if not await self._validate_pdf_file(file_path):
            return EditResult(success=False, file_path=file_path, error_message="非PDF文件", original_name=original_name)
        
        # 验证旋转角度
        valid_angles = {"90", "180", "270"}
        for angle in angle_params.keys():
            if angle not in valid_angles:
                await self.logger.error("无效的旋转角度。角度必须是: 90, 180, 270")
                return EditResult(success=False, file_path=file_path, error_message="无效的旋转角度。角度必须是: 90, 180, 270", original_name=original_name)
        
        # 构建API参数
        extra_params = {
            "angle": json.dumps(angle_params)
        }
        
        # 记录操作描述
        angle_details = ", ".join([f"{angle}°: {pages}" for angle, pages in angle_params.items()])
        await self._log_operation("旋转PDF文件", f"参数: {angle_details}")
        
        # 调用edit_pdf方法处理API请求
        return await self.edit_pdf(file_path, EditType.ROTATE, extra_params, password, original_name)

    async def compress_pdf(self, file_path: str, image_quantity: int = 60, password: Optional[str] = None, original_name: Optional[str] = None) -> EditResult:
        """压缩PDF文件
        
        Args:
            file_path: 要压缩的PDF文件路径
            image_quantity: 图片质量，范围1-100，默认为60
            password: 文档密码，如果文档受密码保护，则需要提供（可选）
            original_name: 原始文件名（可选）
            
        Returns:
            EditResult: 压缩结果
        """
        # 验证输入文件是否为PDF
        if not await self._validate_pdf_file(file_path):
            return EditResult(success=False, file_path=file_path, error_message="非PDF文件", original_name=original_name)
        
        # 验证图片质量范围
        if not (1 <= image_quantity <= 100):
            await self.logger.error("图片质量必须在1到100之间")
            return EditResult(success=False, file_path=file_path, error_message="图片质量必须在1到100之间", original_name=original_name)
        
        # 构建API参数
        extra_params = {
            "image_quantity": image_quantity
        }
        
        # 记录操作描述
        await self._log_operation("压缩PDF文件", f"图片质量: {image_quantity}")
        
        # 调用edit_pdf方法处理API请求
        return await self.edit_pdf(file_path, EditType.COMPRESS, extra_params, password, original_name)

    async def encrypt_pdf(self, file_path: str, password: str, original_password: Optional[str] = None, provider: Optional[str] = None, original_name: Optional[str] = None) -> EditResult:
        """加密PDF文件
        
        Args:
            file_path: 要加密的PDF文件路径
            password: 要设置的新密码
            original_password: 原始密码，如果文件已经加密，则需要提供（可选）
            original_name: 原始文件名（可选）
            
        Returns:
            EditResult: 加密结果
        """
        # 验证输入文件是否为PDF
        if not await self._validate_pdf_file(file_path):
            return EditResult(success=False, file_path=file_path, error_message="非PDF文件", original_name=original_name)
        
        # 验证新密码
        if not password:
            await self.logger.error("加密PDF文件需要提供新密码")
            return EditResult(success=False, file_path=file_path, error_message="加密PDF文件需要提供新密码", original_name=original_name)
        
        # 构建API参数
        extra_params = {
            "password": password  # 新密码
        }
        if provider:
            extra_params["provider"] = provider
        
        # 记录操作描述
        await self._log_operation("加密PDF文件")
        
        # 调用edit_pdf方法处理API请求
        result = await self.edit_pdf(file_path, EditType.ENCRYPT, extra_params, original_password, original_name)

        # protect_pdf 特例：输出 original_password 为“加密后当前生效的打开密码”（即新设置的 password）
        # 注意：restrict_printing 会传 provider="printpermission"，不走该特例
        try:
            if (not provider) and isinstance(password, str) and password and isinstance(result, BaseResult):
                result.original_password = password
        except Exception:
            pass

        return result

    async def decrypt_pdf(self, file_path: str, password: Optional[str] = None, original_name: Optional[str] = None) -> EditResult:
        """解密PDF文件
        
        Args:
            file_path: 要解密的PDF文件路径
            password: 文档密码，用于解锁已加密的文档
            original_name: 原始文件名（可选）
            
        Returns:
            EditResult: 解密结果
        """
        # 验证输入文件是否为PDF
        if not await self._validate_pdf_file(file_path):
            return EditResult(success=False, file_path=file_path, error_message="非PDF文件", original_name=original_name)
        
        # 验证密码
        if not password:
            await self.logger.error("解密PDF文件需要提供密码")
            return EditResult(success=False, file_path=file_path, error_message="解密PDF文件需要提供密码", original_name=original_name)
        
        # 记录操作描述
        await self._log_operation("解密PDF文件")
        
        # 调用edit_pdf方法处理API请求
        return await self.edit_pdf(file_path, EditType.DECRYPT, {}, password, original_name)

    async def add_text_watermark(
        self, 
        file_path: str, 
        text: str, 
        position: str,  # 必需参数：位置，如"top", "center", "diagonal"等
        opacity: float = 1.0, 
        range: str = "",  # 与API保持一致，使用range而非pages
        layout: Optional[str] = None,  # 可选参数: "on"/"under"
        font_family: Optional[str] = None,
        font_size: Optional[int] = None,
        font_color: Optional[str] = None,
        password: Optional[str] = None,
        original_name: Optional[str] = None
    ) -> EditResult:
        """为PDF文件添加文本水印
        
        Args:
            file_path: 要添加水印的PDF文件路径
            text: 水印文本内容
            position: 水印位置，如"top", "center", "diagonal"等
            opacity: 透明度，0.0-1.0，默认1.0
            range: 页面范围，例如 "1,3,5-7" 或空字符串表示所有页面
            layout: 布局方式："on"=在内容上，"under"=在内容下，默认"on"
            font_family: 字体
            font_size: 字体大小
            font_color: 字体颜色，如 "#ff0000"
            password: 文档密码，如果文档受密码保护，则需要提供（可选）
            original_name: 原始文件名（可选）
            
        Returns:
            EditResult: 添加水印结果
        """
        # 验证输入文件是否为PDF
        if not await self._validate_pdf_file(file_path):
            return EditResult(success=False, file_path=file_path, error_message="非PDF文件", original_name=original_name)
        
        # 验证必需参数
        if not text:
            await self.logger.error("水印文本不能为空")
            return EditResult(success=False, file_path=file_path, error_message="水印文本不能为空", original_name=original_name)
        
        # 构建API参数
        extra_params = {
            "edit_type": "text",
            "text": text,
            "position": position,
            "opacity": opacity,
            "range": range
        }
        
        # 添加可选参数
        if layout:
            extra_params["layout"] = layout
        if font_family:
            extra_params["font_family"] = font_family
        if font_size:
            extra_params["font_size"] = font_size
        if font_color:
            extra_params["font_color"] = font_color
        
        # 记录操作描述
        await self._log_operation("为PDF添加水印", f"文本: {text}, 位置: {position}, 透明度: {opacity}")
        
        # 调用edit_pdf方法处理API请求
        return await self.edit_pdf(file_path, EditType.ADD_WATERMARK, extra_params, password, original_name)

    async def add_image_watermark(
        self,
        file_path: str,
        image_url: str,
        position: str = "center",
        opacity: float = 0.7,
        range: str = "",
        layout: Optional[str] = None,
        password: Optional[str] = None,
        original_name: Optional[str] = None
    ) -> EditResult:
        """为PDF文件添加图片水印
        
        Args:
            file_path: 要添加水印的PDF文件路径
            image_url: 水印图片的URL，必须包含协议（http/https/oss）
            position: 水印位置，如"top", "center", "diagonal"等，默认"center"
            opacity: 透明度，0.0-1.0，默认0.7
            range: 页面范围，例如 "1,3,5-7" 或空字符串表示所有页面
            layout: 布局方式："on"=在内容上，"under"=在内容下，默认"on"
            password: 文档密码，如果文档受密码保护，则需要提供（可选）
            original_name: 原始文件名（可选）
        
        Returns:
            EditResult: 添加图片水印结果
        """
        # 验证输入文件是否为PDF
        if not await self._validate_pdf_file(file_path):
            return EditResult(success=False, file_path=file_path, error_message="非PDF文件", original_name=original_name)
        if not image_url:
            await self.logger.error("水印图片URL不能为空")
            return EditResult(success=False, file_path=file_path, error_message="水印图片URL不能为空", original_name=original_name)
        # 构建API参数
        extra_params = {
            "edit_type": "image",
            "sign_url": image_url,
            "position": position,
            "opacity": opacity,
            "range": range
        }
        if layout:
            extra_params["layout"] = layout
        # 记录操作描述
        await self._log_operation("为PDF添加图片水印", f"图片: {image_url}, 位置: {position}, 透明度: {opacity}")
        # 调用edit_pdf方法处理API请求
        return await self.edit_pdf(file_path, EditType.ADD_WATERMARK, extra_params, password, original_name)

    async def remove_margin(self, file_path: str, password: Optional[str] = None, original_name: Optional[str] = None) -> EditResult:
        """去除PDF文件的白边
        
        Args:
            file_path: 要去除白边的PDF文件路径
            password: 文档密码，如果文档受密码保护，则需要提供（可选）
            original_name: 原始文件名（可选）
            
        Returns:
            EditResult: 去除白边的结果
        """
        # 验证输入文件是否为PDF
        if not await self._validate_pdf_file(file_path):
            return EditResult(success=False, file_path=file_path, error_message="非PDF文件", original_name=original_name)
        
        # 记录操作描述
        await self._log_operation("去除PDF文件白边")
        
        # 构建API参数，按照固定格式传递
        extra_params = {
            "pages": [{"url": "oss://autocrop", "oss_file": ""}]
        }
        
        # 调用edit_pdf方法处理API请求
        return await self.edit_pdf(file_path, EditType.EDIT, extra_params, password, original_name)

    async def extract_images(self, file_path: str, format: str = "png", password: Optional[str] = None, original_name: Optional[str] = None) -> EditResult:
        """从PDF文件中提取图片
        
        Args:
            file_path: 要提取图片的PDF文件路径
            format: 提取的图片格式，可选值为"bmp"/"png"/"gif"/"tif"/"jpg"，默认为"png"
            password: 文档密码，如果文档受密码保护，则需要提供（可选）
            original_name: 原始文件名（可选）
            
        Returns:
            EditResult: 提取结果
        """
        # 验证输入文件是否为PDF
        if not await self._validate_pdf_file(file_path):
            return EditResult(success=False, file_path=file_path, error_message="非PDF文件", original_name=original_name)
        
        # 验证图片格式
        valid_formats = {"bmp", "png", "gif", "tif", "jpg"}
        if format not in valid_formats:
            error_msg = f"无效的图片格式: {format}。有效值为: bmp, png, gif, tif, jpg"
            await self.logger.error(error_msg)
            return EditResult(success=False, file_path=file_path, error_message=error_msg, original_name=original_name)
        
        # 构建API参数
        extra_params = {
            "extract_type": "image",
            "format": format
        }
        
        # 记录操作描述
        await self._log_operation("从PDF提取图片", f"格式: {format}")
        
        # 调用edit_pdf方法处理API请求
        return await self.edit_pdf(file_path, EditType.EXTRACT_IMAGE, extra_params, password, original_name)

    async def delete_pages(self, file_path: str, range: str, password: Optional[str] = None, original_name: Optional[str] = None) -> EditResult:
        """删除PDF文件的指定页面
        
        Args:
            file_path: 要删除页面的PDF文件路径
            range: 要删除的页面范围，例如 "1,3,5-7"
            password: 文档密码，如果文档受密码保护，则需要提供（可选）
            original_name: 原始文件名（可选）
            
        Returns:
            EditResult: 删除页面的结果
        """
        # 验证输入文件是否为PDF
        if not await self._validate_pdf_file(file_path):
            return EditResult(success=False, file_path=file_path, error_message="非PDF文件", original_name=original_name)
        
        # 验证页面范围
        if not range.strip():
            await self.logger.error("页面范围不能为空")
            return EditResult(success=False, file_path=file_path, error_message="页面范围不能为空", original_name=original_name)
        
        # 构建API参数
        extra_params = {
            "range": range
        }
        
        # 记录操作描述
        await self._log_operation("删除PDF页面", f"页面范围: {range}")
        
        # 调用edit_pdf方法处理API请求，使用pdf-delete-page作为edit_type
        return await self.edit_pdf(file_path, EditType.DELETE_PAGE, extra_params, password, original_name)

    @require_api_key
    async def edit_pdf(self, file_path: str, edit_type: EditType, extra_params: Dict[str, Any] = None, password: Optional[str] = None, original_name: Optional[str] = None) -> EditResult:
        """编辑PDF文件
        
        Args:
            file_path: 要编辑的PDF文件路径
            edit_type: 编辑操作类型
            extra_params: 额外的API参数
            password: 文档密码，如果文档受密码保护，则需要提供（可选）
            original_name: 原始文件名（可选）
            
        注意:
            1. 对于加密操作(protect)，需要在extra_params中提供新密码
            2. 对于解密操作(unlock)，需要提供正确的password参数
            3. 所有extra_params中的参数将直接传递给API
            
        Returns:
            EditResult: 编辑结果
        """
        # 验证文件
        exists = await self.file_handler.validate_file_exists(file_path)
        if not exists:
            return EditResult(success=False, file_path=file_path, error_message="文件不存在", original_name=original_name)

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
                
                # 创建编辑任务
                task_id = await self._create_task(client, file_path, edit_type, extra_params)
                
                # 等待任务完成
                download_url = await self._wait_for_task(client, task_id, "编辑")
                
                # 记录完成信息
                await self.logger.log("info", "编辑完成。可通过下载链接获取结果文件。")
                
                return EditResult(
                    success=True,
                    file_path=file_path,
                    error_message=None,
                    download_url=download_url,
                    original_name=original_name,
                    task_id=task_id
                )

            except Exception as e:
                return EditResult(
                    success=False,
                    file_path=file_path,
                    error_message=str(e),
                    download_url=None,
                    original_name=original_name,
                    task_id=task_id
                )

    async def _create_task(self, client: httpx.AsyncClient, file_path: str, edit_type, extra_params: dict = None) -> str:
        data = {"type": edit_type.value}
        if extra_params:
            data.update(extra_params)

        return await super()._create_task(
            client=client,
            file_path=file_path,
            data=data,
            response_action="编辑任务"
        )

    async def _create_merge_task(self, client: httpx.AsyncClient, file_paths: List[str], password: Optional[str] = None, original_name: Optional[str] = None) -> str:
        """创建PDF合并任务
        
        Args:
            client: HTTP客户端
            file_paths: 要合并的PDF文件路径列表
            password: 文档密码，如果文档受密码保护，则需要提供（可选）
        
        Returns:
            str: 任务ID
        """
        headers = {"X-API-KEY": self.api_key}
        data = {"type": EditType.MERGE.value}
        
        if original_name:
            data["filename"] = os.path.splitext(original_name)[0]
        
        # 准备URL格式的输入
        url_inputs = []
        
        # 准备本地文件列表
        local_files = []
        files = {}
        
        for i, file_path in enumerate(file_paths):
            # 检查是否为URL或OSS路径
            if self.file_handler.is_oss_id(file_path):
                # 对于OSS路径，添加到inputs数组
                input_item = {"resource_id": file_path.split("oss_id://")[1]}
                if password:
                    input_item["password"] = password
                url_inputs.append(input_item)
            elif self.file_handler.is_url(file_path):
                # arxiv.org/pdf/特殊处理
                if isinstance(file_path, str) and "arxiv.org/pdf/" in file_path:
                    from urllib.parse import urlparse, urlunparse
                    url_obj = urlparse(file_path)
                    if not url_obj.path.endswith(".pdf"):
                        new_path = url_obj.path + ".pdf"
                        file_path = urlunparse(url_obj._replace(path=new_path))
                # 对于URL或OSS路径，添加到inputs数组
                input_item = {"url": file_path}
                if password:
                    input_item["password"] = password
                url_inputs.append(input_item)
            else:
                # 记录本地文件，需要使用form方式
                local_files.append(file_path)
                
        await self.logger.log("info", f"正在提交PDF合并任务...{data}")
        
        # 如果全部是URL输入，使用JSON方式
        if url_inputs and not local_files:
            data["inputs"] = url_inputs
            # 使用JSON方式时添加Content-Type
            headers["Content-Type"] = "application/json"
            response = await client.post(
                self.api_base_url,
                json=data,
                headers=headers
            )
        else:
            # 如果有本地文件，使用form方式，不需要添加Content-Type
            # 准备文件
            for i, file_path in enumerate(local_files):
                files[f"file{i+1}"] = open(file_path, "rb")
                
            # 如果有URL输入，添加inputs参数
            if url_inputs:
                data["inputs"] = json.dumps(url_inputs)
            
            try:
                # 发送请求
                response = await client.post(
                    self.api_base_url,
                    data=data,
                    files=files,
                    headers=headers
                )
                
            finally:
                # 确保所有打开的文件都被关闭
                for file_obj in files.values():
                    file_obj.close()
            
        # 使用基类的方法处理API响应
        return await self._handle_api_response(response, "创建合并任务") 