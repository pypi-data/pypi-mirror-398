from dataclasses import dataclass, field, asdict, fields
from typing import TypeVar, Type, Dict, Any, Optional, get_type_hints, get_origin, get_args, List
import json

T = TypeVar("T", bound="BaseModel")


@dataclass
class BaseModel:
    @classmethod
    def from_dict(cls: Type[T], data: Optional[Dict[str, Any]]) -> T:
        if data is None:
            data = {}
        
        type_hints = get_type_hints(cls)
        field_names = {f.name for f in fields(cls)}
        kwargs = {}
        
        for field_name in field_names:
            if field_name in data:
                value = data[field_name]
                expected_type = type_hints.get(field_name)
                
                if value is not None and expected_type:
                    origin = get_origin(expected_type)
                    args = get_args(expected_type)
                    
                    if origin is list and args:
                        inner_type = args[0]
                        if isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
                            value = [inner_type.from_dict(item) if isinstance(item, dict) else item for item in value]
                    elif isinstance(expected_type, type) and issubclass(expected_type, BaseModel):
                        if isinstance(value, dict):
                            value = expected_type.from_dict(value)
                
                kwargs[field_name] = value
        
        return cls(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if value is not None:
                if isinstance(value, BaseModel):
                    result[f.name] = value.to_dict()
                elif isinstance(value, list):
                    result[f.name] = [
                        item.to_dict() if isinstance(item, BaseModel) else item
                        for item in value
                    ]
                else:
                    result[f.name] = value
        return result

    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def __repr__(self) -> str:
        field_strs = []
        for f in fields(self):
            value = getattr(self, f.name)
            if value is not None:
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                field_strs.append(f"{f.name}={value!r}")
        return f"{self.__class__.__name__}({', '.join(field_strs)})"
