import ast
from typing import Any


def build_dict_node(
    dictionary: dict[str, Any] | list[dict[str, Any]] | str | int | float | bool | None,
) -> ast.Dict | ast.List | ast.Constant:
    if isinstance(dictionary, dict):
        """
        Builds an AST node for a dictionary.

        Args:
            dictionary (dict[str, Any] | list[dict[str, Any]] | str | int | float | bool | None):
            The dictionary to convert.

        Returns:
            ast.Dict | ast.List | ast.Constant: The AST node representing the dictionary.

        Raises:
            ValueError: If the dictionary type is unsupported.
        """
        # Create an empty Dict AST node
        dict_ast = ast.Dict(keys=[], values=[])

        for key, value in dictionary.items():
            # Convert the key to a string AST node
            key_ast = ast.Constant(s=str(key))  # type: ignore[call-arg]

            # Convert the value recursively
            value_ast = build_dict_node(value)

            # Append the key-value pair to the Dict AST node
            dict_ast.keys.append(key_ast)
            dict_ast.values.append(value_ast)

        return dict_ast

    elif isinstance(dictionary, list):
        # Create an empty List AST node
        list_ast = ast.List(elts=[])

        for value in dictionary:
            # Convert the value recursively
            value_ast = build_dict_node(value)

            # Append the value to the List AST node
            list_ast.elts.append(value_ast)

        return list_ast
    elif isinstance(dictionary, str):
        return ast.Constant(value=dictionary)
    elif isinstance(dictionary, int | float):
        return ast.Constant(value=dictionary)
    elif isinstance(dictionary, bool):
        return ast.Constant(value=dictionary)
    elif dictionary is None:
        return ast.Constant(value=None)

    msg = f'Unsupported type: {type(dictionary)}'

    raise ValueError(msg)
