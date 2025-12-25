from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from arizona_ai_sdk.models.base import BaseModel


@dataclass
class LimitsData(BaseModel):
    per_minute: Optional[int] = None
    per_day: Optional[int] = None


@dataclass
class UsageData(BaseModel):
    used_today: int = 0
    used_last_minute: int = 0


@dataclass
class RemainingData(BaseModel):
    minute: Optional[int] = None
    day: Optional[int] = None


@dataclass
class UserLimits(BaseModel):
    status: str = "success"
    limits: Optional[LimitsData] = None
    usage: Optional[UsageData] = None
    remaining: Optional[RemainingData] = None
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "UserLimits":
        if data is None:
            data = {}
        inner_data = data.get("data", data)
        return cls(
            status=data.get("status", "success"),
            limits=LimitsData.from_dict(inner_data.get("limits")) if inner_data.get("limits") else None,
            usage=UsageData.from_dict(inner_data.get("usage")) if inner_data.get("usage") else None,
            remaining=RemainingData.from_dict(inner_data.get("remaining")) if inner_data.get("remaining") else None
        )
    
    @property
    def requests_remaining_today(self) -> Optional[int]:
        return self.remaining.day if self.remaining else None
    
    @property
    def requests_remaining_minute(self) -> Optional[int]:
        return self.remaining.minute if self.remaining else None
    
    def can_make_request(self) -> bool:
        if self.remaining:
            if self.remaining.minute is not None and self.remaining.minute <= 0:
                return False
            if self.remaining.day is not None and self.remaining.day <= 0:
                return False
        return True


@dataclass
class TokenValidation(BaseModel):
    status: str = "success"
    valid: bool = False
    user_id: Optional[int] = None
    nickname: Optional[str] = None
    role: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "TokenValidation":
        if data is None:
            data = {}
        inner_data = data.get("data", data)
        return cls(
            status=data.get("status", "success"),
            valid=inner_data.get("valid", False),
            user_id=inner_data.get("user_id"),
            nickname=inner_data.get("nickname"),
            role=inner_data.get("role")
        )


@dataclass
class HistoryChat(BaseModel):
    id: str = ""
    title: str = ""
    model: Optional[str] = None
    messages_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class HistoryPagination(BaseModel):
    page: int = 1
    per_page: int = 20
    total: int = 0
    pages: int = 0
    
    @property
    def has_next(self) -> bool:
        return self.page < self.pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1


@dataclass
class HistoryResponse(BaseModel):
    status: str = "success"
    chats: List[HistoryChat] = field(default_factory=list)
    pagination: Optional[HistoryPagination] = None
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "HistoryResponse":
        if data is None:
            data = {}
        inner_data = data.get("data", data)
        chats_data = inner_data.get("chats", [])
        chats = [HistoryChat.from_dict(c) for c in chats_data]
        pagination_data = inner_data.get("pagination")
        pagination = HistoryPagination.from_dict(pagination_data) if pagination_data else None
        return cls(
            status=data.get("status", "success"),
            chats=chats,
            pagination=pagination
        )
    
    def __iter__(self):
        return iter(self.chats)
    
    def __len__(self):
        return len(self.chats)
