import re

from ..llm.llm_client import LLMClient


text_prompt = """你是一个识别消息内容的助手，请根据消息内容，判断该消息是不是用户要匹配的消息

你回答的格式必须是“是”或“不是”二者之一。如果该消息是用户要匹配的消息，则回答“是”，否则回答“不是”。


重要：
    1.你必须分析消息内容，不能自己编造消息
    2.你必须严格按照上述格式输出，不能有多余的文字
    3.如果你不能完全理解用户消息，或者用户消息缺少上下文，不完整，则回答“不是”

用户要匹配的消息：
{prompt}

消息内容：
{plain}
"""


class PlainUtil:
    def __init__(self, key_word: str = "", regex: str = "", prompt: str = ""):
        self.regex = regex
        self.prompt = prompt
        self.key_word = key_word

    # 关键词匹配文本
    async def key_word_plain_check(self, plain: str):
        if not plain or not self.key_word:
            return False
        if self.key_word in plain:
            return True
        return False

    # 正则表达式匹配文本
    async def regex_plain_check(self, plain: str):
        if not plain or not self.regex:
            return False
        if re.search(self.regex, plain):
            return True
        return False

    # ai匹配文本
    async def ai_plain_check(self, plain: str, llm: LLMClient):
        if not self.prompt or not plain:
            return False
        response = await llm.text_think(
            prompt=text_prompt.format(prompt=self.prompt, plain=plain)
        )
        if "是" == response.strip():
            return True
        else:
            return False
