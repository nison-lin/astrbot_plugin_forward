from datetime import datetime
import base64
import os
import re
from PIL import Image as ima

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api.message_components import Plain, Image, Node
from astrbot.builtin_stars.astrbot_plugin_forward.llm_client import LLMClientWrapper
import astrbot.api.message_components as Comp


text_prompt = """你是一个辨别离谱消息的助手，请分辨用户的消息是普通的聊天还是离谱或有意思的事件

你回答的格式必须是“是”或“不是”二者之一。如果用户的消息是离谱或有意思的完整事件，则回答“是”，否则回答“不是”。


重要：
    1.你必须分析用户的输入，不能自己编造消息
    2.你必须严格按照上述格式输出，不能有多余的文字
    3.如果你不能完全理解用户消息，或者用户消息缺少上下文，不完整，则回答“不是”
"""


image_prompt = """你是一个辨别美少女图片的机器人，请分辨用户的图片描述是性感或可爱的美少女图片还是新闻、游戏或其他图片

你回答的格式必须是“是”或“不是”二者之一。如果用户的描述是性感或可爱的美少女图片，则回答“是”，否则回答“不是”。


重要：
    1.你必须分析用户的输入，不能自己编造图片描述
    2.你必须严格按照上述格式输出，不能有多余的文字
    3.如果图片中有美少女元素，但很可能是游戏界面或其他图片，则回答“不是”
"""


class ForwardPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.llm = LLMClientWrapper()
        # 参数配置
        self.TARGET_GROUP_ID = "1106585797"
        self.MAX_SIZE_KB = 500
        

    # 监听所有消息
    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_group_message(self, event: AstrMessageEvent):

        #检查消息来源，防止重复转发
        if event.get_group_id() == self.TARGET_GROUP_ID:
            return
        
        # 调用LLM，判断消息该不该被转发
        try:
            user_input = event.get_messages()
            if isinstance(user_input[0], Node):
                node = user_input[0]
                result = await self.node_check(node=node, event=event)
                if result == True:
                    event.message_obj.group_id = self.TARGET_GROUP_ID
                    self.log("识别到史，已转发")
                    yield event.chain_result(user_input)
                elif result.startswith("正常："):
                    self.log(str(result[3:]))
                else:
                    self.warning(str(result))

            elif isinstance(user_input[0], Image):
                image = user_input[0]
                result = await self.image_check(image=image, event=event)
                if result == True:
                    event.message_obj.group_id = self.TARGET_GROUP_ID
                    self.log("识别到涩图，已转发")
                    yield event.chain_result(user_input)
                elif result.startswith("正常："):
                    self.log(str(result[3:]))
                else:
                    self.warning(str(result))
            
        except Exception as e:
            self.warning(str(e))


    # 合并消息：有文本则看文本，没有文本则看第一张图片
    async def node_check(self, node: Node, event:AstrMessageEvent):
        result = "合并消息解析失败"
        have_checked_image = False
        for comp in node.content:
            if isinstance(comp, Plain):
                total_plain = self.total_text_in_node(node=node, event=event)
                result = await self.plain_check(plain=total_plain, event=event)
                break
            if isinstance(comp, Image):
                if not have_checked_image:
                    result = await self.image_check(image=comp, event=event)
                    have_checked_image = True
            if isinstance(comp, Node):
                result = await self.node_check(node=comp, event=event)
        return result


    # 判断文本是不是史
    async def plain_check(self, plain: str, event: AstrMessageEvent):
        if not plain:
            return "无文本数据"
        response = await self.llm.think_without_tools(
                messages=[{"role": "system", "content": text_prompt}, {"role": "user", "content": plain}]
            )
        if "是" == response.strip():
            return True
        elif "不是" == response.strip():
            return "正常：LLM认为不是史"
        else:
            return "LLM异常回复：" + response

    
    # 判断图片是不是涩图
    async def image_check(self, image: Image, event: AstrMessageEvent):
        # 检查图片有效性
        if not image.file and not image.url and not image.path:
            return "图片无法访问"
        path = image.path or await image.convert_to_file_path()
        if path:
            if self.get_image_format(path) == "不是图片":
                return "正常：不是图片"
            path = self.compress_image_if_needed(path)

        # 排除表情包
        raw_msg = event.message_obj.raw_message.get("raw_message")
        if raw_msg:
            match = re.search(r'sub_type=(\d+)', raw_msg)
            if match and match.group(1) == "1":
                return "正常：是表情包"

        # 构造LLM请求
        messages = []
        if image.url:
            messages = [
                {
                    "role": "system",
                    "content": image_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请分辨这张图片是不是美少女图片",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image.url,
                            },
                        },
                    ]
                }
            ]
        elif path:
            image_format = self.get_image_format(path)
            with open(path, "rb") as f:
                raw_base64 = base64.b64encode(f.read()).decode("utf-8")
            data_url = f"data:image/{image_format};base64,{raw_base64}"
            messages = [
                {
                    "role": "system",
                    "content": image_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请分辨这张图片是不是美少女图片",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url,
                            },
                        },
                    ],
                }
            ]

        # 执行LLM请求
        if not messages:
            return "图片无法访问"
        response = await self.llm.think_without_tools(
                messages=messages,
                model="qwen3.5-flash"
            )
        if "是" == response.strip():
            return True
        elif "不是" == response.strip():
            return "正常：LLM认为不是涩图"
        else:
            return "LLM异常回复：" + response
        
        
    # 汇总合并消息中的文本
    def total_text_in_node(self, node: Node, event:AstrMessageEvent):
        total_text = []
        for comp in node.content:
            if isinstance(comp, Plain):
                total_text.append(comp.text)
            if isinstance(comp, Node):
                total_text.append(self.total_text_in_node(node=comp, event=event))
        return "\n".join(total_text)

            
    # 如果图片超过 MAX_SIZE_KB，压缩后保存为新文件并返回新路径
    def compress_image_if_needed(self, path: str) -> str:
        if os.path.getsize(path) <= self.MAX_SIZE_KB * 1024:
            return path
        base, _ = os.path.splitext(path)
        output_path = base + "_compressed.jpg"
        img = ima.open(path).convert("RGB")
        quality = 85
        img.save(output_path, "JPEG", quality=quality, optimize=True)
        while os.path.getsize(output_path) > self.MAX_SIZE_KB * 1024 and quality > 20:
            quality -= 10
            img.save(output_path, "JPEG", quality=quality, optimize=True)
        return output_path


    # 判断图片类型
    def get_image_format(self, url_or_path: str) -> str:
        if url_or_path.endswith('.jpg') or url_or_path.endswith('.jpeg'):
            return 'jpg'
        elif url_or_path.endswith('.png'):
            return 'png'
        elif url_or_path.endswith('.webp'):
            return 'webp'
        else:
            return '不是图片'
        

    # 写入日志
    def log(self, log: str):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(script_dir, 'log.txt')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]  ' + log + '\n')

    
    # 写入警告
    def warning(self, warning: str):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(script_dir, 'warning.txt')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]  ' + warning + '\n')