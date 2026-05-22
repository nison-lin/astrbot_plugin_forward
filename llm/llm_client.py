from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.star.context import Context
from astrbot.core.exceptions import ProviderNotFoundError


class LLMClient:
    def __init__(self, provider_id: str, context: Context):
        self.provider_id = provider_id
        self.context = context


    @classmethod
    async def create(cls, context: Context, event: AstrMessageEvent):
        umo = event.unified_msg_origin
        try:
            provider_id = await context.get_current_chat_provider_id(umo=umo)
        except ProviderNotFoundError:
            return None
        if provider_id:
            return cls(provider_id, context)
        else:
            return None


    # 调用文本LLM
    async def text_think(self, prompt: str, system_prompt: str = ""):
        if not self.provider_id or not prompt:
            return ""
        llm_resp = None
        if system_prompt:
            llm_resp = await self.context.llm_generate(
                chat_provider_id=self.provider_id,
                prompt=prompt,
                system_prompt=system_prompt
            )
        else:
            llm_resp = await self.context.llm_generate(
                chat_provider_id=self.provider_id,
                prompt=prompt
            )
        if llm_resp:
            return llm_resp.completion_text
        else:
            return ""
    

    # 调用图片LLM
    async def image_think(self, prompt: str, image_urls: list[str]):
        if not self.provider_id or not prompt:
            return ""
        llm_resp = None
        llm_resp = await self.context.llm_generate(
                chat_provider_id=self.provider_id,
                prompt=prompt,
                image_urls=image_urls
            )
        if llm_resp:
            return llm_resp.completion_text
        else:
            return ""