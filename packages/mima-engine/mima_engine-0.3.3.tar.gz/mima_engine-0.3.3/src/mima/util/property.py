from dataclasses import dataclass


@dataclass
class Property:
    name: str
    dtype: str
    value: str
