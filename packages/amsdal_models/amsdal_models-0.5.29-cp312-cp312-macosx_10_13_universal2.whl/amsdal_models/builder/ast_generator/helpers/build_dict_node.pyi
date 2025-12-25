import ast
from typing import Any

def build_dict_node(dictionary: dict[str, Any] | list[dict[str, Any]] | str | int | float | bool | None) -> ast.Dict | ast.List | ast.Constant: ...
