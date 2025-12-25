from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Union

from ..util.functions import strtobool
from ..util.property import Property

if TYPE_CHECKING:
    from ..engine import MimaEngine


class Template:
    engine: MimaEngine

    def __init__(self, name: str):
        self.name: str = name
        self.properties: Dict[str, Property] = {}

    def get_string(self, key: str, default_val: str = "") -> str:
        if key in self.properties:
            return self.properties[key].value
        else:
            return default_val

    def get_int(self, key: str, default_val: int = 0) -> int:
        if key in self.properties:
            return int(self.properties[key].value)
        else:
            return default_val

    def get_float(self, key: str, default_val: float = 0.0) -> float:
        if key in self.properties:
            return float(self.properties[key].value)
        else:
            return default_val

    def get_bool(self, key: str, default_val: bool = False) -> bool:
        if key in self.properties:
            return bool(strtobool(self.properties[key].value))
        else:
            return default_val

    def get(
        self, key: str, default_val: Optional[str, int, float, bool] = None
    ) -> Union[str, int, float, bool]:

        if key in self.properties:
            if self.properties[key].dtype == "str":
                if default_val is None:
                    return self.get_string(key)
                return self.get_string(key, default_val)
            if self.properties[key].dtype == "int":
                if default_val is None:
                    return self.get_int(key)
                return self.get_int(key, int(default_val))
            if self.properties[key].dtype == "float":
                if default_val is None:
                    return self.get_float(key)
                return self.get_float(key, float(default_val))
            if self.properties[key].dtype == "bool":
                if default_val is None:
                    return self.get_bool(key)
                elif not isinstance(default_val, bool):
                    msg = (
                        "Trying to access a bool value but default value "
                        f"{default_val} is of type {type(default_val)}"
                    )
                    raise TypeError(msg)
                return self.get_bool(key, default_val)

        return default_val
