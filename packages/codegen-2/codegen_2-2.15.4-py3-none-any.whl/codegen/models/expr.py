from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence

from codegen.models.var import Var


class Expr(ABC):
    @abstractmethod
    def to_python(self):
        raise NotImplementedError(self.__class__)

    def to_typescript(self):
        raise NotImplementedError(self.__class__)

    def to_wrapped_python(self):
        if isinstance(self, (ExprVar, ExprConstant)):
            return self.to_python()
        return f"({self.to_python()})"


class ExceptionExpr(Expr): ...


@dataclass
class StandardExceptionExpr(ExceptionExpr):
    cls: Expr
    args: Sequence[Expr]

    def to_python(self):
        return f"{self.cls.to_python()}({', '.join([arg.to_python() for arg in self.args])})"


@dataclass
class ExprConstant(Expr):
    constant: Any

    def to_python(self):
        return ExprConstant.constant_to_python(self.constant)

    def to_typescript(self):
        return ExprConstant.constant_to_typescript(self.constant)

    @staticmethod
    def constant_to_python(val: Any) -> str:
        if isinstance(val, bool) or val is None:
            return str(val)
        if isinstance(val, (str, int, float)):
            return json.dumps(val)
        if isinstance(val, list):
            return (
                "[" + ", ".join([ExprConstant.constant_to_python(v) for v in val]) + "]"
            )
        if isinstance(val, dict):
            return (
                "{"
                + ", ".join(
                    [
                        f"{ExprConstant.constant_to_python(k)}: {ExprConstant.constant_to_python(v)}"
                        for k, v in val.items()
                    ]
                )
                + "}"
            )
        if isinstance(val, set):
            return (
                "{"
                + ", ".join(sorted((ExprConstant.constant_to_python(v) for v in val)))
                + "}"
            )
        if isinstance(val, tuple):
            return (
                "(" + ", ".join([ExprConstant.constant_to_python(v) for v in val]) + ")"
            )
        raise NotImplementedError()

    @staticmethod
    def constant_to_typescript(val: Any) -> str:
        if isinstance(val, bool):
            return str(val).lower()
        if val == "undefined":
            return "undefined"
        if val is None:
            return "null"
        if isinstance(val, (str, int, float)):
            return json.dumps(val)
        if isinstance(val, list):
            return (
                "["
                + ", ".join([ExprConstant.constant_to_typescript(v) for v in val])
                + "]"
            )
        if isinstance(val, dict):
            return (
                "{"
                + ", ".join(
                    [
                        f"{ExprConstant.constant_to_typescript(k)}: {ExprConstant.constant_to_typescript(v)}"
                        for k, v in val.items()
                    ]
                )
                + "}"
            )
        if isinstance(val, set):
            return (
                "new Set(["
                + ", ".join([ExprConstant.constant_to_typescript(v) for v in val])
                + "])"
            )
        raise NotImplementedError()


@dataclass
class ExprIdent(Expr):
    ident: str

    def to_python(self):
        return self.ident

    def to_typescript(self):
        return self.ident


@dataclass
class ExprRawPython(Expr):
    code: str

    def to_python(self):
        return self.code


@dataclass
class ExprRawTypescript(Expr):
    code: str

    def to_python(self):
        raise NotImplementedError("Raw Typescript cannot be converted to Python")

    def to_typescript(self):
        return self.code


@dataclass
class ExprVar(Expr):  # a special identifier
    var: Var

    def to_python(self):
        return self.var.get_name()


@dataclass
class ExprFuncCall(Expr):
    func_name: Expr
    args: Sequence[Expr]

    def to_python(self):
        return f"{self.func_name.to_python()}({', '.join([arg.to_python() for arg in self.args])})"

    def to_typescript(self):
        return f"{self.func_name.to_typescript()}({', '.join([arg.to_typescript() for arg in self.args])})"


@dataclass
class ExprAwait(Expr):
    expr: Expr

    def to_python(self):
        return f"(await {self.expr.to_python()})"

    def to_typescript(self):
        return f"(await {self.expr.to_typescript()})"


