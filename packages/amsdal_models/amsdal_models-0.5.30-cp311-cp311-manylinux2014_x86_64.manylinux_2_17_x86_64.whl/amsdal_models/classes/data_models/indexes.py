from dataclasses import dataclass


@dataclass(kw_only=True)
class IndexInfo:
    name: str
    field: str
