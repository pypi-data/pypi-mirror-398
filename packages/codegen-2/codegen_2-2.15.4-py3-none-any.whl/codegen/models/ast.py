from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional, Sequence

from codegen.models.expr import ExceptionExpr, Expr
from codegen.models.statement import (
    AssignStatement,
    BlockStatement,
    CatchStatement,
    Comment,
    DefClassLikeStatement,
    DefClassStatement,
    DefClassVarStatement,
    DefFuncStatement,
    ElseStatement,
    ExceptionStatement,
    ForLoopStatement,
    IfStatement,
    ImportStatement,
    LineBreak,
    NoStatement,
    PythonStatement,
    ReturnStatement,
    SingleExprStatement,
    Statement,
    TryStatement,
)
from codegen.models.types import AST_ID
from codegen.models.var import DeferredVar, Var, VarScope

if TYPE_CHECKING:
    from codegen.models.program import Program


@dataclass
class AST:
    id: AST_ID
    prog: Program
    stmt: Statement
    children: list[AST] = field(default_factory=list)
    _is_frozen: bool = (
        False  # whether to freeze the AST and disallow further modification
    )

    @staticmethod
    def root(prog: Program):
        return AST(tuple(), prog, BlockStatement(has_owned_env=False))

    def is_root(self) -> bool:
        """Check if this is the root AST"""
        return len(self.id) == 0

    def __call__(
        self,
        *args: Callable[[AST], Any] | Optional[Statement],
        return_self: bool = False,
    ) -> Optional[AST]:
        """Allow to build the graph hierarchically"""
        assert isinstance(return_self, bool)

        return_val = None

        for fn in args:
            if isinstance(fn, Statement):
                self._add_stmt(fn)
            elif callable(fn):
                return_val = fn(self)
            else:
                assert fn is None

        if return_self:
            assert return_val is None, "Trying to return multiple asts at the same time"
            return self
        return return_val

    def freeze(self):
        self._is_frozen = True
        for child in self.children:
            child.freeze()

    def import_(self, module: str, is_import_attr: bool, alias: Optional[str] = None):
        self._add_stmt(ImportStatement(module, is_import_attr, alias))

    def return_(self, expr: Expr):
        self._add_stmt(ReturnStatement(expr))

    def linebreak(self):
        self._add_stmt(LineBreak())

    def block(self):
        return self._add_stmt(BlockStatement())

    def comment(self, comment: str):
        self._add_stmt(Comment(comment))

    def func(
        self,
        name: str,
        vars: Sequence[DeferredVar | tuple[DeferredVar, Expr]],
        return_type: Optional[Expr] = None,
        is_async: bool = False,
        is_static: bool = False,
        modifiers: Optional[Sequence[Literal["get", "set"]]] = None,
        comment: str = "",
    ):
        """Define a function. The input variables are deferred vars as they are created for this function (i.e., must not be predefined prior to this function)"""
        grandchild_id = self.next_grandchild_id()
        for vararg in vars:
            if isinstance(vararg, tuple):
                var = vararg[0]
            else:
                var = vararg
            var.set_var(
                self.prog.create_var(
                    var.name, var.key, grandchild_id, var.force_name, var.type
                )
            )

        return self._add_stmt(
            DefFuncStatement(
                name,
                [
                    (
                        (var[0].get_var(), var[1])
                        if isinstance(var, tuple)
                        else var.get_var()
                    )
                    for var in vars
                ],
                return_type,
                is_async,
                is_static,
                modifiers or [],
                comment,
            )
        )

    def class_(self, name: str, parents: Optional[Sequence[Expr]] = None):
        """Define a class."""
        return self._add_stmt(DefClassStatement(name, parents or []))

    def class_like(
        self,
        keyword: Literal["interface", "enum"],
        name: str,
        parents: Optional[Sequence[Expr]] = None,
    ):
        """Define a class-like structure such as enum or interface in Typescript."""
        return self._add_stmt(DefClassLikeStatement(keyword, name, parents or []))

    def expr(self, expr: Expr):
        return self._add_stmt(SingleExprStatement(expr))

    def raise_exception(self, expr: ExceptionExpr):
        return self._add_stmt(ExceptionStatement(expr))

    def assign(self, var: DeferredVar | Var, expr: Expr):
        """When we assign the variable, we accept that either you create/declare the variable for the first time or reassign it"""
        if isinstance(var, DeferredVar):
            # create the variable for the first time
            real_var = self.prog.create_var(
                var.name, var.key, self.next_child_id(), var.force_name
            )
            var.set_var(real_var)
            var = real_var
        else:
            # the variable is already created -- and we are just reassigning it
            # we have to make sure that it's accessible from the current scope
            assert self.prog.is_within_scope(self.next_child_id(), var.scope)

        self._add_stmt(AssignStatement(var, expr))

    def for_loop(self, item: DeferredVar, iter: Expr):
        """When we construct a for-loop, the item (or var) is always declared. We don't allow reassigning the variable in the for-loop."""
        assert (
            isinstance(item, DeferredVar) and item.has_not_been_created()
        ), "The item must be a new variable"
        var = self.prog.create_var(
            item.name, item.key, self.next_grandchild_id(), item.force_name
        )
        item.set_var(var)

        return self._add_stmt(ForLoopStatement(var, iter))

    def if_(self, condition: Expr):
        return self._add_stmt(IfStatement(condition))

    def else_(self):
        assert len(self.children) > 0 and isinstance(
            self.children[-1].stmt, (IfStatement, CatchStatement)
        )
        return self._add_stmt(ElseStatement())

    def try_(self):
        """Start a try block. The next statement must be an exception statement."""
        return self._add_stmt(TryStatement())

    def catch(self, match: Optional[Expr] = None):
        return self._add_stmt(
            CatchStatement(
                match,
            )
        )

    def python_stmt(self, stmt: str) -> AST:
        return self._add_stmt(PythonStatement(stmt))

    def update_recursively(
        self, fn: Callable[[AST, Any], tuple[AST, Any, bool]], context: Any
    ):
        """Recursively updating the ast. It takes a function that works on the current tree and a context, returns a tuple of
        (new_tree, new_context, stop). This function returns the last AST that is updated.
        """
        ast = self
        stop = False
        while not stop:
            ast, context, stop = fn(ast, context)
        return ast

    def has_statement_between_ast(self, stmtcls: type[Statement], end_ast_id: AST_ID):
        """Check if there is a statement of the given type the current AST and the end_ast (exclusive)"""
        for ast in self.children:
            for intermediate_ast in ast.find_ast_to(end_ast_id):
                if (
                    isinstance(intermediate_ast.stmt, stmtcls)
                    and intermediate_ast.id != end_ast_id
                ):
                    return True
        return False

    def find_ast_to(self, id: AST_ID):
        """Iterate through ASTs that lead to the AST with the given id (inclusive)"""
        if self.id == id:
            yield self
        else:
            for ast in self.children:
                if ast.find_ast(id) is not None:
                    yield self
                    yield from ast.find_ast_to(id)
                    break

    def find_ast(self, id: AST_ID) -> Optional[AST]:
        """Find the AST with the given id"""
        if len(self.id) > len(id):
            # the ast that we are looking for is not in the subtree of this ast
            return None

        for i in range(len(self.id)):
            if self.id[i] != id[i]:
                # the ast that we are looking for is not in the subtree of this ast
                return None

        if len(self.id) == len(id):
            return self

        ast = self
        for i in range(len(self.id), len(id)):
            ast = ast.children[id[i]]
        return ast

    def next_child_id(self) -> AST_ID:
        """Get ID for the next child of this AST"""
        return self.id + (len(self.children),)

    def next_grandchild_id(self) -> AST_ID:
        """Get ID for the next grandchild of this AST"""
        return self.id + (len(self.children), 0)

    def next_var_scope(self) -> VarScope:
        """Get a scope for the next variable that will be have if it is assigned to this AST"""
        return VarScope(self.id, len(self.children))

    def _add_stmt(self, stmt: Statement):
        if self._is_frozen:
            raise Exception("The AST is frozen and cannot be modified")
        ast = AST(self.next_child_id(), self.prog, stmt)
        self.children.append(ast)
        return ast

    def to_python(self, level: int = 0):
        """Convert the AST to python code"""
        if isinstance(self.stmt, BlockStatement):
            # there is no direct statement and the level does not increase after this statement
            return "\n".join([child.to_python(level) for child in self.children])

        prog = ["\t" * level + line for line in self.stmt.to_python().split("\n")]
        prog.extend((child.to_python(level + 1) for child in self.children))
        return "\n".join(prog)

    def to_typescript(self, level: int = 0):
        """Convert the AST to typescript code"""
        if isinstance(self.stmt, BlockStatement):
            if not self.stmt.has_owned_env:
                # the level does not increase after this statement because we do not need to create a new scope
                content = "\n".join(
                    [child.to_typescript(level) for child in self.children]
                )
                if self.is_root():
                    return content.lstrip("\n")
                return content

            if len(self.children) == 0:
                return ""

            return (
                ("\t" * level + "{")
                + "\n".join([child.to_typescript(level + 1) for child in self.children])
                + "\n"
                + ("\t" * level + "}")
            )

        prog = ["\t" * level + line for line in self.stmt.to_typescript().split("\n")]
        if len(self.children) > 0:
            prog.append("\t" * level + "{")
            prog.extend((child.to_typescript(level + 1) for child in self.children))
            prog.append("\t" * level + "}")
        return "\n".join(prog)
