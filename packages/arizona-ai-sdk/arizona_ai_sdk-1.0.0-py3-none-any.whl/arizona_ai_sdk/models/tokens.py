from dataclasses import dataclass
from typing import Optional, Dict, Any
from arizona_ai_sdk.models.base import BaseModel


@dataclass
class TokenCount(BaseModel):
    status: str = "success"
    token_count: int = 0
    max_request_tokens: Optional[int] = None
    max_chat_tokens: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "TokenCount":
        if data is None:
            data = {}
        inner_data = data.get("data", data)
        return cls(
            status=data.get("status", "success"),
            token_count=inner_data.get("token_count", 0),
            max_request_tokens=inner_data.get("max_request_tokens"),
            max_chat_tokens=inner_data.get("max_chat_tokens")
        )
    
    @property
    def count(self) -> int:
        return self.token_count
    
    def exceeds_request_limit(self) -> bool:
        if self.max_request_tokens:
            return self.token_count > self.max_request_tokens
        return False
    
    def exceeds_chat_limit(self) -> bool:
        if self.max_chat_tokens:
            return self.token_count > self.max_chat_tokens
        return False
    
    def remaining_request_tokens(self) -> Optional[int]:
        if self.max_request_tokens:
            return self.max_request_tokens - self.token_count
        return None
    
    def remaining_chat_tokens(self) -> Optional[int]:
        if self.max_chat_tokens:
            return self.max_chat_tokens - self.token_count
        return None
