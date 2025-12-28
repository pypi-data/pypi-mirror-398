from typing import Any, Dict, List, Union

from mat3ra.esse.models.core.primitive.slugified_entry import SlugifiedEntry
from mat3ra.esse.models.models_directory.legacy.dft import Functional1
from pydantic import Field

from ..model import Model


class DFTModel(Model):
    type: str = Field(default="dft")
    subtype: str = Field(default="gga")
    functional: Union[Functional1, SlugifiedEntry, Dict[str, Any], None] = Field(
        default=Functional1.pbe
    )
    refiners: List[Union[SlugifiedEntry, str]] = Field(default_factory=list)
    modifiers: List[Union[SlugifiedEntry, str]] = Field(default_factory=list)

    def __convert_kwargs__(self, **kwargs: Any) -> Dict[str, Any]:
        if isinstance(kwargs.get("functional"), str):
            kwargs["functional"] = {"slug": kwargs["functional"]}
        return super().__convert_kwargs__(**kwargs)
