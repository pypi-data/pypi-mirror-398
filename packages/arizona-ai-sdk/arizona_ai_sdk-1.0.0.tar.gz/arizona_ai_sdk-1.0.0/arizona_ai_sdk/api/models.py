from typing import Optional, List, TYPE_CHECKING
from arizona_ai_sdk.models.model import Model, ModelsResponse

if TYPE_CHECKING:
    from arizona_ai_sdk.http_client import HTTPClient


class ModelsAPI:
    def __init__(self, client: "HTTPClient"):
        self._client = client
    
    def list(self) -> List[Model]:
        response = self._client.get("models")
        models_response = ModelsResponse.from_dict(response)
        return models_response.models
    
    async def alist(self) -> List[Model]:
        response = await self._client.aget("models")
        models_response = ModelsResponse.from_dict(response)
        return models_response.models
    
    def get(self, model_id: str) -> Model:
        response = self._client.get(f"models/{model_id}")
        data = response.get("data", response)
        return Model.from_dict(data)
    
    async def aget(self, model_id: str) -> Model:
        response = await self._client.aget(f"models/{model_id}")
        data = response.get("data", response)
        return Model.from_dict(data)
    
    def get_available(self) -> List[Model]:
        models = self.list()
        return [m for m in models if m.is_available]
    
    async def aget_available(self) -> List[Model]:
        models = await self.alist()
        return [m for m in models if m.is_available]
    
    def get_by_category(self, category: str) -> List[Model]:
        models = self.list()
        return [m for m in models if category in m.category]
    
    async def aget_by_category(self, category: str) -> List[Model]:
        models = await self.alist()
        return [m for m in models if category in m.category]
    
    def find(self, query: str) -> Optional[Model]:
        models = self.list()
        query_lower = query.lower()
        for model in models:
            if model.id.lower() == query_lower:
                return model
            if query_lower in [alias.lower() for alias in model.aliases]:
                return model
            if query_lower in model.name.lower():
                return model
        return None
    
    async def afind(self, query: str) -> Optional[Model]:
        models = await self.alist()
        query_lower = query.lower()
        for model in models:
            if model.id.lower() == query_lower:
                return model
            if query_lower in [alias.lower() for alias in model.aliases]:
                return model
            if query_lower in model.name.lower():
                return model
        return None
