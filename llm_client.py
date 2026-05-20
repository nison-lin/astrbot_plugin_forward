import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

class LLMClientWrapper:

    def __init__(self, model: Optional[str] = None, apiKey: Optional[str] = None, baseUrl: Optional[str] = None, timeout: Optional[int] = None):
        """
        初始化客户端。优先使用传入参数，如果未提供，则从环境变量加载。
        """
        self.model = model or os.getenv("LLM_MODEL_ID", "")
        apiKey = apiKey or os.getenv("LLM_API_KEY", "")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL", "")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        if not all([self.model, apiKey, baseUrl]):
            return "模型ID、API密钥和服务地址必须被提供或在.env文件中定义。"

        self.client = AsyncOpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    async def think_without_tools(self, messages: List[Dict], temperature: float = 0, model: str = "") -> str:

        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = await self.client.chat.completions.create(
                model=model if model else self.model,
                messages=messages, # type: ignore
                temperature=temperature
            )

            
            # 处理非流式响应
            if not response.choices:
                print(f"❌ 模型响应中没有choices。")
                return f"模型响应中没有choices。"
            if response.choices[0].message.content:
                return response.choices[0].message.content
            else:
                return "模型返回结果为空"
           
        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return f"调用LLM API时发生错误: {e}"
        
    async def think_with_tools(self, messages: List[Dict], temperature: float = 0, tools: list[dict] | None = None):
        if tools is None:
            tools = []

        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages, # type: ignore
                temperature=temperature,
                stream=False,
                tools=tools, # type: ignore
                tool_choice="auto"
            )

            result = response.choices[0].message
            if result.tool_calls:
                print("✅ 大语言模型响应成功,调用了函数:")
                for tool_call in result.tool_calls:
                    print(f"   - {tool_call.function.name}")
                    print(tool_call.function.arguments)
                return result
            if result.content:
                print("✅ 大语言模型响应成功,未调用函数。")
                return result
            print(f"❌ 模型响应中既没有内容也没有工具调用。")
            return f"模型响应中既没有内容也没有工具调用。"

        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return f"调用LLM API时发生错误: {e}"