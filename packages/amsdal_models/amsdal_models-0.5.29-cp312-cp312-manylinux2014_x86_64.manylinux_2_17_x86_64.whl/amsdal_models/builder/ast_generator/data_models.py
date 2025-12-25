import ast
from functools import cached_property
from typing import Any
from typing import Union

from pydantic import BaseModel
from pydantic import Field


class PropertyAst(BaseModel):
    """
    Represents a property in the AST.

    Attributes:
        name (str): The name of the property.
        types (list[Union[NestedPropertyTypeAst, PropertyValueAst]]): The types of the property.
        value (Optional[PropertyValueAst]): The value of the property.
    """

    name: str
    types: list[Union['NestedPropertyTypeAst', 'PropertyValueAst']]
    value: Union['PropertyValueAst', 'PropertyListValueAst'] | None = None

    @property
    def ast(self) -> Any:
        """
        Generates the AST node for the property.

        Returns:
            Any: The AST node representing the property.
        """
        return ast.AnnAssign(
            target=ast.Name(id=self.name, ctx=ast.Store()),
            annotation=join_property_values(self.types),
            value=self.value.ast if self.value else None,
            simple=1,
        )


class PropertyValueAst(BaseModel):
    """
    Represents a property value in the AST.

    Attributes:
        attr (Optional[tuple[str, str]]): The attribute of the property value.
        name (Optional[str]): The name of the property value.
        constant (Optional[Any]): The constant value of the property value.
    """

    attr: tuple[str, str] | None = None
    name: str | None = None
    constant: Any | None = None

    @property
    def ast(self) -> Any:
        """
        Generates the AST node for the property.

        Returns:
            Any: The AST node representing the property.
        """
        if self.attr:
            return ast.Attribute(
                value=ast.Name(id=self.attr[0], ctx=ast.Load()),
                attr=self.attr[1],
                ctx=ast.Load(),
            )
        elif self.name is not None:
            return ast.Name(id=self.name, ctx=ast.Load())
        elif self.constant is not None:
            return ast.Constant(value=self.constant, kind=None)
        else:
            msg = 'Invalid property value'
            raise ValueError(msg)


class CallAst(BaseModel):  # type: ignore[no-redef]
    func_name: str
    args: list[PropertyValueAst] = Field(default_factory=list)
    kwargs: dict[str, Union[PropertyValueAst, 'NestedPropertyTypeAst']] = Field(default_factory=dict)

    @property
    def ast(self) -> ast.Call:
        return ast.Call(
            func=ast.Name(id=self.func_name, ctx=ast.Load()),
            args=[arg.ast for arg in self.args],
            keywords=[
                ast.keyword(
                    arg=name,
                    value=value.ast,
                )
                for name, value in self.kwargs.items()
            ],
        )


class PropertyListValueAst(BaseModel):
    elements: list[CallAst | PropertyValueAst]

    @property
    def ast(self) -> Any:
        return ast.List(
            elts=[element.ast for element in self.elements],
            ctx=ast.Load(),
        )


class NestedPropertyTypeAst(BaseModel):
    """
    Represents a nested property type in the AST.

    Attributes:
        root (PropertyValueAst): The root property value.
        child (list[PropertyValueAst]): The child property values.
    """

    root: 'PropertyValueAst'
    child: list[Union['PropertyValueAst', 'NestedPropertyTypeAst']]

    @property
    def ast(self) -> Any:
        """
        Generates the AST node for the property.

        Returns:
            Any: The AST node representing the property.
        """
        return ast.Subscript(
            value=self.root.ast,
            slice=join_property_values(self.child),
            ctx=ast.Load(),
        )


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
        return ast.parse(self.custom_code.strip())

    @property
    def ast(self) -> list[Any]:
        """
        Extracts the AST nodes from the custom code, excluding imports.

        Returns:
            list[Any]: The list of AST nodes representing the custom code.
        """
        return [node for node in self.ast_module.body if not isinstance(node, (ast.Import, ast.ImportFrom))]

    @property
    def ast_imports(self) -> list[Any]:
        """
        Extracts the import AST nodes from the custom code.

        Returns:
            list[Any]: The list of import AST nodes.
        """
        return [node for node in self.ast_module.body if isinstance(node, (ast.Import, ast.ImportFrom))]


def join_property_values(
    items: list[Union['NestedPropertyTypeAst', 'PropertyValueAst']] | list['PropertyValueAst'],
) -> Any:
    """
    Joins property values into a single AST node.

    Args:
        items (list[Union[NestedPropertyTypeAst, PropertyValueAst]] | list[PropertyValueAst]): The list of property
            values to join.

    Returns:
        Any: The AST node representing the joined property values.
    """
    if len(items) == 1:
        return items[0].ast
    else:
        return ast.BinOp(
            left=join_property_values(items[:-1]),
            op=ast.BitOr(),
            right=items[-1].ast,
        )


class DependencyItem(BaseModel):
    module: tuple[str | None, str, str | None]

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, DependencyItem):
            return self.module == other.module
        return False

    def __hash__(self) -> int:
        return hash(self.module)


PropertyAst.model_rebuild()
NestedPropertyTypeAst.model_rebuild()
