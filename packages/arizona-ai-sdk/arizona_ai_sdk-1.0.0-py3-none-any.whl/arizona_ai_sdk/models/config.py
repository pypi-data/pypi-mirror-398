from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from arizona_ai_sdk.models.base import BaseModel


@dataclass
class Config(BaseModel):
    id: str = ""
    name: str = ""
    description: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Config":
        if data is None:
            data = {}
        return cls(
            id=str(data.get("id", "")),
            name=data.get("name", ""),
            description=data.get("description")
        )


@dataclass
class ConfigsResponse(BaseModel):
    status: str = "success"
    configs: List[Config] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ConfigsResponse":
        if data is None:
            data = {}
        configs_data = data.get("data", [])
        configs = [Config.from_dict(c) for c in configs_data]
        return cls(
            status=data.get("status", "success"),
            configs=configs
        )
    
    def __iter__(self):
        return iter(self.configs)
    
    def __len__(self):
        return len(self.configs)
    
    def get_by_id(self, config_id: str) -> Optional[Config]:
        for config in self.configs:
            if config.id == config_id:
                return config
        return None
    
    def get_by_name(self, name: str) -> Optional[Config]:
        for config in self.configs:
            if config.name.lower() == name.lower():
                return config
        return None
