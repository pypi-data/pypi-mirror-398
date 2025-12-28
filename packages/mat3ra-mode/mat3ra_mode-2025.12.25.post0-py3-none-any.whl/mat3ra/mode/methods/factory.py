from typing import Any, Dict

from ..method import Method
from .pseudopotential import PseudopotentialMethod


class MethodFactory:
    Method = Method
    PseudopotentialMethod = PseudopotentialMethod

    @classmethod
    def create(cls, config: Dict[str, Any]) -> Method:
        method_type = config.get("type", "")

        if method_type == "pseudopotential":
            return cls.PseudopotentialMethod.create(config)

        return cls.Method.create(config)
