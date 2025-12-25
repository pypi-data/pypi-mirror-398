from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from arizona_ai_sdk.models.base import BaseModel


@dataclass
class Attachment(BaseModel):
    name: str = ""
    type: str = ""
    base64: str = ""
    
    @classmethod
    def create(cls, name: str, mime_type: str, base64_data: str) -> "Attachment":
        return cls(name=name, type=mime_type, base64=base64_data)


@dataclass
class Message(BaseModel):
    role: str = "user"
    content: str = ""
    action_steps: Optional[List[Dict[str, Any]]] = None
    thinking: Optional[str] = None
    
    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role="user", content=content)
    
    @classmethod
    def assistant(cls, content: str, action_steps: Optional[List[Dict[str, Any]]] = None) -> "Message":
        return cls(role="assistant", content=content, action_steps=action_steps)
    
    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role="system", content=content)


@dataclass
class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ChatChoice(BaseModel):
    index: int = 0
    message: Optional[Message] = None
    finish_reason: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ChatChoice":
        if data is None:
            data = {}
        message_data = data.get("message")
        message = Message.from_dict(message_data) if message_data else None
        return cls(
            index=data.get("index", 0),
            message=message,
            finish_reason=data.get("finish_reason")
        )


@dataclass
class ChatCompletion(BaseModel):
    status: str = "success"
    choices: List[ChatChoice] = field(default_factory=list)
    usage: Optional[Usage] = None
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ChatCompletion":
        if data is None:
            data = {}
        choices_data = data.get("choices", [])
        choices = [ChatChoice.from_dict(c) for c in choices_data]
        usage_data = data.get("usage")
        usage = Usage.from_dict(usage_data) if usage_data else None
        return cls(
            status=data.get("status", "success"),
            choices=choices,
            usage=usage
        )
    
    @property
    def content(self) -> str:
        if self.choices and self.choices[0].message:
            return self.choices[0].message.content
        return ""
    
    @property
    def message(self) -> Optional[Message]:
        if self.choices:
            return self.choices[0].message
        return None


@dataclass
class DeltaContent(BaseModel):
    content: str = ""
    thinking: Optional[str] = None


@dataclass
class ChatCompletionChunk(BaseModel):
    choices: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ChatCompletionChunk":
        if data is None:
            data = {}
        return cls(choices=data.get("choices", []))
    
    @property
    def delta(self) -> DeltaContent:
        if self.choices:
            delta_data = self.choices[0].get("delta", {})
            return DeltaContent(
                content=delta_data.get("content", ""),
                thinking=delta_data.get("thinking")
            )
        return DeltaContent()
    
    @property
    def content(self) -> str:
        return self.delta.content
    
    @property
    def thinking(self) -> Optional[str]:
        return self.delta.thinking
