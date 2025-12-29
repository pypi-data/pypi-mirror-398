"""
LangChain compatibility wrapper for browser-use 0.11.x

Browser-use moved away from native langchain support and now uses its own
BaseChatModel protocol. This module provides the ChatLangchain wrapper
to adapt any langchain model for use with browser-use.

Based on: https://github.com/browser-use/browser-use/tree/main/examples/models/langchain
"""

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar, overload

from pydantic import BaseModel

from browser_use.llm.base import BaseChatModel
from browser_use.llm.exceptions import ModelProviderError
from browser_use.llm.messages import (
    AssistantMessage,
    BaseMessage,
    ContentPartImageParam,
    ContentPartRefusalParam,
    ContentPartTextParam,
    ToolCall,
    UserMessage,
)
from browser_use.llm.messages import SystemMessage as BrowserUseSystemMessage
from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel as LangChainBaseChatModel
    from langchain_core.messages import AIMessage as LangChainAIMessage

T = TypeVar('T', bound=BaseModel)


class LangChainMessageSerializer:
    """Serializer for converting between browser-use message types and LangChain message types."""

    @staticmethod
    def _serialize_user_content(
        content: str | list[ContentPartTextParam | ContentPartImageParam],
    ) -> str | list[str | dict]:
        if isinstance(content, str):
            return content

        serialized_parts = []
        for part in content:
            if part.type == 'text':
                serialized_parts.append({
                    'type': 'text',
                    'text': part.text,
                })
            elif part.type == 'image_url':
                serialized_parts.append({
                    'type': 'image_url',
                    'image_url': {'url': part.image_url.url, 'detail': part.image_url.detail}
                })

        return serialized_parts

    @staticmethod
    def _serialize_system_content(content: str | list[ContentPartTextParam]) -> str:
        if isinstance(content, str):
            return content

        text_parts = []
        for part in content:
            if part.type == 'text':
                text_parts.append(part.text)

        return '\n'.join(text_parts)

    @staticmethod
    def _serialize_assistant_content(
        content: str | list[ContentPartTextParam | ContentPartRefusalParam] | None,
    ) -> str:
        if content is None:
            return ''
        if isinstance(content, str):
            return content

        text_parts = []
        for part in content:
            if part.type == 'text':
                text_parts.append(part.text)

        return '\n'.join(text_parts)

    @staticmethod
    def _serialize_tool_call(tool_call: ToolCall):
        from langchain_core.messages import ToolCall as LangChainToolCall
        try:
            args_dict = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            args_dict = {'arguments': tool_call.function.arguments}

        return LangChainToolCall(
            name=tool_call.function.name,
            args=args_dict,
            id=tool_call.id,
        )

    @staticmethod
    def serialize(message: BaseMessage):
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        if isinstance(message, UserMessage):
            content = LangChainMessageSerializer._serialize_user_content(message.content)
            return HumanMessage(content=content, name=message.name)

        elif isinstance(message, BrowserUseSystemMessage):
            content = LangChainMessageSerializer._serialize_system_content(message.content)
            return SystemMessage(content=content, name=message.name)

        elif isinstance(message, AssistantMessage):
            content = LangChainMessageSerializer._serialize_assistant_content(message.content)
            return AIMessage(content=content, name=message.name)

        else:
            raise ValueError(f'Unknown message type: {type(message)}')

    @staticmethod
    def serialize_messages(messages: list[BaseMessage]) -> list:
        return [LangChainMessageSerializer.serialize(m) for m in messages]


