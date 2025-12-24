from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Optional

from codegen.models.ast import AST
from codegen.models.expr import ExprIdent  # You may need to adjust this import path
from codegen.models.statement import BlockStatement, IfStatement
from codegen.models.types import AST_ID, KEY
from codegen.models.var import Var, VarScope


@dataclass(init=False)
class Program:
    root: AST
    vars: VarRegisters
    import_area: AST
    imported_modules: set[str]

    def __init__(self):
        self.vars = VarRegisters(self)
        self.root = AST.root(self)
        self.import_area = self.root._add_stmt(BlockStatement(has_owned_env=False))
        self.imported_modules = set()

    def import_(self, module: str, is_import_attr: bool, alias: Optional[str] = None):
        if module not in self.imported_modules:
            self.import_area.import_(module, is_import_attr, alias)
            self.imported_modules.add(module)

    def get_ast_by_id(self, id: AST_ID) -> AST:
        ast = self.root
        for item in id:
            ast = ast.children[item]
        return ast

    def is_within_scope(self, ast: AST_ID, scope: VarScope) -> bool:
        if len(ast) - 1 < len(scope.ast):
            return False

        for i in range(len(scope.ast)):
            if ast[i] != scope.ast[i]:
                return False

        if len(ast) - 1 == len(scope.ast):
            return ast[-1] >= scope.child_index_start and (
                scope.child_index_end is None or ast[-1] < scope.child_index_end
            )

        return ast[len(scope.ast)] >= scope.child_index_start and (
            scope.child_index_end is None or ast[len(scope.ast)] < scope.child_index_end
        )

    def create_var(
        self,
        name: str,
        key: KEY,
        ast: AST_ID,
        force_name: Optional[str] = None,
        type: Optional[ExprIdent] = None,
    ) -> Var:
        reg = self.vars.register(name, key, ast, force_name, type)
        return Var(
            name=name,
            key=key,
            register_id=reg.id,
            scope=reg.scope,
            force_name=force_name,
            type=type,
        )

    def get_var(
        self,
        *,
        key: KEY,
        at: AST_ID,
    ) -> Var:
        """De-reference a variable from the memory that is available at the provided AST"""
        reg = self.vars.find(key, at)
        if reg is None:
            raise KeyError(f"Variable with key {key} is not found in the current scope")
        return Var(
            name=reg.name, key=key, register_id=reg.id, scope=reg.scope, type=reg.type
        )


@dataclass
class VarRegister:
    id: int
    name: str
    key: KEY
    scope: VarScope
    force_name: Optional[str] = None
    type: Optional[ExprIdent] = None


@dataclass
class VarRegisters:
    program: Program
    registers: list[VarRegister] = field(default_factory=list)
    key2registers: dict[KEY, list[int]] = field(default_factory=dict)

    def register(
        self,
        name: str,
        key: KEY,
        ast: AST_ID,
        force_name: Optional[str] = None,
        type: Optional[ExprIdent] = None,
    ) -> VarRegister:
        """Register a new variable with the given name, key, then return the register id.

        The scope of the variable is created from the given ast.
        """
        reg = self.find(key, ast)
        if reg is not None:
            # we found an existing register -- we need to test if we can override the existing register, which
            # means if we go out of the new register scope, the value of the existing register is restored.

            # for now, we don't support overriding an existing register
            raise ValueError(
                f"Variable {name} with key {key} is already registered in the current scope"
            )

        reg = VarRegister(
            id=len(self.registers),
            name=name,
            key=key,
            scope=VarScope.from_ast_id(ast),
            force_name=force_name,
            type=type,
        )
        self.registers.append(reg)
        self.key2registers.setdefault(key, []).append(reg.id)
        return reg

    def find(self, key: KEY, ast: AST_ID) -> Optional[VarRegister]:
        """Find the most specific register by name, key that is available in the given ast. If
        there are multiple matches, the most specific register is the one with the largest depth.
        """
        if key not in self.key2registers:
            return None

        matched_regid = None
        matched_regid_depth = -1
        for regid in self.key2registers[key]:
            reg = self.registers[regid]
            if self.program.is_within_scope(ast, reg.scope):
                regscope_depth = reg.scope.get_depth()
                if regscope_depth > matched_regid_depth:
                    matched_regid = reg.id
                    matched_regid_depth = regscope_depth

        if matched_regid is None:
            return None
        return self.registers[matched_regid]


@dataclass
class ImportHelper:
    """Helper class to manage imports in the program."""

    program: Program
    # mapping from identifiers to their imported paths
    idents: dict[str, str] = field(default_factory=dict)

    def use(self, ident: str):
        assert ident in self.idents, ident
        self.program.import_(self.idents[ident], True)
        return ExprIdent(ident)

    def python_import_for_hint(
        self, module: str, is_import_attr: bool, alias: Optional[str] = None
    ):
        """A specific function only for Python to import identifiers that causing circular import error into a same TYPE_CHECKING condition"""
        if module in self.program.imported_modules:
            return
        self.program.imported_modules.add(module)

        self.program.import_("typing.TYPE_CHECKING", True)
        for child in self.program.import_area.children:
            if isinstance(child.stmt, IfStatement) and child.stmt.cond == ExprIdent(
                "TYPE_CHECKING"
            ):
                child.import_(module, is_import_attr, alias)
                break
        else:
            self.program.import_area.if_(ExprIdent("TYPE_CHECKING"))(
                lambda ast: ast.import_(module, is_import_attr, alias)
            )
