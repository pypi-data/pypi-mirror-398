# topdogalerts/evaluation/expression_ast.py
"""
Abstract Syntax Tree (AST) node classes for trigger expressions.

The expression parser produces these AST nodes, which are then
evaluated against event attributes and trigger values.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union


@dataclass(frozen=True)
class Literal:
    """
    A literal value (string, number, boolean, or null).

    Examples:
        - "up", 'down' (strings)
        - 42, 3.14 (numbers)
        - true, false (booleans)
        - null (null)
    """
    value: Any


@dataclass(frozen=True)
class Variable:
    """
    A variable reference to an event attribute or trigger value.

    Examples:
        - product, timeframe, rsi (event attributes)
        - string_value1, number_value1 (trigger values)
    """
    name: str


@dataclass(frozen=True)
class BinaryOp:
    """
    A binary operation (comparison or logical).

    Comparison operators: ==, !=, <, >, <=, >=
    Logical operators: AND, OR
    """
    left: Expression
    operator: str
    right: Expression


@dataclass(frozen=True)
class UnaryOp:
    """
    A unary operation (currently only NOT).
    """
    operator: str  # "NOT"
    operand: Expression


# Type alias for any expression node
Expression = Union[Literal, Variable, BinaryOp, UnaryOp]
