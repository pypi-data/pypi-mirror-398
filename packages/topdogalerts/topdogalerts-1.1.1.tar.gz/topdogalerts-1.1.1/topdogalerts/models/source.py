# topdogalerts/models/source.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Source:
    id: str
    name: Optional[str]
    access: Optional[str]
