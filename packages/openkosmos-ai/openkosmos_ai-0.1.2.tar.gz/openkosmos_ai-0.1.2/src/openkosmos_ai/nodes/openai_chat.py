from typing import Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr


class OpenAIServerConfig(BaseModel):
    base_url: str
    api_key: str
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.8
    presence_penalty: Optional[float] = 1.03


class OpenAIChatNode:
    def __init__(self, server_config: OpenAIServerConfig, tools=None):
        self.llm = ChatOpenAI(
            model=server_config.model,
            base_url=server_config.base_url,
            api_key=SecretStr(server_config.api_key),
            temperature=server_config.temperature,
            top_p=server_config.top_p,
            presence_penalty=server_config.presence_penalty
        )
        if tools is not None:
            self.llm = self.llm.bind_tools(tools)

    def model(self):
        return self.llm

    def invoke(self, messages):
        response = self.llm.invoke(messages)
        return response

    def chat(self, messages):
        response = self.llm.invoke(messages)
        return response.content_blocks
