from typing import Optional, List, Union, Dict, Any, AsyncIterator, Callable, TYPE_CHECKING
from arizona_ai_sdk.models.chat import (
    Message,
    ChatCompletion,
    ChatCompletionChunk,
    Attachment,
    Usage,
)

if TYPE_CHECKING:
    from arizona_ai_sdk.http_client import HTTPClient


class ChatAPI:
    def __init__(self, client: "HTTPClient"):
        self._client = client
    
    def _prepare_messages(
        self,
        messages: Union[str, List[Message], List[Dict[str, str]]],
    ) -> tuple:
        content = None
        messages_list = None
        
        if isinstance(messages, str):
            content = messages
        elif isinstance(messages, list):
            messages_list = []
            for msg in messages:
                if isinstance(msg, Message):
                    messages_list.append(msg.to_dict())
                elif isinstance(msg, dict):
                    messages_list.append(msg)
        
        return content, messages_list
    
    def _prepare_attachments(
        self,
        attachments: Optional[List[Union[Attachment, Dict[str, str]]]] = None,
    ) -> Optional[List[Dict[str, str]]]:
        if not attachments:
            return None
        
        result = []
        for att in attachments:
            if isinstance(att, Attachment):
                result.append(att.to_dict())
            elif isinstance(att, dict):
                result.append(att)
        return result
    
    def completions(
        self,
        messages: Union[str, List[Message], List[Dict[str, str]]],
        model: str = "arizona-lm-forum",
        temperature: Optional[float] = None,
        config_id: Optional[str] = None,
        attachments: Optional[List[Union[Attachment, Dict[str, str]]]] = None,
    ) -> ChatCompletion:
        content, messages_list = self._prepare_messages(messages)
        prepared_attachments = self._prepare_attachments(attachments)
        
        payload: Dict[str, Any] = {
            "model": model,
            "stream": False,
        }
        
        if content:
            payload["content"] = content
        if messages_list:
            payload["messages"] = messages_list
        if temperature is not None:
            payload["temperature"] = temperature
        if config_id:
            payload["config_id"] = config_id
        if prepared_attachments:
            payload["attachments"] = prepared_attachments
        
        response = self._client.post("chat/completions", json_data=payload)
        return ChatCompletion.from_dict(response)
    
    async def acompletions(
        self,
        messages: Union[str, List[Message], List[Dict[str, str]]],
        model: str = "arizona-lm-forum",
        temperature: Optional[float] = None,
        config_id: Optional[str] = None,
        attachments: Optional[List[Union[Attachment, Dict[str, str]]]] = None,
    ) -> ChatCompletion:
        content, messages_list = self._prepare_messages(messages)
        prepared_attachments = self._prepare_attachments(attachments)
        
        payload: Dict[str, Any] = {
            "model": model,
            "stream": False,
        }
        
        if content:
            payload["content"] = content
        if messages_list:
            payload["messages"] = messages_list
        if temperature is not None:
            payload["temperature"] = temperature
        if config_id:
            payload["config_id"] = config_id
        if prepared_attachments:
            payload["attachments"] = prepared_attachments
        
        response = await self._client.apost("chat/completions", json_data=payload)
        return ChatCompletion.from_dict(response)
    
    def stream(
        self,
        messages: Union[str, List[Message], List[Dict[str, str]]],
        model: str = "arizona-lm-forum",
        temperature: Optional[float] = None,
        config_id: Optional[str] = None,
        attachments: Optional[List[Union[Attachment, Dict[str, str]]]] = None,
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        content, messages_list = self._prepare_messages(messages)
        prepared_attachments = self._prepare_attachments(attachments)
        
        payload: Dict[str, Any] = {
            "model": model,
            "stream": True,
        }
        
        if content:
            payload["content"] = content
        if messages_list:
            payload["messages"] = messages_list
        if temperature is not None:
            payload["temperature"] = temperature
        if config_id:
            payload["config_id"] = config_id
        if prepared_attachments:
            payload["attachments"] = prepared_attachments
        
        def chunk_callback(data: Dict[str, Any]) -> None:
            if callback:
                choices = data.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content_chunk = delta.get("content", "")
                    if content_chunk:
                        callback(content_chunk)
        
        return self._client.stream("chat/completions", json_data=payload, callback=chunk_callback)
    
    async def astream(
        self,
        messages: Union[str, List[Message], List[Dict[str, str]]],
        model: str = "arizona-lm-forum",
        temperature: Optional[float] = None,
        config_id: Optional[str] = None,
        attachments: Optional[List[Union[Attachment, Dict[str, str]]]] = None,
    ) -> AsyncIterator[ChatCompletionChunk]:
        content, messages_list = self._prepare_messages(messages)
        prepared_attachments = self._prepare_attachments(attachments)
        
        payload: Dict[str, Any] = {
            "model": model,
            "stream": True,
        }
        
        if content:
            payload["content"] = content
        if messages_list:
            payload["messages"] = messages_list
        if temperature is not None:
            payload["temperature"] = temperature
        if config_id:
            payload["config_id"] = config_id
        if prepared_attachments:
            payload["attachments"] = prepared_attachments
        
        async for data in self._client.astream("chat/completions", json_data=payload):
            yield ChatCompletionChunk.from_dict(data)
    
    async def astream_text(
        self,
        messages: Union[str, List[Message], List[Dict[str, str]]],
        model: str = "arizona-lm-forum",
        temperature: Optional[float] = None,
        config_id: Optional[str] = None,
        attachments: Optional[List[Union[Attachment, Dict[str, str]]]] = None,
    ) -> AsyncIterator[str]:
        async for chunk in self.astream(messages, model, temperature, config_id, attachments):
            if chunk.content:
                yield chunk.content
    
    def create(
        self,
        messages: Union[str, List[Message], List[Dict[str, str]]],
        model: str = "arizona-lm-forum",
        stream: bool = False,
        temperature: Optional[float] = None,
        config_id: Optional[str] = None,
        attachments: Optional[List[Union[Attachment, Dict[str, str]]]] = None,
        callback: Optional[Callable[[str], None]] = None,
    ) -> Union[ChatCompletion, str]:
        if stream:
            return self.stream(messages, model, temperature, config_id, attachments, callback)
        return self.completions(messages, model, temperature, config_id, attachments)
    
    async def acreate(
        self,
        messages: Union[str, List[Message], List[Dict[str, str]]],
        model: str = "arizona-lm-forum",
        stream: bool = False,
        temperature: Optional[float] = None,
        config_id: Optional[str] = None,
        attachments: Optional[List[Union[Attachment, Dict[str, str]]]] = None,
    ) -> Union[ChatCompletion, AsyncIterator[ChatCompletionChunk]]:
        if stream:
            return self.astream(messages, model, temperature, config_id, attachments)
        return await self.acompletions(messages, model, temperature, config_id, attachments)
