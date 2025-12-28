"""文件打包（Archive）服务：将多个资源打包为一个 zip"""
import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import httpx

from ..utils.common import BaseResult, Logger, FileHandler, BaseApiClient, require_api_key


@dataclass
class ArchiveResult(BaseResult):
    """打包结果数据类"""
    pass


class Archiver(BaseApiClient):
    """
    打包服务（archive）：
    - POST https://{endpoint}/tasks/document/archive
    - GET  https://{endpoint}/tasks/document/archive/{task_id}
    """
    def __init__(self, logger: Logger, file_handler: FileHandler):
        super().__init__(logger, file_handler)
        self.api_base_url = f"https://{self.api_endpoint}/tasks/document/archive"

    @require_api_key
    async def package_files(
        self,
        file_paths: List[str],
        original_name: Optional[str] = None,
        custom_filenames: Optional[Dict[str, str]] = None
    ) -> ArchiveResult:
        """
        打包多个文件为一个zip。
        入参（三选一，且至少2个）：
        - resource_ids: ["id1","id2",...]
        - urls: ["https://...","https://...",...]
        - files: multipart (file1,file2,...)
        可选：
        - custom_filenames: { "<resource_id|url>": "<custom_name>", ... }  # 压缩包内文件名（不含扩展名也可）
        """
        if not file_paths or len(file_paths) < 2:
            return ArchiveResult(success=False, file_path="", error_message="打包至少需要两个文件", original_name=original_name)

        async with httpx.AsyncClient(timeout=3600.0) as client:
            task_id = None
            try:
                task_id = await self._create_archive_task(
                    client,
                    file_paths,
                    filename=original_name,
                    custom_filenames=custom_filenames
                )
                download_url = await self._wait_for_task(client, task_id, "打包")
                await self.logger.log("info", "文件打包完成")
                return ArchiveResult(
                    success=True,
                    file_path="",
                    error_message=None,
                    download_url=download_url,
                    original_name=original_name or self._default_zip_name(file_paths),
                    task_id=task_id
                )
            except Exception as e:
                return ArchiveResult(
                    success=False,
                    file_path="",
                    error_message=str(e),
                    download_url=None,
                    original_name=original_name,
                    task_id=task_id
                )

    def _default_zip_name(self, file_paths: List[str]) -> str:
        # 不做本地化，仅兜底命名
        return "Batch-Download"

    async def _create_archive_task(
        self,
        client: httpx.AsyncClient,
        file_paths: List[str],
        *,
        filename: Optional[str] = None,
        custom_filenames: Optional[Dict[str, str]] = None
    ) -> str:
        """
        创建 archive 打包任务：
        - 允许 resource_ids 与 urls 共存（按接口能力）
        - 全部为本地文件 => multipart files
        - 暂不支持「本地文件」与「urls/resource_ids」混合
        """
        headers = {"X-API-KEY": self.api_key}

        oss_ids = [p.split("oss_id://", 1)[1] for p in file_paths if self.file_handler.is_oss_id(p)]
        urls = [p for p in file_paths if self.file_handler.is_url(p)]
        locals_ = [p for p in file_paths if (not self.file_handler.is_url(p) and not self.file_handler.is_oss_id(p))]

        await self.logger.log("info", "正在提交文件打包任务...")

        # 本地文件：走 multipart（不与 url/oss 混用）
        if locals_:
            if oss_ids or urls:
                raise RuntimeError("打包暂不支持本地文件与远程(urls/resource_ids)混合输入")
            files = {}
            try:
                for i, fp in enumerate(locals_):
                    files[f"file{i+1}"] = open(fp, "rb")
                response = await client.post(self.api_base_url, files=files, headers=headers)
                return await self._handle_api_response(response, "创建打包任务")
            finally:
                for f in files.values():
                    try:
                        f.close()
                    except Exception:
                        pass

        # 远程输入：resource_ids 与 urls 可共存
        payload: Dict[str, Any] = {}
        if oss_ids:
            payload["resource_ids"] = oss_ids
        if urls:
            payload["urls"] = urls
        if filename:
            # 注意：archive 接口通常会自动追加 ".zip" 后缀；
            # 因此这里传入不带后缀的文件名，避免出现 "xxx.zip.zip"。
            base = os.path.basename(filename)
            if base.lower().endswith(".zip"):
                base = base[:-4]
            payload["filename"] = base
        if custom_filenames:
            allowed_keys = set(oss_ids) | set(urls)
            payload["custom_filenames"] = {k: v for k, v in custom_filenames.items() if k in allowed_keys and v}
        if not payload:
            raise RuntimeError("打包输入为空或不支持：需要 urls/resource_ids 或本地文件")
        headers["Content-Type"] = "application/json"
        response = await client.post(self.api_base_url, json=payload, headers=headers)
        return await self._handle_api_response(response, "创建打包任务")