@dataclass
class ExprNewInstance(Expr):
    class_name: Expr
    args: Sequence[Expr]

    def to_python(self):
        return f"{self.class_name.to_python()}({', '.join([arg.to_python() for arg in self.args])})"

    def to_typescript(self):
        return f"new {self.class_name.to_typescript()}({', '.join([arg.to_typescript() for arg in self.args])})"


@dataclass
class ExprMethodCall(Expr):
    object: Expr
    method: str
    args: Sequence[Expr]

    def to_python(self):
        if self.method == "__contains__" and len(self.args) == 1:
            return f"{self.args[0].to_python()} in {self.object.to_python()}"
        return f"{self.object.to_python()}.{self.method}({', '.join([arg.to_python() for arg in self.args])})"

    def to_typescript(self):
        return f"{self.object.to_typescript()}.{self.method}({', '.join([arg.to_typescript() for arg in self.args])})"


@dataclass
class ExprNotEqual(Expr):
    left: Expr
    right: Expr

    def to_python(self):
        return f"{self.left.to_python()} != {self.right.to_python()}"

    def to_typescript(self):
        return f"{self.left.to_typescript()} !== {self.right.to_typescript()}"


@dataclass
class ExprLessThanOrEqual(Expr):
    left: Expr
    right: Expr

    def to_python(self):
        return f"{self.left.to_python()} < {self.right.to_python()}"


@dataclass
class ExprEqual(Expr):
    left: Expr
    right: Expr

    def to_python(self):
        return f"{self.left.to_python()} == {self.right.to_python()}"

    def to_typescript(self):
        return f"{self.left.to_typescript()} === {self.right.to_typescript()}"


@dataclass
class ExprIs(Expr):
    left: Expr
    right: Expr

    def to_python(self):
        return f"{self.left.to_python()} is {self.right.to_python()}"


@dataclass
class ExprNegation(Expr):
    expr: Expr

    def to_python(self):
        if isinstance(self.expr, ExprIs):
            return f"{self.expr.left.to_python()} is not {self.expr.right.to_python()}"
        return f"not {self.expr.to_wrapped_python()}"


@dataclass
class ExprLogicalAnd(Expr):
    terms: Sequence[Expr]

    def to_python(self):
        return f" and ".join([term.to_python() for term in self.terms])

    def to_typescript(self):
        return f" && ".join([term.to_typescript() for term in self.terms])


@dataclass
class ExprLogicalOr(Expr):
    terms: Sequence[Expr]

    def to_python(self):
        return f" or ".join([term.to_python() for term in self.terms])

    def to_typescript(self):
        return f" || ".join([term.to_typescript() for term in self.terms])


@dataclass
class ExprDivision(Expr):
    left: Expr
    right: Expr

    def to_python(self):
        return f"{self.left.to_python()} / {self.right.to_python()}"


@dataclass
class ExprTernary(Expr):
    condition: Expr
    true_expr: Expr
    false_expr: Expr

    def to_python(self):
        return f"{self.true_expr.to_python()} if {self.condition.to_python()} else {self.false_expr.to_python()}"

    def to_typescript(self):
        return f"{self.condition.to_typescript()} ? {self.true_expr.to_typescript()} : {self.false_expr.to_typescript()}"


