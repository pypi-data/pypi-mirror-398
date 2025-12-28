from typing import Any, Dict, Optional

from mat3ra.code.entity import InMemoryEntityPydantic
from mat3ra.esse.models.model import BaseModel1
from pydantic import Field

from .method import Method
from .methods.factory import MethodFactory


class Model(BaseModel1, InMemoryEntityPydantic):
    method: Method = Field(default_factory=lambda: MethodFactory.create({}))

    application: Optional[Dict[str, Any]] = Field(default=None, exclude=True)


    def __convert_kwargs__(self, **kwargs: Any) -> Dict[str, Any]:
        if isinstance(kwargs.get("method"), dict):
            kwargs["method"] =  MethodFactory.create(kwargs.get("method", Method().to_dict()))
        if isinstance(kwargs.get("subtype"), dict):
            kwargs["subtype"] =  str(kwargs["subtype"].get("slug", ""))
        return kwargs

    def __init__(self, *args: Any, **kwargs: Any):
        kwargs = self.__convert_kwargs__(**kwargs)
        super().__init__(*args, **kwargs)


    @property
    def group_slug(self) -> str:
        if not self.application:
            return f"{self.type}:{self.subtype}"
        short_name = self.application.get("shortName", "")
        return f"{short_name}:{self.type}:{self.subtype}"

    @property
    def is_unknown(self) -> bool:
        return self.type == "unknown"
