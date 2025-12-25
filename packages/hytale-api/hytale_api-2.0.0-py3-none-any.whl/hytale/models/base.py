from typing import Any, Dict, Type, TypeVar

import attrs

T = TypeVar("T")


@attrs.define(slots=True)
class FromDictMixin:
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        if isinstance(data, cls):
            return data

        field_names = {field.name for field in attrs.fields(cls)}
        filtered = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered)
