from __future__ import annotations

from typing import Literal, TypeAlias

KEY = str | tuple
NO_KEY = tuple()
REGISTER_TYPE = Literal["var"]

AST_ID: TypeAlias = tuple[int, ...]
