from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple, Optional

from codegen.models.types import AST_ID, KEY, NO_KEY

if TYPE_CHECKING:
    from codegen.models.expr import ExprIdent


class VarScope(NamedTuple):
    ast: AST_ID  # the ast that has a child, which is an assign statement, that the first time the variable is defined
    child_index_start: int  # the index of the child (assign statement)
    child_index_end: Optional[int] = (
        None  # the index of the child that the variable is deleted (exclusive)
    )

    @staticmethod
    def from_ast_id(ast_id: AST_ID) -> VarScope:
        """Get the scope of a variable as if it is assigned to the given AST"""
        return VarScope(ast_id[:-1], ast_id[-1], None)

    def get_depth(self) -> int:
        return len(self.ast) + 1


@dataclass
class Var:  # variable
    """To create the variable for the first time, use DeferredVar."""

    name: str
    key: KEY
    register_id: int
    scope: VarScope
    force_name: Optional[str] = None
    # type of the variable
    type: Optional[ExprIdent] = None

    def get_name(self) -> str:
        if self.force_name is None:
            return f"{self.name}_{self.register_id}"
        return self.force_name

    def to_python(self):
        """Get the python code to create the variable"""
        if self.type is None:
            return f"{self.get_name()}"
        return f"{self.get_name()}: {self.type.to_python()}"

    def to_typescript(self):
        """Get the typescript code to create the variable"""
        if self.type is None:
            return f"{self.get_name()}"
        return f"{self.get_name()}: {self.type.to_typescript()}"


@dataclass
class DeferredVar:
    """Containings the information to create a variable. This is the class to use to create variable."""

    name: str
    key: KEY = NO_KEY
    force_name: Optional[str] = None
    type: Optional[ExprIdent] = None

    # the variable that we want to create --- this will be not None when the variable is actually created
    _var: Optional[Var] = None

    @staticmethod
    def simple(name: str, type: Optional[ExprIdent] = None) -> DeferredVar:
        """Create a DeferredVar with the given name and type"""
        return DeferredVar(name, (name,), name, type)

    def get_var(self) -> Var:
        if self._var is None:
            raise ValueError("The variable has not been created yet")
        return self._var

    def set_var(self, var: Var):
        if self._var is not None:
            raise ValueError("The variable has been created already")
        self._var = var

    def has_not_been_created(self) -> bool:
        return self._var is None
