import ast
from functools import cached_property as cached_property
from pydantic import BaseModel
from typing import Any

class PropertyAst(BaseModel):
    """
    Represents a property in the AST.

    Attributes:
        name (str): The name of the property.
        types (list[Union[NestedPropertyTypeAst, PropertyValueAst]]): The types of the property.
        value (Optional[PropertyValueAst]): The value of the property.
    """
    name: str
    types: list[NestedPropertyTypeAst | PropertyValueAst]
    value: PropertyValueAst | PropertyListValueAst | None
    @property
    def ast(self) -> Any:
        """
        Generates the AST node for the property.

        Returns:
            Any: The AST node representing the property.
        """

class PropertyValueAst(BaseModel):
    """
    Represents a property value in the AST.

    Attributes:
        attr (Optional[tuple[str, str]]): The attribute of the property value.
        name (Optional[str]): The name of the property value.
        constant (Optional[Any]): The constant value of the property value.
    """
    attr: tuple[str, str] | None
    name: str | None
    constant: Any | None
    @property
    def ast(self) -> Any:
        """
        Generates the AST node for the property.

        Returns:
            Any: The AST node representing the property.
        """

class CallAst(BaseModel):
    func_name: str
    args: list[PropertyValueAst]
    kwargs: dict[str, PropertyValueAst | NestedPropertyTypeAst]
    @property
    def ast(self) -> ast.Call: ...

class PropertyListValueAst(BaseModel):
    elements: list[CallAst | PropertyValueAst]
    @property
    def ast(self) -> Any: ...

class NestedPropertyTypeAst(BaseModel):
    """
    Represents a nested property type in the AST.

    Attributes:
        root (PropertyValueAst): The root property value.
        child (list[PropertyValueAst]): The child property values.
    """
    root: PropertyValueAst
    child: list[PropertyValueAst | NestedPropertyTypeAst]
    @property
    def ast(self) -> Any:
        """
        Generates the AST node for the property.

        Returns:
            Any: The AST node representing the property.
        """

class CustomCodeAst(BaseModel):
    """
    Represents custom code in the AST.

    Attributes:
        custom_code (str): The custom code to be parsed into AST.
    """
    custom_code: str
    @cached_property
    def ast_module(self) -> Any:
        """
        Parses the custom code into an AST module.

        Returns:
            Any: The AST module representing the custom code.
        """
    @property
    def ast(self) -> list[Any]:
        """
        Extracts the AST nodes from the custom code, excluding imports.

        Returns:
            list[Any]: The list of AST nodes representing the custom code.
        """
    @property
    def ast_imports(self) -> list[Any]:
        """
        Extracts the import AST nodes from the custom code.

        Returns:
            list[Any]: The list of import AST nodes.
        """

def join_property_values(items: list[NestedPropertyTypeAst | PropertyValueAst] | list['PropertyValueAst']) -> Any:
    """
    Joins property values into a single AST node.

    Args:
        items (list[Union[NestedPropertyTypeAst, PropertyValueAst]] | list[PropertyValueAst]): The list of property
            values to join.

    Returns:
        Any: The AST node representing the joined property values.
    """

class DependencyItem(BaseModel):
    module: tuple[str | None, str, str | None]
    def __eq__(self, other: Any) -> bool: ...
    def __hash__(self) -> int: ...
