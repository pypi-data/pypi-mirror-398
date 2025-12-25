from enum import Enum
from typing import Any

class ReferenceMode(str, Enum):
    CASCADE = 'CASCADE'
    PROTECT = 'PROTECT'
    RESTRICT = 'RESTRICT'
    SET_NULL = 'SET_NULL'
    SET_DEFAULT = 'SET_DEFAULT'
    DO_NOTHING = 'DO_NOTHING'
    @staticmethod
    def SET(value: Any) -> None: ...
