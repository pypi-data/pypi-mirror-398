# topdogalerts/evaluation/expression_parser.py
"""
Tokenizer and recursive descent parser for trigger expressions.

Parses boolean expressions like:
    product == string_value1 AND (
        (string_value3 == "up" AND prev_rsi < number_value1) OR
        (string_value3 == "down" AND prev_rsi > number_value1)
    )

Grammar (in order of precedence, lowest to highest):
    expression := or_expr
    or_expr    := and_expr (OR and_expr)*
    and_expr   := not_expr (AND not_expr)*
    not_expr   := NOT? comparison
    comparison := primary (comp_op primary)?
    primary    := LPAREN expression RPAREN | literal | variable
    comp_op    := == | != | < | > | <= | >=
    literal    := STRING | NUMBER | BOOLEAN | NULL
    variable   := IDENTIFIER
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, List, Optional

from .expression_ast import BinaryOp, Expression, Literal, UnaryOp, Variable


class TokenType(Enum):
    """Token types for the expression lexer."""
    IDENTIFIER = auto()   # product, string_value1, etc.
    STRING = auto()       # "up", 'down'
    NUMBER = auto()       # 42, 3.14, -10
    BOOLEAN = auto()      # true, false
    NULL = auto()         # null
    EQ = auto()           # ==
    NEQ = auto()          # !=
    LT = auto()           # <
    GT = auto()           # >
    LTE = auto()          # <=
    GTE = auto()          # >=
    AND = auto()          # AND, and
    OR = auto()           # OR, or
    NOT = auto()          # NOT, not
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    EOF = auto()          # End of input


@dataclass
class Token:
    """A single token from the lexer."""
    type: TokenType
    value: Any
    position: int


class ExpressionParseError(Exception):
    """Raised when expression parsing fails."""

    def __init__(self, message: str, position: int, expression: str):
        self.position = position
        self.expression = expression
        # Show context around error
        start = max(0, position - 20)
        end = min(len(expression), position + 20)
        context = expression[start:end]
        pointer = " " * (position - start) + "^"
        super().__init__(f"{message} at position {position}:\n  {context}\n  {pointer}")


class Tokenizer:
    """
    Tokenizes a boolean expression string into tokens.

    Uses regex patterns to identify tokens.
    """

    # Token patterns (order matters - longer matches first)
    PATTERNS = [
        (r'\s+', None),  # Whitespace (skip)
        (r'==', TokenType.EQ),
        (r'!=', TokenType.NEQ),
        (r'<=', TokenType.LTE),
        (r'>=', TokenType.GTE),
        (r'<', TokenType.LT),
        (r'>', TokenType.GT),
        (r'\(', TokenType.LPAREN),
        (r'\)', TokenType.RPAREN),
        (r'"([^"]*)"', TokenType.STRING),  # Double-quoted string
        (r"'([^']*)'", TokenType.STRING),  # Single-quoted string
        (r'-?\d+\.?\d*', TokenType.NUMBER),  # Integer or float (with optional negative)
        (r'(?i)\btrue\b', TokenType.BOOLEAN),
        (r'(?i)\bfalse\b', TokenType.BOOLEAN),
        (r'(?i)\bnull\b', TokenType.NULL),
        (r'(?i)\band\b', TokenType.AND),
        (r'(?i)\bor\b', TokenType.OR),
        (r'(?i)\bnot\b', TokenType.NOT),
        (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER),
    ]

    def __init__(self, expression: str):
        self.expression = expression
        self.position = 0
        self.tokens: List[Token] = []
        self._compiled_patterns = [
            (re.compile(pattern), token_type)
            for pattern, token_type in self.PATTERNS
        ]

    def tokenize(self) -> List[Token]:
        """Tokenize the expression and return list of tokens."""
        self.tokens = []
        self.position = 0

        while self.position < len(self.expression):
            match_found = False

            for pattern, token_type in self._compiled_patterns:
                match = pattern.match(self.expression, self.position)
                if match:
                    if token_type is not None:  # Skip whitespace
                        value = self._extract_value(match, token_type)
                        self.tokens.append(Token(token_type, value, self.position))
                    self.position = match.end()
                    match_found = True
                    break

            if not match_found:
                raise ExpressionParseError(
                    f"Unexpected character '{self.expression[self.position]}'",
                    self.position,
                    self.expression
                )

        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, None, self.position))
        return self.tokens

    def _extract_value(self, match: re.Match, token_type: TokenType) -> Any:
        """Extract and convert the token value."""
        if token_type == TokenType.STRING:
            # Group 1 contains the string without quotes
            return match.group(1)
        elif token_type == TokenType.NUMBER:
            text = match.group(0)
            return float(text) if '.' in text else int(text)
        elif token_type == TokenType.BOOLEAN:
            return match.group(0).lower() == 'true'
        elif token_type == TokenType.NULL:
            return None
        else:
            return match.group(0)


class Parser:
    """
    Recursive descent parser for boolean expressions.

    Produces an AST from a list of tokens.
    """

    COMPARISON_OPS = {
        TokenType.EQ: "==",
        TokenType.NEQ: "!=",
        TokenType.LT: "<",
        TokenType.GT: ">",
        TokenType.LTE: "<=",
        TokenType.GTE: ">=",
    }

    def __init__(self):
        self.tokens: List[Token] = []
        self.current = 0
        self.expression = ""

    def parse(self, expression: str) -> Expression:
        """Parse expression string into AST."""
        self.expression = expression
        tokenizer = Tokenizer(expression)
        self.tokens = tokenizer.tokenize()
        self.current = 0

        ast = self._parse_or_expr()

        # Ensure we consumed all tokens
        if not self._is_at_end():
            raise ExpressionParseError(
                f"Unexpected token '{self._peek().value}'",
                self._peek().position,
                self.expression
            )

        return ast

    def _parse_or_expr(self) -> Expression:
        """or_expr := and_expr (OR and_expr)*"""
        left = self._parse_and_expr()

        while self._match(TokenType.OR):
            right = self._parse_and_expr()
            left = BinaryOp(left, "OR", right)

        return left

    def _parse_and_expr(self) -> Expression:
        """and_expr := not_expr (AND not_expr)*"""
        left = self._parse_not_expr()

        while self._match(TokenType.AND):
            right = self._parse_not_expr()
            left = BinaryOp(left, "AND", right)

        return left

    def _parse_not_expr(self) -> Expression:
        """not_expr := NOT? comparison"""
        if self._match(TokenType.NOT):
            operand = self._parse_not_expr()  # Allow chained NOT
            return UnaryOp("NOT", operand)

        return self._parse_comparison()

    def _parse_comparison(self) -> Expression:
        """comparison := primary (comp_op primary)?"""
        left = self._parse_primary()

        for token_type, operator in self.COMPARISON_OPS.items():
            if self._match(token_type):
                right = self._parse_primary()
                return BinaryOp(left, operator, right)

        return left

    def _parse_primary(self) -> Expression:
        """primary := LPAREN expression RPAREN | literal | variable"""
        # Parenthesized expression
        if self._match(TokenType.LPAREN):
            expr = self._parse_or_expr()
            if not self._match(TokenType.RPAREN):
                raise ExpressionParseError(
                    "Expected ')' after expression",
                    self._peek().position,
                    self.expression
                )
            return expr

        # Literals
        if self._match(TokenType.STRING, TokenType.NUMBER, TokenType.BOOLEAN, TokenType.NULL):
            return Literal(self._previous().value)

        # Variable (identifier)
        if self._match(TokenType.IDENTIFIER):
            return Variable(self._previous().value)

        # Error
        raise ExpressionParseError(
            f"Expected expression, got '{self._peek().value}'",
            self._peek().position,
            self.expression
        )

    def _match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types, and advance if so."""
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        """Check if current token is of the given type."""
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _advance(self) -> Token:
        """Consume current token and return it."""
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        """Check if we've reached the end of tokens."""
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        """Return current token without consuming it."""
        return self.tokens[self.current]

    def _previous(self) -> Token:
        """Return the previously consumed token."""
        return self.tokens[self.current - 1]


def parse_expression(expression: str) -> Expression:
    """
    Parse a boolean expression string into an AST.

    This is the main entry point for parsing expressions.

    Args:
        expression: The expression string to parse.

    Returns:
        The root AST node.

    Raises:
        ExpressionParseError: If the expression is malformed.

    Example:
        >>> ast = parse_expression('product == "BTC-USD" AND rsi > 70')
        >>> isinstance(ast, BinaryOp)
        True
    """
    parser = Parser()
    return parser.parse(expression)
