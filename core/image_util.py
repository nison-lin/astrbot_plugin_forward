import os
import re
from PIL import Image as ima

from astrbot.core.message.components import Image
from astrbot.core.platform.astr_message_event import AstrMessageEvent

from ..llm.llm_client import LLMClient


image_prompt = """你是一个识别图片的助手，请判断以下一张或多张图片中是否有满足要求的图片

你回答的格式必须是“是”或“不是”二者之一。如果有满足要求的图片，则回答“是”，否则回答“不是”。


重要：
    1.你必须分析图片，不能自己编造图片描述
    2.你必须严格按照上述格式输出，不能有多余的文字
    3.即使有部分图片不满足要求，只要有一张满足要求，则回答“是”

要求：
{prompt}
"""


class ImageUtil:
    def __init__(self, max_size_kb: int, max_dimension: int, prompt: str):
        self.max_size_kb = max_size_kb
        self.prompt = prompt
        self.max_dimension = max_dimension


    # ai匹配图片
    async def ai_image_check(self, images: list[Image], llm: LLMClient, event: AstrMessageEvent):
        # 排除表情包
        try:
            raw_msg = event.message_obj.raw_message.get("raw_message")
            if not raw_msg:
                return False
            cq_codes = re.findall(r'\[CQ:image[^\]]*\]', raw_msg)
            zero_indices = [i for i, cq in enumerate(cq_codes) if 'sub_type=0' in cq]
            images = [image for i, image in enumerate(images) if i in zero_indices]
        except Exception:
            pass

        # 逐一检查图片有效性，并构造url列表
        image_urls = []
        for image in images:
            if not image.file and not image.url and not image.path:
                continue
            path = image.path or await image.convert_to_file_path()
            if path:
                if await self.get_image_format(path) != "不是图片":
                    image_urls.append(await self.process_image(path))
                    continue
            if image.file:
                if image.file.startswith("data:image") or image.file.startswith("base64://"):
                    image_urls.append(image.file)
                    continue
        if not image_urls:
            return False
                
        # 调用ai
        response = await llm.image_think(
                prompt=image_prompt.format(prompt=self.prompt),
                image_urls=image_urls
            )
        if "是" == response.strip():
            return True
        else:
            return False


    # 判断图片类型
    async def get_image_format(self, url_or_path: str) -> str:
        if url_or_path.endswith('.jpg') or url_or_path.endswith('.jpeg'):
            return 'jpg'
        elif url_or_path.endswith('.png'):
            return 'png'
        elif url_or_path.endswith('.webp'):
            return 'webp'
        else:
            return '不是图片'


    # 如果尺寸超过 max_dimension，缩放后保存为新文件并返回新路径
    async def resize_image(self, path: str, img: ima.Image) -> tuple[str, ima.Image]:
        if self.max_dimension <= 0:
            return path, img
        w, h = img.size
        if w <= self.max_dimension and h <= self.max_dimension:
            return path, img
        ratio = min(self.max_dimension / w, self.max_dimension / h)
        img = img.resize((int(w * ratio), int(h * ratio)), ima.Resampling.LANCZOS)
        base, _ = os.path.splitext(path)
        output_path = base + "_resized.jpg"
        img.save(output_path, "JPEG", quality=85, optimize=True)
        return output_path, img


    # 如果文件大小超过 max_size_kb，压缩质量后保存为新文件并返回新路径
    async def compress_image(self, path: str, img: ima.Image) -> str:
        if self.max_size_kb <= 0:
            return path
        if os.path.getsize(path) <= self.max_size_kb * 1024:
            return path
        base, _ = os.path.splitext(path)
        output_path = base + "_compressed.jpg"
        quality = 85
        img.save(output_path, "JPEG", quality=quality, optimize=True)
        while os.path.getsize(output_path) > self.max_size_kb * 1024 and quality > 20:
            quality -= 10
            img.save(output_path, "JPEG", quality=quality, optimize=True)
        return output_path


    # 对图片进行尺寸缩放和大小压缩
    async def process_image(self, path: str) -> str:
        img = ima.open(path).convert("RGB")
        path, img = await self.resize_image(path, img)
        path = await self.compress_image(path, img)
        return path
