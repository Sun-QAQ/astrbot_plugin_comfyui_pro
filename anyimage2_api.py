import aiohttp
import base64
import json
from astrbot.api import logger


class AnyImage2ImageAPI:
    """AnyImage2 图片生成客户端，接口与 ComfyUI/Gitee 保持一致"""

    def __init__(self, config: dict) -> None:
        any_conf = config.get("anyimage2_settings", {})
        self.api_key = any_conf.get("api_key", "")
        self.base_url = any_conf.get(
            "base_url", "https://a-ocnfniawgw.cn-shanghai.fcapp.run/v1/responses"
        )
        self.model = any_conf.get("model", "gpt-5.3-codex")
        self.size = str(any_conf.get("size", "1024x1024")).strip() or "1024x1024"
        self.quality = str(any_conf.get("quality", "high")).strip() or "high"
        self.output_format = str(any_conf.get("output_format", "png")).strip() or "png"

        if not self.api_key:
            logger.warning("[AnyImage2 API] 未配置 api_key，生图将会失败")

        logger.info(
            f"[AnyImage2 API] 已加载 | 模型: {self.model} | 尺寸: {self.size} | "
            f"质量: {self.quality} | 格式: {self.output_format}"
        )

    def _build_tool(self, action: str):
        return {
            "type": "image_generation",
            "action": action,
            "size": self.size,
            "quality": self.quality,
            "output_format": self.output_format,
        }

    def _build_payload(self, prompt: str, image_data_url: str | None = None):
        if image_data_url:
            content = [
                {"type": "input_image", "image_url": image_data_url},
                {"type": "input_text", "text": prompt},
            ]
            input_field = [{"role": "user", "content": content}]
            action = "edit"
        else:
            input_field = f"Use the following text as the complete prompt. Do not rewrite it:\n{prompt}"
            action = "generate"

        return {
            "model": self.model,
            "input": input_field,
            "tools": [self._build_tool(action)],
            "tool_choice": "required",
            "stream": True,
        }

    def _to_data_url(self, filename: str, raw: bytes) -> str:
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "png"
        mime_map = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
            "gif": "image/gif",
            "bmp": "image/bmp",
        }
        mime = mime_map.get(ext, "image/png")
        b64 = base64.b64encode(raw).decode("utf-8")
        return f"data:{mime};base64,{b64}"

    def _decode_possible_base64(self, value: str):
        if not value or not isinstance(value, str):
            return None

        payload = value
        if value.startswith("data:") and "," in value:
            payload = value.split(",", 1)[1]

        try:
            return base64.b64decode(payload)
        except Exception:
            return None

    def _extract_image_from_obj(self, data_obj):
        if isinstance(data_obj, dict):
            for key, value in data_obj.items():
                if key == "result" and isinstance(value, str):
                    decoded = self._decode_possible_base64(value)
                    if decoded:
                        return decoded, None
                if key in ("url", "image_url", "file_url") and isinstance(value, str):
                    if value.startswith("http"):
                        return None, value
                found = self._extract_image_from_obj(value)
                if found != (None, None):
                    return found
        elif isinstance(data_obj, list):
            for item in data_obj:
                found = self._extract_image_from_obj(item)
                if found != (None, None):
                    return found
        return None, None

    async def _download_image(self, session: aiohttp.ClientSession, url: str):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    return None, f"下载图片失败: HTTP {resp.status}"
                return await resp.read(), None
        except Exception as e:
            return None, f"下载图片失败: {e}"

    async def _request_image(self, payload: dict):
        if not self.api_key:
            return None, "AnyImage2 API Key 未配置，请在插件设置中填写"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "accept": "text/event-stream",
        }

        timeout = aiohttp.ClientTimeout(total=180)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(
                            f"[AnyImage2 API] 请求失败 HTTP {resp.status}: {text[:200]}"
                        )
                        return None, f"AnyImage2 API 请求失败: HTTP {resp.status}"

                    content_type = (resp.headers.get("Content-Type") or "").lower()

                    if "text/event-stream" in content_type:
                        while not resp.content.at_eof():
                            line = await resp.content.readline()
                            if not line:
                                continue

                            decoded_line = line.decode("utf-8", errors="ignore").strip()
                            if not decoded_line or not decoded_line.startswith("data:"):
                                continue

                            data_str = decoded_line[5:].strip()
                            if not data_str or data_str == "[DONE]":
                                continue

                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            img_bytes, url = self._extract_image_from_obj(data)
                            if img_bytes:
                                return img_bytes, None
                            if url:
                                return await self._download_image(session, url)

                        return None, "AnyImage2 未返回图片数据"

                    data = await resp.json()
                    img_bytes, url = self._extract_image_from_obj(data)
                    if img_bytes:
                        return img_bytes, None
                    if url:
                        return await self._download_image(session, url)
                    return None, "AnyImage2 响应中未找到图片数据"

        except aiohttp.ClientError as e:
            logger.error(f"[AnyImage2 API] 网络错误: {e}")
            return None, f"网络错误: {e}"
        except Exception as e:
            logger.error(f"[AnyImage2 API] 未知错误: {e}")
            return None, f"生成失败: {e}"

    async def generate(self, prompt: str):
        payload = self._build_payload(prompt)
        return await self._request_image(payload)

    async def edit(self, prompt: str, image_bytes_list: list[tuple[str, bytes]]):
        if not image_bytes_list:
            return None, "未提供图片"

        filename, raw = image_bytes_list[0]
        image_data_url = self._to_data_url(filename, raw)
        edit_prompt = (
            "请根据以下要求，对我提供的这张图片进行编辑修改，"
            f"直接生成修改后的新图片。要求：{prompt}"
        )
        payload = self._build_payload(edit_prompt, image_data_url=image_data_url)
        return await self._request_image(payload)