class PredefinedFn:
    @dataclass
    class is_null(Expr):
        expr: Expr

        def to_python(self):
            return f"{self.expr.to_python()} is None"

    @dataclass
    class tuple(Expr):
        items: Sequence[Expr]

        def to_python(self):
            if len(self.items) == 1:
                return f"({self.items[0].to_python()},)"
            return f"({', '.join([item.to_python() for item in self.items])})"

    @dataclass
    class set(Expr):
        items: Sequence[Expr]

        def to_python(self):
            return f"{{{', '.join([item.to_python() for item in self.items])}}}"

    @dataclass
    class list(Expr):
        items: Sequence[Expr]

        def to_python(self):
            return f"[{', '.join([item.to_python() for item in self.items])}]"

        def to_typescript(self):
            return f"[{', '.join([item.to_typescript() for item in self.items])}]"

    @dataclass
    class dict(Expr):
        items: Sequence[tuple[Expr, Expr]]

        def to_python(self):
            return (
                "{"
                + ", ".join(
                    [
                        f"{key.to_python()}: {value.to_python()}"
                        for key, value in self.items
                    ]
                )
                + "}"
            )

        def to_typescript(self):
            return (
                "{"
                + ", ".join(
                    [
                        f"{key.to_typescript()}: {value.to_typescript()}"
                        for key, value in self.items
                    ]
                )
                + "}"
            )

    @dataclass
    class attr_getter(Expr):
        collection: Expr
        attr: Expr

        def to_python(self):
            return f"{self.collection.to_python()}.{self.attr.to_python()}"

        def to_typescript(self):
            return f"{self.collection.to_typescript()}.{self.attr.to_typescript()}"

    @dataclass
    class attr_setter(Expr):
        collection: Expr
        attr: Expr
        value: Expr

        def to_python(self):
            return f"{self.collection.to_python()}.{self.attr.to_python()} = {self.value.to_python()}"

        def to_typescript(self):
            return f"{self.collection.to_typescript()}.{self.attr.to_typescript()} = {self.value.to_typescript()};"

    @dataclass
    class item_getter(Expr):
        collection: Expr
        item: Expr

        def to_python(self):
            return f"{self.collection.to_python()}[{self.item.to_python()}]"

    @dataclass
    class item_setter(Expr):
        collection: Expr
        item: Expr
        value: Expr

        def to_python(self):
            return f"{self.collection.to_python()}[{self.item.to_python()}] = {self.value.to_python()}"

    @dataclass
    class len(Expr):
        collection: Expr

        def to_python(self):
            return f"len({self.collection.to_python()})"

    @dataclass(init=False)
    class map_list(Expr):
        collection: Expr
        func: Expr
        filter: Optional[Expr] = None

        def __init__(
            self,
            collection: Expr,
            func: Callable[[ExprIdent], Expr],
            filter: Optional[Callable[[ExprIdent], Expr]] = None,
        ):
            self.collection = collection
            self.func = func(ExprIdent("_x"))
            self.filter = filter(ExprIdent("_x")) if filter is not None else None

        def to_python(self):
            if self.filter is not None:
                return f"[{self.func.to_python()} for _x in {self.collection.to_python()} if {self.filter.to_python()}]"
            return f"[{self.func.to_python()} for _x in {self.collection.to_python()}]"

        def to_typescript(self):
            if self.filter is not None:
                return f"{self.collection.to_typescript()}.filter((_x: any) => {self.filter.to_typescript()}).map((_x: any) => {self.func.to_typescript()})"
            return f"{self.collection.to_typescript()}.map((_x: any) => {self.func.to_typescript()})"

    @dataclass
    class range(Expr):
        start: Expr
        end: Expr
        step: Optional[Expr] = None

        def to_python(self):
            if self.step is not None:
                return f"range({self.start.to_python()}, {self.end.to_python()}, {self.step.to_python()})"
            return f"range({self.start.to_python()}, {self.end.to_python()})"

    @dataclass
    class set_contains(Expr):
        set_: Expr
        item: Expr

        def to_python(self):
            return f"{self.item.to_wrapped_python()} in {self.set_.to_wrapped_python()}"

    @dataclass
    class list_append(Expr):
        lst: Expr
        item: Expr

        def to_python(self):
            return f"{self.lst.to_wrapped_python()}.append({self.item.to_python()})"

    @dataclass
    class has_item(Expr):
        collection: Expr
        item: Expr

        def to_python(self):
            return f"{self.item.to_wrapped_python()} in {self.collection.to_wrapped_python()}"

    @dataclass
    class not_has_item(Expr):
        collection: Expr
        item: Expr

        def to_python(self):
            return f"{self.item.to_wrapped_python()} not in {self.collection.to_wrapped_python()}"

    @dataclass
    class base_error(ExceptionExpr):
        msg: str

        def to_python(self):
            return f"Exception('{self.msg}')"

    @dataclass
    class key_error(ExceptionExpr):
        msg: str

        def to_python(self):
            return f"KeyError('{self.msg}')"

    @dataclass
    class keyword_assignment(Expr):
        keyword: str
        value: Expr

        def to_python(self):
            return f"{self.keyword}={self.value.to_python()}"
