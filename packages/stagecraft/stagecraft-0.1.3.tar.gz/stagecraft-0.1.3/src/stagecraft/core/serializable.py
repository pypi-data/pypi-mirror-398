from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

import pandas as pd
from pydantic import BaseModel, ConfigDict

from .str import snake_to_camel_case

if TYPE_CHECKING:
    pass

SERIALIZABLE = TypeVar("SERIALIZABLE", bound="Serializable")


class Serializable(BaseModel):
    model_config = ConfigDict(
        alias_generator=snake_to_camel_case,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={pd.DataFrame: lambda df: df.to_dict("records")},
        ser_json_timedelta="iso8601",
        ser_json_bytes="base64",
    )

    def to_dict(self, *, convert_keys: bool = False) -> Dict[str, Any]:
        """
        Serialize object to Python dictionary.

        Args:
            convert_keys: Convert keys to camelCase (JSON standard)
        """
        if convert_keys:
            return self.model_dump(by_alias=True)
        return self.model_dump()

    @classmethod
    def from_dict(cls: Type[SERIALIZABLE], _dict: Dict[str, Any]) -> SERIALIZABLE:
        """
        Deserialize object from Python dictionary.

        Args:
            _dict: Dictionary to deserialize from
        """
        return cls.model_validate(_dict)
