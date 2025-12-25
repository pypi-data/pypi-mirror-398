from dataclasses import dataclass


@dataclass(kw_only=True)
class UniqueConstraint:
    name: str
    fields: list[str]
