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
