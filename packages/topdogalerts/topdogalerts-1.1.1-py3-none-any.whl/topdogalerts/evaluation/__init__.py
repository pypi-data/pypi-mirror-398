# topdogalerts/evaluation/__init__.py
"""
Trigger evaluation module for topdogalerts.

Provides boolean expression parsing and evaluation for trigger matching.
"""
from .evaluator import evaluate
from .expression_ast import BinaryOp, Expression, Literal, UnaryOp, Variable
from .expression_evaluator import (
    ExpressionEvaluationError,
    ExpressionEvaluator,
    evaluate_expression,
    validate_expression,
)
from .expression_parser import (
    ExpressionParseError,
    Parser,
    Tokenizer,
    parse_expression,
)

__all__ = [
    # Main entry point
    "evaluate",
    # Expression evaluation
    "evaluate_expression",
    "validate_expression",
    "ExpressionEvaluator",
    "ExpressionEvaluationError",
    # Expression parsing
    "parse_expression",
    "Parser",
    "Tokenizer",
    "ExpressionParseError",
    # AST nodes
    "Expression",
    "Literal",
    "Variable",
    "BinaryOp",
    "UnaryOp",
]
