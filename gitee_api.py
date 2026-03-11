import asyncio
import aiohttp
import base64
from astrbot.api import logger


class GiteeImageAPI:
    """Gitee AI 图片生成客户端，接口与 ComfyUI 保持一致"""

    def __init__(self, config: dict) -> None:
        gitee_conf = config.get("gitee_settings", {})
        self.api_key = gitee_conf.get("api_key", "")
        self.base_url = "https://ai.gitee.com/v1"
        self.model = gitee_conf.get("model", "z-image-turbo")
        self.negative_prompt = gitee_conf.get("negative_prompt", "")
        self.num_inference_steps = gitee_conf.get("num_inference_steps", 9)
        self.guidance_scale = gitee_conf.get("guidance_scale", 1)
        self.image_scale = gitee_conf.get("image_scale", 1)
        self.edit_model = gitee_conf.get("edit_model", "Qwen-Image-Edit-2511")
        self.edit_num_inference_steps = gitee_conf.get("edit_num_inference_steps", 4)
        self.edit_guidance_scale = gitee_conf.get("edit_guidance_scale", 1)

        if not self.api_key:
            logger.warning("[Gitee API] 未配置 api_key，生图将会失败")

        logger.info(
            f"[Gitee API] 已加载 | 模型: {self.model} | "
            f"步数: {self.num_inference_steps} | guidance: {self.guidance_scale}"
        )

    async def generate(self, prompt: str):
        """
        生成图片，返回 (img_bytes, error_msg)。
        成功时 error_msg 为 None，失败时 img_bytes 为 None。
        """
        if not self.api_key:
            return None, "Gitee API Key 未配置，请在插件设置中填写"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": self.model,
            "prompt": prompt,
        }

        # 构建 extra_body 参数
        extra = {}
        if self.negative_prompt:
            extra["negative_prompt"] = self.negative_prompt
        extra["num_inference_steps"] = self.num_inference_steps
        extra["guidance_scale"] = self.guidance_scale
        extra["image_scale"] = self.image_scale
        body.update(extra)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/images/generations",
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"[Gitee API] 请求失败 HTTP {resp.status}: {text[:200]}")
                        return None, f"Gitee API 请求失败: HTTP {resp.status}"

                    data = await resp.json()

            # 解析响应
            images = data.get("data", [])
            if not images:
                return None, "Gitee API 返回了空的图片列表"

            image_item = images[0]

            # 优先使用 URL 下载
            url = image_item.get("url")
            if url:
                return await self._download_image(url)

            # 其次解码 base64
            b64 = image_item.get("b64_json")
            if b64:
                try:
                    img_bytes = base64.b64decode(b64)
                    return img_bytes, None
                except Exception as e:
                    return None, f"base64 解码失败: {e}"

            return None, "Gitee API 响应中无 url 或 b64_json 字段"

        except aiohttp.ClientError as e:
            logger.error(f"[Gitee API] 网络错误: {e}")
            return None, f"网络错误: {e}"
        except Exception as e:
            logger.error(f"[Gitee API] 未知错误: {e}")
            return None, f"生成失败: {e}"

    async def _download_image(self, url: str):
        """从 URL 下载图片"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status != 200:
                        return None, f"下载图片失败: HTTP {resp.status}"
                    img_bytes = await resp.read()
                    return img_bytes, None
        except Exception as e:
            return None, f"下载图片失败: {e}"

    def _infer_task_types(self, image_count: int) -> list[str]:
        """根据图片数量自动推断 task_types"""
        if image_count >= 2:
            return ["id", "style"]
        return ["id"]

    async def _poll_task(self, session: aiohttp.ClientSession, task_id: str, headers: dict):
        """轮询异步任务直到完成，返回 (img_bytes, error_msg)"""
        url = f"{self.base_url}/task/{task_id}"
        max_attempts = 60  # 10 分钟超时 (60 * 10s)

        for attempt in range(1, max_attempts + 1):
            try:
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.warning(
                            f"[Gitee API] 轮询 #{attempt} HTTP {resp.status}: {text[:200]}"
                        )
                        await asyncio.sleep(10)
                        continue

                    data = await resp.json()

                status = data.get("status", "")
                logger.debug(f"[Gitee API] 轮询 #{attempt} 状态: {status}")

                if status == "success":
                    output = data.get("output", {})
                    file_url = output.get("file_url")
                    if file_url:
                        return await self._download_image(file_url)
                    return None, "任务成功但未返回 file_url"

                if status in ("failed", "cancelled"):
                    error = data.get("error", "未知错误")
                    return None, f"任务{status}: {error}"

            except aiohttp.ClientError as e:
                logger.warning(f"[Gitee API] 轮询 #{attempt} 网络错误: {e}")
            except Exception as e:
                logger.warning(f"[Gitee API] 轮询 #{attempt} 异常: {e}")

            await asyncio.sleep(10)

        return None, "任务超时（等待超过 10 分钟）"

    async def edit(self, prompt: str, image_bytes_list: list[tuple[str, bytes]]):
        """
        图片编辑，返回 (img_bytes, error_msg)。
        image_bytes_list: [(filename, raw_bytes), ...]
        """
        if not self.api_key:
            return None, "Gitee API Key 未配置，请在插件设置中填写"

        if not image_bytes_list:
            return None, "未提供图片"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        task_types = self._infer_task_types(len(image_bytes_list))

        try:
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field("prompt", prompt)
                form.add_field("model", self.edit_model)
                form.add_field("num_inference_steps", str(self.edit_num_inference_steps))
                form.add_field("guidance_scale", str(self.edit_guidance_scale))

                for tt in task_types:
                    form.add_field("task_types", tt)

                for filename, raw_bytes in image_bytes_list:
                    form.add_field(
                        "image",
                        raw_bytes,
                        filename=filename,
                        content_type="application/octet-stream",
                    )

                async with session.post(
                    f"{self.base_url}/async/images/edits",
                    headers=headers,
                    data=form,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"[Gitee API] 改图请求失败 HTTP {resp.status}: {text[:200]}")
                        return None, f"Gitee API 改图请求失败: HTTP {resp.status}"

                    data = await resp.json()

                task_id = data.get("task_id")
                if not task_id:
                    return None, "Gitee API 未返回 task_id"

                logger.info(f"[Gitee API] 改图任务已提交: {task_id}")
                return await self._poll_task(session, task_id, headers)

        except aiohttp.ClientError as e:
            logger.error(f"[Gitee API] 改图网络错误: {e}")
            return None, f"网络错误: {e}"
        except Exception as e:
            logger.error(f"[Gitee API] 改图未知错误: {e}")
            return None, f"改图失败: {e}"
