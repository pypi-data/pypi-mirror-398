from dataclasses import dataclass
import os
import httpx
from typing import Optional, Dict, Any
from ..utils.common import Logger, BaseResult, FileHandler, BaseApiClient, require_api_key

@dataclass
class TranslateResult(BaseResult):
    """翻译结果数据类"""
    pass

class Translator(BaseApiClient):
    """PDF文档翻译器"""
    def __init__(self, logger: Logger, file_handler: FileHandler):
        super().__init__(logger, file_handler)
        self.api_base_url = f"https://{self.api_endpoint}/tasks/document/transdocument-local"

    @require_api_key
    async def translate_pdf(self, file_path: str, source: str, target: str, output_type: str = "mono", password: Optional[str] = None, original_name: Optional[str] = None) -> TranslateResult:
        # 构建API参数
        extra_params = {
            "source": source or "auto",
            "target": target,
            "output_type": output_type or "mono"
        }
        if password:
            extra_params["password"] = password
        if original_name:
            extra_params["filename"] = os.path.splitext(original_name)[0]

        async with httpx.AsyncClient(timeout=3600.0) as client:
            task_id = None
            try:
                # 创建翻译任务
                task_id = await self._create_task(client, file_path, extra_params)
                # 等待任务完成
                download_url = await self._wait_for_task(client, task_id, "翻译")

                await self.logger.log("info", "翻译完成。可通过下载链接获取结果文件。")
                return TranslateResult(
                    success=True,
                    file_path=file_path,
                    error_message=None,
                    download_url=download_url,
                    original_name=original_name,
                    task_id=task_id
                )
            except Exception as e:
                return TranslateResult(
                    success=False,
                    file_path=file_path,
                    error_message=str(e),
                    download_url=None,
                    original_name=original_name,
                    task_id=task_id
                )

    async def _create_task(self, client: httpx.AsyncClient, file_path: str, extra_params: dict = None) -> str:
        data = extra_params.copy() if extra_params else {}

        return await super()._create_task(
            client=client,
            file_path=file_path,
            data=data,
            response_action="翻译任务"
        )