from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from arizona_ai_sdk.models.base import BaseModel


@dataclass
class ModelCapabilities(BaseModel):
    text: bool = True
    images: bool = False
    audio: bool = False
    streaming: bool = True
    thinking: bool = False
    tools: bool = False


@dataclass
class Model(BaseModel):
    id: str = ""
    aliases: List[str] = field(default_factory=list)
    name: str = ""
    short_name: Optional[str] = None
    description: Optional[str] = None
    category: List[str] = field(default_factory=list)
    capabilities: Optional[ModelCapabilities] = None
    max_request_tokens: Optional[int] = None
    max_chat_tokens: Optional[int] = None
    overloaded: bool = False
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Model":
        if data is None:
            data = {}
        capabilities_data = data.get("capabilities")
        capabilities = ModelCapabilities.from_dict(capabilities_data) if capabilities_data else None
        return cls(
            id=data.get("id", ""),
            aliases=data.get("aliases", []),
            name=data.get("name", ""),
            short_name=data.get("short_name"),
            description=data.get("description"),
            category=data.get("category", []),
            capabilities=capabilities,
            max_request_tokens=data.get("max_request_tokens"),
            max_chat_tokens=data.get("max_chat_tokens"),
            overloaded=data.get("overloaded", False)
        )
    
    @property
    def supports_images(self) -> bool:
        return self.capabilities.images if self.capabilities else False
    
    @property
    def supports_streaming(self) -> bool:
        return self.capabilities.streaming if self.capabilities else True
    
    @property
    def supports_thinking(self) -> bool:
        return self.capabilities.thinking if self.capabilities else False
    
    @property
    def is_available(self) -> bool:
        return not self.overloaded


@dataclass
class ModelsResponse(BaseModel):
    status: str = "success"
    models: List[Model] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ModelsResponse":
        if data is None:
            data = {}
        models_data = data.get("data", [])
        models = [Model.from_dict(m) for m in models_data]
        return cls(
            status=data.get("status", "success"),
            models=models
        )
    
    def __iter__(self):
        return iter(self.models)
    
    def __len__(self):
        return len(self.models)
    
    def get_by_id(self, model_id: str) -> Optional[Model]:
        for model in self.models:
            if model.id == model_id or model_id in model.aliases:
                return model
        return None
    
    def filter_by_category(self, category: str) -> List[Model]:
        return [m for m in self.models if category in m.category]
    
    def get_available(self) -> List[Model]:
        return [m for m in self.models if m.is_available]
