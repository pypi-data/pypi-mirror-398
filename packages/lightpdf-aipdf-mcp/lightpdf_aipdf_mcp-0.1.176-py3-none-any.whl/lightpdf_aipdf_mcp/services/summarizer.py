from dataclasses import dataclass
import os
import httpx
from typing import Optional
from ..utils.common import Logger, BaseResult, FileHandler, BaseApiClient, require_api_key

@dataclass
class SummarizeResult(BaseResult):
    """摘要结果数据类，结构与 TranslateResult 完全一致"""
    summary: Optional[str] = None

class Summarizer(BaseApiClient):
    """PDF文档摘要器，结构与 Translator 完全一致"""
    def __init__(self, logger: Logger, file_handler: FileHandler):
        super().__init__(logger, file_handler)

    @require_api_key
    async def summarize_pdf(self, file_path: str, prompt: str, language: Optional[str] = None, password: Optional[str] = None, original_name: Optional[str] = None) -> SummarizeResult:
        # 构建API参数
        extra_params = {
            "po": "lightpdf"
        }
        if password:
            extra_params["password"] = password
        if original_name:
            extra_params["filename"] = os.path.splitext(original_name)[0]

        async with httpx.AsyncClient(timeout=3600.0) as client:
            task_id = None
            headers = {"X-API-KEY": self.api_key}
            try:
                # Phase 1: Embedding
                response_action="摘要任务1"
                self.api_base_url = f"https://{self.api_endpoint}/tasks/llm/embedding"

                data = extra_params.copy() if extra_params else {}

                task_id = await self._create_task(client, file_path, data, response_action)
                await self.logger.log("debug", f"摘要任务1，task_id: {task_id}")

                file_hash = await self._wait_for_task(client, task_id, "摘要1")

                # Phase 2: Summarize
                response_action="摘要任务2"
                self.api_base_url = f"https://{self.api_endpoint}/tasks/llm/conversation"

                data = extra_params.copy() if extra_params else {}
                data["template_id"] = "63357fa3-ba37-47d5-b9c3-8b10ed0a59d6"
                data["response_type"] = 0
                data["file_hash"] = file_hash
                data["prompt"] = prompt
                data["language"] = language

                await self.logger.log("debug", f"正在提交{response_action}...{data}")
                response = await client.post(
                    self.api_base_url,
                    json=data,
                    headers=headers
                )

                task_id = await self._handle_api_response(response, response_action)
                await self.logger.log("debug", f"摘要任务2，task_id: {task_id}")

                # /tasks/llm/conversation 完成态需要从 answer.text 取值
                summary = await self._wait_for_task(client, task_id, "摘要2", result_field="answer.text")
                if summary is None:
                    summary = ""

                await self.logger.log("debug", f"摘要完成。")
                return SummarizeResult(
                    success=True,
                    file_path=file_path,
                    error_message=None,
                    summary=summary,
                    original_name=original_name,
                    task_id=task_id
                )
            except Exception as e:
                return SummarizeResult(
                    success=False,
                    file_path=file_path,
                    error_message=str(e),
                    summary=None,
                    original_name=original_name,
                    task_id=task_id
                )