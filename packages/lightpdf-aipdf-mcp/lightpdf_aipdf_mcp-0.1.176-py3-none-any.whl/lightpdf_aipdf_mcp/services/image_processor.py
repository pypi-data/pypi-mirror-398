"""图片处理服务（部分实现：图片去水印、去贴纸）"""
import base64
import io
import json
import os
import urllib.parse
from dataclasses import dataclass
from typing import List, Optional, Tuple
from urllib.request import url2pathname

import httpx
from PIL import Image, ImageDraw

from ..utils.common import BaseResult, Logger, FileHandler, BaseApiClient, require_api_key


@dataclass
class ImageProcessResult(BaseResult):
    """图片处理结果数据类"""
    pass


class ImageProcessor(BaseApiClient):
    """
    图片处理服务（去水印/去Logo/去贴纸/去文字）。
    说明：
    - remove_image_watermark 已接入 /tasks/visual/external/watermark-remove
    - remove_image_logo 与 remove_image_watermark 相同
    - remove_image_sticker 已接入 /tasks/visual/external/image-edit
    - 其它能力目前仅提供工具骨架，占位返回“未配置后端接口”
    """
    def __init__(self, logger: Logger, file_handler: FileHandler):
        super().__init__(logger, file_handler)
        self.external_watermark_remove_url = f"https://{self.api_endpoint}/tasks/visual/external/watermark-remove"
        self.visual_watermark_url = f"https://{self.api_endpoint}/tasks/visual/watermark"
        self.image_edit_url = f"https://{self.api_endpoint}/tasks/visual/external/image-edit"
        self.ocrpp_url = f"https://{self.api_endpoint}/tasks/document/ocrpp"
        # 默认不指定其它视觉接口
        self.api_base_url = None

    def _normalize_image_inputs(self, inputs: List[Tuple[str, Optional[str]]]) -> List[Tuple[str, Optional[str]]]:
        """
        将输入归一化为 (path, original_name) 列表：
        - 仅支持 (path, name) 二元组
        - 统一处理 file:// -> 本地路径
        - 若 name 缺失，则从 path 推断一个兜底文件名
        """
        out: List[Tuple[str, Optional[str]]] = []
        for item in inputs or []:
            p = item[0]
            n = item[1] if len(item) > 1 else None

            if not isinstance(p, str) or not p:
                continue

            p = self._normalize_local_path(p)

            if not n:
                # 从 path 推断文件名（忽略 query）
                try:
                    parsed = urllib.parse.urlparse(p)
                    base = os.path.basename(parsed.path) or None
                    if base:
                        n = urllib.parse.unquote(base)
                except Exception:
                    n = p.rsplit("/", 1)[-1] if "/" in p else p

            out.append((p, n))
        return out

    async def _not_configured(self, op_name: str, file_items: List[Tuple[str, Optional[str]]]) -> List[ImageProcessResult]:
        msg = f"图片处理接口未接入：{op_name}"
        await self.logger.log("error", msg)
        results: List[ImageProcessResult] = []
        for p, n in file_items or []:
            results.append(ImageProcessResult(success=False, file_path=p, error_message=msg, original_name=n))
        return results

    async def _process_external_watermark_remove(
        self,
        file_items: List[Tuple[str, Optional[str]]],
        *,
        operation_name: str
    ) -> List[ImageProcessResult]:
        """通用：external watermark-remove 单图处理 + 轮询 data.file"""
        if not file_items:
            return []

        results: List[ImageProcessResult] = []

        async with httpx.AsyncClient(timeout=3600.0) as client:
            for p, n in file_items:
                if not p:
                    continue
                task_id: Optional[str] = None
                old_api_base_url = self.api_base_url
                self.api_base_url = self.external_watermark_remove_url
                try:
                    # 复用 BaseApiClient._create_task：它天然支持 resource_id/url/file 三选一
                    task_id = await self._create_task(client, p, {}, response_action=f"创建{operation_name}任务")
                    out_url = await self._wait_for_task(
                        client,
                        task_id,
                        operation_name,
                        result_field="file"
                    )

                    results.append(ImageProcessResult(success=True, file_path=p, download_url=out_url, task_id=task_id, original_name=n))
                except Exception as e:
                    results.append(ImageProcessResult(success=False, file_path=p, error_message=str(e), task_id=task_id, original_name=n))
                finally:
                    self.api_base_url = old_api_base_url

        return results

    @require_api_key
    async def remove_image_watermark(self, files: List[Tuple[str, Optional[str]]]) -> List[ImageProcessResult]:
        """
        图片去水印：
        - POST https://{endpoint}/tasks/visual/external/watermark-remove
          入参（三选一）：resource_id / url / file
        - GET  https://{endpoint}/tasks/visual/external/watermark-remove/{task_id}
        
        完成态结果字段：data.file
        """
        items = self._normalize_image_inputs(files)
        return await self._process_external_watermark_remove(items, operation_name="图片去水印")

    @require_api_key
    async def remove_image_logo(self, files: List[Tuple[str, Optional[str]]]) -> List[ImageProcessResult]:
        """
        去除Logo：
        - 与 remove_image_watermark 使用同一接口与流程
        """
        items = self._normalize_image_inputs(files)
        return await self._process_external_watermark_remove(items, operation_name="图片去Logo")

    @require_api_key
    async def remove_image_sticker(self, files: List[Tuple[str, Optional[str]]]) -> List[ImageProcessResult]:
        """
        去除贴纸：
        - POST https://{endpoint}/tasks/visual/external/image-edit
        - GET  https://{endpoint}/tasks/visual/external/image-edit/{task_id}
        """
        items = self._normalize_image_inputs(files)
        if not items:
            return []

        prompt = "去掉图片中的所有贴纸"
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        results: List[ImageProcessResult] = []

        async with httpx.AsyncClient(timeout=3600.0) as client:
            for p, n in items:
                task_id: Optional[str] = None
                try:
                    data = {
                        "po": "lightpdf",
                        "provider": 5,
                        "prompt": prompt,
                        "only_image": True,
                        "input_file": [p]
                    }

                    # 创建任务：该接口返回 data.task_id
                    resp = await client.post(self.image_edit_url, json=data, headers=headers)
                    task_id = await self._handle_api_response(resp, "创建去贴纸任务")

                    # 轮询任务：完成态结果字段为 data.image
                    old_api_base_url = self.api_base_url
                    self.api_base_url = self.image_edit_url
                    try:
                        image_url = await self._wait_for_task(
                            client,
                            task_id,
                            "图片去贴纸",
                            result_field="image_url"
                        )
                    finally:
                        self.api_base_url = old_api_base_url

                    results.append(ImageProcessResult(success=True, file_path=p, download_url=image_url, task_id=task_id, original_name=n))
                except Exception as e:
                    results.append(ImageProcessResult(success=False, file_path=p, error_message=str(e), task_id=task_id, original_name=n))

        return results

    @require_api_key
    async def remove_image_text(self, files: List[Tuple[str, Optional[str]]]) -> List[ImageProcessResult]:
        """
        去除文字（OCRPP + mask + /tasks/visual/watermark）：
        - 先调用 OCRPP 获取文字框坐标（type=2, box=1）
        - 生成与原图同尺寸的 mask（白色=修复区域；黑色=保留区域），PNG base64
        - 调用 /tasks/visual/watermark，传 mask_base64 + image_* 三选一
        """
        items = self._normalize_image_inputs(files)
        if not items:
            return []

        results: List[ImageProcessResult] = []

        async with httpx.AsyncClient(timeout=3600.0) as client:
            for p0, n0 in items:
                task_id: Optional[str] = None
                try:
                    p = self._normalize_local_path(p0)

                    # 1) 获取原图尺寸（用于生成同尺寸 mask）
                    size = await self._get_image_size(client, p)
                    if not size:
                        await self.logger.error(
                            f"无法获取图片尺寸。请使用可直接读取的图片URL（http/https）或本地文件路径。path: {p}"
                        )
                    width, height = size

                    # 2) OCRPP：创建任务 + 轮询拿 result
                    old_api_base_url = self.api_base_url
                    self.api_base_url = self.ocrpp_url
                    try:
                        task_id = await self._create_task(
                            client,
                            p,
                            {"type": 2, "box": 1},
                            response_action="创建OCR任务"
                        )
                        ocr_result = await self._wait_for_task(
                            client,
                            task_id,
                            "OCR识别",
                            result_field="result",
                            allow_empty_result=True
                        )
                    finally:
                        self.api_base_url = old_api_base_url

                    boxes = self._extract_ocr_boxes(ocr_result)
                    if not boxes:
                        # 没识别到文字，直接返回原图（不调用修复接口）
                        results.append(ImageProcessResult(success=True, file_path=p0, download_url=p0, task_id=task_id, original_name=n0))
                        continue

                    # 3) 生成 mask_base64（PNG）
                    mask_b64 = self._build_mask_png_base64(width, height, boxes)

                    # 4) /tasks/visual/watermark：创建任务 + 轮询取 data.image
                    watermark_task_id = await self._create_visual_watermark_task_with_mask(
                        client,
                        p,
                        mask_b64
                    )
                    old_api_base_url = self.api_base_url
                    self.api_base_url = self.visual_watermark_url
                    try:
                        out_url = await self._wait_for_task(
                            client,
                            watermark_task_id,
                            "图片去文字",
                            result_field="image"
                        )
                    finally:
                        self.api_base_url = old_api_base_url

                    results.append(ImageProcessResult(success=True, file_path=p0, download_url=out_url, task_id=watermark_task_id, original_name=n0))
                except Exception as e:
                    results.append(ImageProcessResult(success=False, file_path=p0, error_message=str(e), task_id=task_id, original_name=n0))

        return results

    def _normalize_local_path(self, path: str) -> str:
        """将 file:// 形式转换为本地路径字符串（不落盘）。"""
        if isinstance(path, str) and path.startswith("file://"):
            return url2pathname(path.removeprefix("file:"))
        return path

    async def _get_image_size(self, client: httpx.AsyncClient, path: str) -> Optional[tuple[int, int]]:
        """
        获取图片尺寸（width, height）。
        - 本地文件：直接读取头部
        - http/https URL：下载到内存后读取
        """
        try:
            if not isinstance(path, str) or not path:
                return None

            # oss_id:// 无法直接读取原图字节（除非另有下载接口），先返回 None 让上层提示用户
            if self.file_handler.is_oss_id(path):
                return None

            # oss:// 作为业务 URL 可能可用于 API，但不一定能 http 直接下载
            if path.startswith("oss://"):
                return None

            if path.startswith(("http://", "https://")):
                resp = await client.get(path)
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content))
                img.load()
                return img.size  # (w, h)

            # local file
            with Image.open(path) as img:
                img.load()
                return img.size
        except Exception:
            return None

    def _extract_ocr_boxes(self, ocr_result) -> List[List[List[int]]]:
        """
        从 OCRPP 轮询结果中提取 box 坐标列表。
        期望格式（示例）：
        {
          "lines": [
            { "box": [[x,y],[x,y],[x,y],[x,y]], "text": "..." },
            ...
          ]
        }
        """
        if not isinstance(ocr_result, dict):
            return []
        lines = ocr_result.get("lines")
        if not isinstance(lines, list):
            return []
        out: List[List[List[int]]] = []
        for ln in lines:
            if not isinstance(ln, dict):
                continue
            box = ln.get("box")
            if (
                isinstance(box, list)
                and len(box) >= 4
                and all(isinstance(pt, list) and len(pt) >= 2 for pt in box[:4])
            ):
                pts: List[List[int]] = []
                ok = True
                for pt in box[:4]:
                    try:
                        x = int(pt[0])
                        y = int(pt[1])
                        pts.append([x, y])
                    except Exception:
                        ok = False
                        break
                if ok:
                    out.append(pts)
        return out

    def _build_mask_png_base64(self, width: int, height: int, boxes: List[List[List[int]]]) -> str:
        """生成 mask PNG base64：白色=修复区域，黑色=非修复区域。"""
        img = Image.new("L", (int(width), int(height)), 0)  # black
        draw = ImageDraw.Draw(img)
        for pts in boxes:
            try:
                poly = [(int(x), int(y)) for x, y in pts]
                draw.polygon(poly, fill=255)
            except Exception:
                continue
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    async def _create_visual_watermark_task_with_mask(self, client: httpx.AsyncClient, path: str, mask_base64: str) -> str:
        """
        创建 /tasks/visual/watermark 任务（带 mask_base64）。
        入参（图片三选一）：
        - image_resource_id：oss_id://{resource_id}
        - image_url：http/https/oss URL
        - image_file：本地文件 multipart
        """
        headers = {"X-API-KEY": self.api_key}

        # oss_id:// -> image_resource_id
        if self.file_handler.is_oss_id(path):
            payload = {"image_resource_id": path.split("oss_id://", 1)[1], "mask_base64": mask_base64}
            h = dict(headers)
            h["Content-Type"] = "application/json"
            resp = await client.post(self.visual_watermark_url, json=payload, headers=h)
            return await self._handle_api_response(resp, "创建去文字任务")

        # URL -> image_url（支持 oss:// / http(s)://）
        if self.file_handler.is_url(path):
            payload = {"image_url": path, "mask_base64": mask_base64}
            h = dict(headers)
            h["Content-Type"] = "application/json"
            resp = await client.post(self.visual_watermark_url, json=payload, headers=h)
            return await self._handle_api_response(resp, "创建去文字任务")

        # Local file -> multipart image_file + mask_base64
        try:
            with open(path, "rb") as f:
                files = {"image_file": f}
                data = {"mask_base64": mask_base64}
                resp = await client.post(self.visual_watermark_url, files=files, data=data, headers=headers)
                return await self._handle_api_response(resp, "创建去文字任务")
        except FileNotFoundError:
            await self.logger.error("文件不存在，无法创建去文字任务。", FileNotFoundError)
            raise

