from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api.message_components import Plain, Image
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot import logger

from .core.image_util import ImageUtil
from .core.log_util import LogUtil
from .core.plain_util import PlainUtil
from .llm.llm_client import LLMClient


class ForwardPlugin(Star):
    context: Context

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        # 传入参数
        self.target_group_ids = config.get("target_group_ids", "")
        self.from_group_ids = config.get("from_group_ids", "")
        self.text_enable = config.get("text", {}).get("enable", False)
        self.text_auto_regex = config.get("text", {}).get("auto_regex", "")
        self.text_ai_prompt = config.get("text", {}).get("ai_prompt", "")
        self.image_enable = config.get("image", {}).get("enable", False)
        self.image_ai_prompt = config.get("image", {}).get("ai_prompt", "")
        self.image_max_size_kb = config.get("image", {}).get("max_size_kb", 0)
        self.image_max_dimension = config.get("image", {}).get("max_dimension", 0)
        self.log_enable = config.get("log", {}).get("enable", True)
        self.log_path = config.get("log", {}).get("path", "")
        # 创建工具类
        self.log_util = LogUtil(log_enable=self.log_enable, log_path=self.log_path)
        self.plain_util = PlainUtil(
            regex=self.text_auto_regex, prompt=self.text_ai_prompt
        )
        self.image_util = ImageUtil(
            max_size_kb=self.image_max_size_kb,
            max_dimension=self.image_max_dimension,
            prompt=self.image_ai_prompt,
        )

    # 监听所有消息
    @filter.event_message_type(filter.EventMessageType.ALL)
    async def auto_forward(self, event: AstrMessageEvent):
        try:
            # 禁止默认的LLM请求
            event.should_call_llm(True)

            # 检查消息来源
            if not await self.from_check(event=event):
                return

            # 创建LLM客户端
            llm = None
            if self.text_ai_prompt or self.image_ai_prompt:
                llm = await LLMClient.create(context=self.context, event=event)

            # 开始监测
            messages = event.get_messages()
            if self.text_enable:
                async for r in self.text_check(messages=messages, event=event, llm=llm):
                    yield r
            if self.image_enable:
                async for r in self.image_check(
                    messages=messages, event=event, llm=llm
                ):
                    yield r
        except Exception as e:
            try:
                await self.log_util.warning(str(e))
            except Exception:
                logger.error(f"[auto_forward] {e}")

    # 检查消息来源，只监测指定群聊
    async def from_check(self, event: AstrMessageEvent):
        if not self.from_group_ids:
            return False
        from_group_id_list = ""
        if "," in self.from_group_ids:
            from_group_id_list = self.from_group_ids.strip().split(",")
        elif "，" in self.from_group_ids:
            from_group_id_list = self.from_group_ids.strip().split("，")
        else:
            from_group_id_list = [self.from_group_ids.strip()]
        if str(event.get_group_id()) not in from_group_id_list:
            return False
        return True

    # 纯文本监测
    async def text_check(
        self, messages: list, event: AstrMessageEvent, llm: LLMClient | None
    ):
        for message in messages:
            if not isinstance(message, Plain):
                return
        result = False
        if self.text_auto_regex:
            result = await self.plain_util.regex_plain_check(
                plain=event.get_message_str()
            )
        if self.text_ai_prompt and llm:
            result = (
                await self.plain_util.ai_plain_check(
                    plain=event.get_message_str(), llm=llm
                )
                or result
            )
        if result:
            async for r in self.forward(messages=messages, event=event):
                yield r

    # 图片监测
    async def image_check(
        self, messages: list, event: AstrMessageEvent, llm: LLMClient | None
    ):
        images = []
        for message in messages:
            if isinstance(message, Image):
                images.append(message)
        result = False
        if self.image_ai_prompt and llm:
            result = await self.image_util.ai_image_check(
                images=images, llm=llm, event=event
            )
        if result:
            async for r in self.forward(messages=messages, event=event):
                yield r

    # 转发
    async def forward(self, messages: list, event: AstrMessageEvent):
        if not self.target_group_ids:
            return
        await self.log_util.log("识别到结果，已转发")
        target_group_id_list = ""
        if "," in self.target_group_ids:
            target_group_id_list = self.target_group_ids.strip().split(",")
        elif "，" in self.target_group_ids:
            target_group_id_list = self.target_group_ids.strip().split("，")
        else:
            target_group_id_list = [self.target_group_ids.strip()]
        try:
            for target_group_id in target_group_id_list:
                event.message_obj.group_id = target_group_id
                yield event.chain_result(messages)
        except Exception as e:
            try:
                await self.log_util.warning(str(e))
            except Exception:
                logger.error(f"[auto_forward] {e}")
