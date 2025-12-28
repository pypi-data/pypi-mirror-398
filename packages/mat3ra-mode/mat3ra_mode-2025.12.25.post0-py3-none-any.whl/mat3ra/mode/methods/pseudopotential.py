from typing import Any, Dict, List, Optional

from mat3ra.esse.models.methods_directory.legacy.pseudopotential import LegacyMethodPseudopotential

from ..method import Method


class PseudopotentialMethod(LegacyMethodPseudopotential, Method):
    pseudopotential_cls: Optional[type] = None

    @property
    def pseudo(self) -> List[Dict[str, Any]]:
        return self.data.get("pseudo", [])

    @property
    def all_pseudo(self) -> List[Dict[str, Any]]:
        return self.data.get("allPseudo", [])

    @property
    def pseudopotentials(self) -> List[Any]:
        if not self.pseudopotential_cls:
            return []
        return [self.pseudopotential_cls(config) for config in self.pseudo]

    @property
    def all_pseudopotentials(self) -> List[Any]:
        if not self.pseudopotential_cls:
            return []
        return [self.pseudopotential_cls(config) for config in self.all_pseudo]

    def to_dict(self, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        json_data = super().to_dict(exclude=exclude)

        if exclude is None or "data" not in exclude:
            filtered_data = self.data.copy()
            filtered_data.pop("allPseudo", None)
            json_data["data"] = filtered_data

        return json_data