@dataclass
class ChatLangchain(BaseChatModel):
    """
    Wrapper around LangChain BaseChatModel that implements browser-use BaseChatModel protocol.
    This allows using any LangChain-compatible model with browser-use 0.11.x+
    """

    chat: 'LangChainBaseChatModel'

    @property
    def model(self) -> str:
        return self.name

    @property
    def provider(self) -> str:
        model_class_name = self.chat.__class__.__name__.lower()
        if 'openai' in model_class_name:
            base_url = getattr(self.chat, 'openai_api_base', None) or getattr(self.chat, 'base_url', None)
            if base_url and 'openrouter.ai' in str(base_url):
                return 'openrouter'
            return 'openai'
        elif 'anthropic' in model_class_name or 'claude' in model_class_name:
            return 'anthropic'
        elif 'google' in model_class_name or 'gemini' in model_class_name:
            return 'google'
        elif 'groq' in model_class_name:
            return 'groq'
        elif 'ollama' in model_class_name:
            return 'ollama'
        elif 'deepseek' in model_class_name:
            return 'deepseek'
        else:
            return 'langchain'

    @property
    def name(self) -> str:
        model_name = getattr(self.chat, 'model_name', None)
        if model_name:
            return str(model_name)

        model_attr = getattr(self.chat, 'model', None)
        if model_attr:
            return str(model_attr)

        return self.chat.__class__.__name__

    def _get_usage(self, response: 'LangChainAIMessage') -> ChatInvokeUsage | None:
        usage = getattr(response, 'usage_metadata', None)
        if usage is None:
            return None

        prompt_tokens = usage.get('input_tokens', 0) or 0
        completion_tokens = usage.get('output_tokens', 0) or 0
        total_tokens = usage.get('total_tokens', 0) or 0

        input_token_details = usage.get('input_token_details', None)

        if input_token_details is not None:
            prompt_cached_tokens = input_token_details.get('cache_read', None)
            prompt_cache_creation_tokens = input_token_details.get('cache_creation', None)
        else:
            prompt_cached_tokens = None
            prompt_cache_creation_tokens = None

        return ChatInvokeUsage(
            prompt_tokens=prompt_tokens,
            prompt_cached_tokens=prompt_cached_tokens,
            prompt_cache_creation_tokens=prompt_cache_creation_tokens,
            prompt_image_tokens=None,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    @overload
    async def ainvoke(self, messages: list[BaseMessage], output_format: None = None, **kwargs) -> ChatInvokeCompletion[str]: ...

    @overload
    async def ainvoke(self, messages: list[BaseMessage], output_format: type[T], **kwargs) -> ChatInvokeCompletion[T]: ...

    async def ainvoke(
        self, messages: list[BaseMessage], output_format: type[T] | None = None, **kwargs
    ) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
        langchain_messages = LangChainMessageSerializer.serialize_messages(messages)

        try:
            if output_format is None:
                response = await self.chat.ainvoke(langchain_messages)

                from langchain_core.messages import AIMessage as LangChainAIMessage

                if not isinstance(response, LangChainAIMessage):
                    raise ModelProviderError(
                        message=f'Response is not an AIMessage: {type(response)}',
                        model=self.name,
                    )

                content = response.content if hasattr(response, 'content') else str(response)

                usage = self._get_usage(response)
                return ChatInvokeCompletion(
                    completion=str(content),
                    usage=usage,
                )

            else:
                try:
                    structured_chat = self.chat.with_structured_output(output_format)
                    parsed_object = await structured_chat.ainvoke(langchain_messages)

                    usage = None

                    return ChatInvokeCompletion(
                        completion=parsed_object,
                        usage=usage,
                    )
                except (AttributeError, NotImplementedError):
                    response = await self.chat.ainvoke(langchain_messages)

                    from langchain_core.messages import AIMessage as LangChainAIMessage

                    if not isinstance(response, LangChainAIMessage):
                        raise ModelProviderError(
                            message=f'Response is not an AIMessage: {type(response)}',
                            model=self.name,
                        )

                    content = response.content if hasattr(response, 'content') else str(response)

                    try:
                        if isinstance(content, str):
                            parsed_data = json.loads(content)
                            if isinstance(parsed_data, dict):
                                parsed_object = output_format(**parsed_data)
                            else:
                                raise ValueError('Parsed JSON is not a dictionary')
                        else:
                            raise ValueError('Content is not a string and structured output not supported')
                    except Exception as e:
                        raise ModelProviderError(
                            message=f'Failed to parse response as {output_format.__name__}: {e}',
                            model=self.name,
                        ) from e

                    usage = self._get_usage(response)
                    return ChatInvokeCompletion(
                        completion=parsed_object,
                        usage=usage,
                    )

        except ModelProviderError:
            raise
        except Exception as e:
            raise ModelProviderError(
                message=f'LangChain model error: {str(e)}',
                model=self.name,
            ) from e
