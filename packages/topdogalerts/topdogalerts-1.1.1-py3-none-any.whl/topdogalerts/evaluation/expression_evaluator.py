# topdogalerts/evaluation/expression_evaluator.py
"""
Expression evaluator for trigger expressions.

Evaluates parsed AST nodes against event attributes and trigger values.
Includes automatic type coercion for trigger value columns.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

from .expression_ast import BinaryOp, Expression, Literal, UnaryOp, Variable
from .expression_parser import ExpressionParseError, parse_expression

logger = logging.getLogger(__name__)


class ExpressionEvaluationError(Exception):
    """Raised when expression evaluation fails."""
    pass


# Regex patterns for trigger value column names
NUMBER_VALUE_PATTERN = re.compile(r'^number_value\d+$')
DATETIME_VALUE_PATTERN = re.compile(r'^datetime_value\d+$')
STRING_VALUE_PATTERN = re.compile(r'^string_value\d+$')


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    """
    Parse an ISO 8601 datetime string to a datetime object.

    Handles common formats including "Z" suffix for UTC.
    All datetimes are normalized to UTC.

    Args:
        value: The value to parse (should be a string).

    Returns:
        A timezone-aware datetime in UTC, or None if parsing fails.
    """
    if isinstance(value, datetime):
        # Already a datetime, ensure it's UTC
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if not isinstance(value, str):
        return None

    # Handle "Z" suffix (replace with +00:00 for fromisoformat)
    normalized = value.replace("Z", "+00:00")

    try:
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _coerce_to_float(value: Any) -> Optional[float]:
    """
    Coerce a value to float for numeric comparison.

    Args:
        value: The value to coerce.

    Returns:
        Float value, or None if coercion fails.
    """
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    return None


def _coerce_values_for_comparison(
    left: Any,
    right: Any,
    left_name: Optional[str],
    right_name: Optional[str],
) -> Tuple[Any, Any, Optional[str]]:
    """
    Coerce values for comparison based on variable names.

    Detects trigger value column patterns (number_value*, datetime_value*, string_value*)
    and coerces both values to appropriate types.

    Args:
        left: Left operand value
        right: Right operand value
        left_name: Variable name of left operand (if it was a Variable node)
        right_name: Variable name of right operand (if it was a Variable node)

    Returns:
        Tuple of (coerced_left, coerced_right, warning_message or None)
    """
    warning = None

    # Determine target type based on variable names
    is_number_comparison = False
    is_datetime_comparison = False

    for name in (left_name, right_name):
        if name:
            if NUMBER_VALUE_PATTERN.match(name):
                is_number_comparison = True
            elif DATETIME_VALUE_PATTERN.match(name):
                is_datetime_comparison = True

    # Also detect if comparing event attributes that look numeric
    # (e.g., rsi, prev_rsi, pct_change, etc.)
    if isinstance(left, (int, float)) or isinstance(right, (int, float)):
        is_number_comparison = True

    if is_datetime_comparison:
        # Coerce both to datetime
        left_dt = _parse_iso_datetime(left)
        right_dt = _parse_iso_datetime(right)

        if left_dt is None or right_dt is None:
            warning = (
                f"Datetime coercion failed: left={left!r} ({type(left).__name__}), "
                f"right={right!r} ({type(right).__name__})"
            )
            return left, right, warning

        return left_dt, right_dt, None

    if is_number_comparison:
        # Coerce both to float
        left_float = _coerce_to_float(left)
        right_float = _coerce_to_float(right)

        if left_float is None or right_float is None:
            warning = (
                f"Numeric coercion failed: left={left!r} ({type(left).__name__}), "
                f"right={right!r} ({type(right).__name__})"
            )
            return left, right, warning

        return left_float, right_float, None

    # Default: no coercion needed (string comparison or mixed types)
    return left, right, None


class ExpressionEvaluator:
    """
    Evaluates a parsed expression AST against event attributes and trigger values.

    The evaluator resolves variables by looking up:
    1. Event attributes (product, timeframe, rsi, etc.)
    2. Trigger values (string_value1, number_value1, etc.)

    Includes automatic type coercion:
    - number_value* columns are coerced to float
    - datetime_value* columns are parsed as ISO 8601 (UTC)
    - string_value* columns remain as strings
    """

    COMPARISON_OPS = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        "<": lambda a, b: a < b,
        ">": lambda a, b: a > b,
        "<=": lambda a, b: a <= b,
        ">=": lambda a, b: a >= b,
    }

    def __init__(self) -> None:
        self._variable_names: Dict[int, str] = {}  # node id -> variable name

    def evaluate(
        self,
        expression: Expression,
        attributes: Dict[str, Any],
        trigger_values: Dict[str, Any],
    ) -> bool:
        """
        Evaluate an expression AST against attributes and trigger values.
        """
        self._variable_names.clear()
        return self._evaluate_node(expression, attributes, trigger_values)

    def _evaluate_node(
        self,
        node: Expression,
        attributes: Dict[str, Any],
        trigger_values: Dict[str, Any],
    ) -> Any:
        """Recursively evaluate an AST node."""
        if isinstance(node, Literal):
            return node.value

        elif isinstance(node, Variable):
            value = self._resolve_variable(node.name, attributes, trigger_values)
            # Track variable name for type coercion
            self._variable_names[id(node)] = node.name
            return value

        elif isinstance(node, BinaryOp):
            return self._evaluate_binary_op(node, attributes, trigger_values)

        elif isinstance(node, UnaryOp):
            return self._evaluate_unary_op(node, attributes, trigger_values)

        else:
            raise ExpressionEvaluationError(f"Unknown node type: {type(node)}")

    def _resolve_variable(
        self,
        name: str,
        attributes: Dict[str, Any],
        trigger_values: Dict[str, Any],
    ) -> Any:
        """Resolve a variable name to its value."""
        if name in attributes:
            return attributes[name]
        elif name in trigger_values:
            return trigger_values[name]
        else:
            raise ExpressionEvaluationError(
                f"Unknown variable '{name}'. "
                f"Available: attributes={list(attributes.keys())}, "
                f"trigger_values={list(trigger_values.keys())}"
            )

    def _get_variable_name(self, node: Expression) -> Optional[str]:
        """Get the variable name for a node if it was a Variable."""
        if isinstance(node, Variable):
            return node.name
        return None

    def _evaluate_binary_op(
        self,
        node: BinaryOp,
        attributes: Dict[str, Any],
        trigger_values: Dict[str, Any],
    ) -> Any:
        """Evaluate a binary operation."""
        # Short-circuit evaluation for logical operators
        if node.operator == "AND":
            left = self._evaluate_node(node.left, attributes, trigger_values)
            if not left:
                return False
            return bool(self._evaluate_node(node.right, attributes, trigger_values))

        elif node.operator == "OR":
            left = self._evaluate_node(node.left, attributes, trigger_values)
            if left:
                return True
            return bool(self._evaluate_node(node.right, attributes, trigger_values))

        # Comparison operators with type coercion
        elif node.operator in self.COMPARISON_OPS:
            # Get variable names before evaluation (for type coercion)
            left_name = self._get_variable_name(node.left)
            right_name = self._get_variable_name(node.right)

            left = self._evaluate_node(node.left, attributes, trigger_values)
            right = self._evaluate_node(node.right, attributes, trigger_values)

            # Apply type coercion
            left, right, warning = _coerce_values_for_comparison(
                left, right, left_name, right_name
            )

            if warning:
                logger.warning(f"Type coercion issue: {warning}")

            try:
                return self.COMPARISON_OPS[node.operator](left, right)
            except TypeError as e:
                raise ExpressionEvaluationError(
                    f"Cannot compare {type(left).__name__} ({left!r}) and "
                    f"{type(right).__name__} ({right!r}) with operator '{node.operator}': {e}"
                )

        else:
            raise ExpressionEvaluationError(f"Unknown operator: {node.operator}")

    def _evaluate_unary_op(
        self,
        node: UnaryOp,
        attributes: Dict[str, Any],
        trigger_values: Dict[str, Any],
    ) -> Any:
        """Evaluate a unary operation."""
        if node.operator == "NOT":
            operand = self._evaluate_node(node.operand, attributes, trigger_values)
            return not operand
        else:
            raise ExpressionEvaluationError(f"Unknown unary operator: {node.operator}")


# Cache parsed expressions for performance
@lru_cache(maxsize=128)
def _cached_parse(expression: str) -> Expression:
    """Parse and cache an expression string."""
    return parse_expression(expression)


def evaluate_expression(
    expression: str,
    attributes: Dict[str, Any],
    trigger_values: Dict[str, Any],
) -> bool:
    """
    Parse and evaluate a boolean expression string.

    This is the main entry point for evaluating trigger expressions.
    Parsed expressions are cached for performance.

    Args:
        expression: The expression string to evaluate.
        attributes: Event attributes (product, timeframe, rsi, etc.)
        trigger_values: Trigger values (string_value1, number_value1, etc.)

    Returns:
        Boolean result of the expression.

    Raises:
        ExpressionParseError: If the expression is malformed.
        ExpressionEvaluationError: If evaluation fails.
    """
    ast = _cached_parse(expression)
    evaluator = ExpressionEvaluator()
    return evaluator.evaluate(ast, attributes, trigger_values)


def validate_expression(expression: str) -> Optional[str]:
    """
    Validate an expression string without evaluating it.

    Args:
        expression: The expression string to validate.

    Returns:
        None if valid, or an error message string if invalid.
    """
    try:
        parse_expression(expression)
        return None
    except ExpressionParseError as e:
        return str(e)
