from typing import Optional, TYPE_CHECKING
from arizona_ai_sdk.models.user import UserLimits, TokenValidation, HistoryResponse

if TYPE_CHECKING:
    from arizona_ai_sdk.http_client import HTTPClient


class UserAPI:
    def __init__(self, client: "HTTPClient"):
        self._client = client
    
    def get_limits(self) -> UserLimits:
        response = self._client.get("user/limits")
        return UserLimits.from_dict(response)
    
    async def aget_limits(self) -> UserLimits:
        response = await self._client.aget("user/limits")
        return UserLimits.from_dict(response)
    
    def validate_token(self) -> TokenValidation:
        response = self._client.post("user/token/validate")
        return TokenValidation.from_dict(response)
    
    async def avalidate_token(self) -> TokenValidation:
        response = await self._client.apost("user/token/validate")
        return TokenValidation.from_dict(response)
    
    def get_history(
        self,
        page: int = 1,
        per_page: int = 20,
    ) -> HistoryResponse:
        params = {
            "page": page,
            "per_page": per_page,
        }
        response = self._client.get("user/history", params=params)
        return HistoryResponse.from_dict(response)
    
    async def aget_history(
        self,
        page: int = 1,
        per_page: int = 20,
    ) -> HistoryResponse:
        params = {
            "page": page,
            "per_page": per_page,
        }
        response = await self._client.aget("user/history", params=params)
        return HistoryResponse.from_dict(response)
    
    def can_make_request(self) -> bool:
        limits = self.get_limits()
        return limits.can_make_request()
    
    async def acan_make_request(self) -> bool:
        limits = await self.aget_limits()
        return limits.can_make_request()
    
    def is_valid(self) -> bool:
        try:
            validation = self.validate_token()
            return validation.valid
        except Exception:
            return False
    
    async def ais_valid(self) -> bool:
        try:
            validation = await self.avalidate_token()
            return validation.valid
        except Exception:
            return False
