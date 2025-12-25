# topdogalerts/publisher/__init__.py
"""
Message publishing module for topdogalerts.
"""
from .sqs import SqsPublisher

__all__ = ["SqsPublisher"]
