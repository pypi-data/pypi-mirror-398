from dataclasses import dataclass
import os
import httpx
from typing import Optional, Dict, Any
from ..utils.common import Logger, BaseResult, FileHandler, BaseApiClient, require_api_key

@dataclass
class OcrResult(BaseResult):
    """OCR结果数据类"""
    pass

class OcrClient(BaseApiClient):
    """文档OCR识别器"""
    def __init__(self, logger: Logger, file_handler: FileHandler):
        super().__init__(logger, file_handler)
        self.api_base_url = f"https://{self.api_endpoint}/tasks/document/ocr"

    @require_api_key
    async def ocr_document(self, file_path: str, format: str = "pdf", language: Optional[str] = None, password: Optional[str] = None, original_name: Optional[str] = None) -> OcrResult:
        # 构建API参数
        extra_params = {
            "format": format or "pdf"
        }
        if language:
            extra_params["language"] = language
        else:
            extra_params["language"] = "English,Digits,ChinesePRC"
        if password:
            extra_params["password"] = password
        if original_name:
            extra_params["filename"] = os.path.splitext(original_name)[0]

        async with httpx.AsyncClient(timeout=3600.0) as client:
            task_id = None
            try:
                # 创建OCR任务
                task_id = await self._create_task(client, file_path, extra_params)
                # 等待任务完成
                download_url = await self._wait_for_task(client, task_id, "OCR识别")

                await self.logger.log("info", "OCR识别完成。可通过下载链接获取结果文件。")
                return OcrResult(
                    success=True,
                    file_path=file_path,
                    error_message=None,
                    download_url=download_url,
                    original_name=original_name,
                    task_id=task_id
                )
            except Exception as e:
                return OcrResult(
                    success=False,
                    file_path=file_path,
                    error_message=str(e),
                    download_url=None,
                    original_name=original_name,
                    task_id=task_id
                )

    async def _create_task(self, client: httpx.AsyncClient, file_path: str, extra_params: dict = None) -> str:
        data = extra_params.copy() if extra_params else {}

        # 调用基类通用方法
        return await super()._create_task(
            client=client,
            file_path=file_path,
            data=data,
            response_action="OCR任务"
        ) 