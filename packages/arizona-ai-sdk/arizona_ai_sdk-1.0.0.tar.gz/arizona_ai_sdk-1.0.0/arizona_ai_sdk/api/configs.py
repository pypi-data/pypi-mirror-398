from typing import List, Optional, TYPE_CHECKING
from arizona_ai_sdk.models.config import Config, ConfigsResponse
from arizona_ai_sdk.types import ConfigScope

if TYPE_CHECKING:
    from arizona_ai_sdk.http_client import HTTPClient


class ConfigsAPI:
    def __init__(self, client: "HTTPClient"):
        self._client = client
    
    def list(self, scope: ConfigScope = "library") -> List[Config]:
        params = {"scope": scope}
        response = self._client.get("configs", params=params)
        configs_response = ConfigsResponse.from_dict(response)
        return configs_response.configs
    
    async def alist(self, scope: ConfigScope = "library") -> List[Config]:
        params = {"scope": scope}
        response = await self._client.aget("configs", params=params)
        configs_response = ConfigsResponse.from_dict(response)
        return configs_response.configs
    
    def get_all(self) -> List[Config]:
        return self.list(scope="all")
    
    async def aget_all(self) -> List[Config]:
        return await self.alist(scope="all")
    
    def get_library(self) -> List[Config]:
        return self.list(scope="library")
    
    async def aget_library(self) -> List[Config]:
        return await self.alist(scope="library")
    
    def find_by_name(self, name: str, scope: ConfigScope = "all") -> Optional[Config]:
        configs = self.list(scope=scope)
        name_lower = name.lower()
        for config in configs:
            if config.name.lower() == name_lower:
                return config
        return None
    
    async def afind_by_name(self, name: str, scope: ConfigScope = "all") -> Optional[Config]:
        configs = await self.alist(scope=scope)
        name_lower = name.lower()
        for config in configs:
            if config.name.lower() == name_lower:
                return config
        return None
