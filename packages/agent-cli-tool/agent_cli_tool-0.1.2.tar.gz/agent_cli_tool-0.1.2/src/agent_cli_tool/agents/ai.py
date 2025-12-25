from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletion


class BaseAI:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int,
        stream: bool = True,
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> None:
        """
        初始化BaseAI类。

        :param api_key: OpenAI API密钥
        :param base_url: OpenAI API的基础URL
        :param model: 使用的模型名称
        :param timeout: 请求超时时间
        :param stream: 是否使用流式响应，默认为True
        :param tools: 工具列表，默认为NOT_GIVEN
        :param system_prompt: 系统提示信息，默认为None
        :param messages: 初始消息列表，默认为None
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
        self.stream = stream
        self.tools = tools
        self.model = model
        self.messages = (
            messages
            if messages is not None
            else ([self.system_message(system_prompt)] if system_prompt else [])
        )

    def system_message(self, content: str) -> Dict[str, str]:
        """
        创建系统消息。

        :param content: 消息内容
        :return: 包含角色和内容的消息字典
        """
        return {"role": "system", "content": content}

    def user_message(self, content: str) -> Dict[str, str]:
        """
        创建用户消息。

        :param content: 消息内容
        :return: 包含角色和内容的消息字典
        """
        return {"role": "user", "content": content}

    def ai_message(self, content: str) -> Dict[str, str]:
        """
        创建AI助手消息。

        :param content: 消息内容
        :return: 包含角色和内容的消息字典
        """
        return {"role": "assistant", "content": content}

    def tool_message(self, tool_call_id: str, content: str) -> Dict[str, str]:
        """
        创建工具消息。

        :param tool_call_id: 工具调用ID
        :param content: 消息内容
        :return: 包含角色、工具调用ID和内容的消息字典
        """
        return {"role": "tool", "tool_call_id": tool_call_id, "content": content}

    def send_messages(self) -> ChatCompletion:
        """
        发送消息并获取响应。

        :return: OpenAI的ChatCompletion响应对象
        """
        try:
            return self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools,
                stream=self.stream,
            )
        except Exception as e:
            # 处理异常情况，例如网络错误或API错误
            raise RuntimeError(f"Failed to send messages: {e}")
