from typing import Any, Dict, List, Optional

from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.method import BaseMethod
from pydantic import Field



class Method(BaseMethod, InMemoryEntityPydantic):
    type: str = Field(default="unknown")
    subtype: str = Field(default="unknown")
    data: Dict[str, Any] = Field(default_factory=dict)

    def clone_without_data(self) -> "Method":
        cloned = self.clone()
        cloned.data = {}
        return cloned


    @classmethod
    def clean(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        data = config.get("data", {})
        cleaned = super().clean(config)
        cleaned["data"] = data
        return cleaned

    @property
    def search_text(self) -> str:
        return self.data.get("searchText", "")

    @property
    def omit_in_hash_calculation(self) -> bool:
        data = self.data
        if not data:
            return True
        # Omit if only searchText is present and empty, or no fields at all
        search_text = data.get("searchText", "")
        other_fields = {k: v for k, v in data.items() if k != "searchText"}
        return not search_text and not other_fields

    def to_dict(self, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        exclude_set = set(exclude) if exclude else set()
        should_exclude_data = "data" in exclude_set
        exclude_set = {x for x in exclude_set if x != "data"}

        dict_data = super().to_dict(exclude=list(exclude_set) if exclude_set else None)

        if not should_exclude_data:
            dict_data["data"] = self.data.copy()

        return dict_data
