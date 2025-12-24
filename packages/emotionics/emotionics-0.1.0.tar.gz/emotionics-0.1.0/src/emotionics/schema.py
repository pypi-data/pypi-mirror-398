# src/emotionics/schema.py
from __future__ import annotations
from typing import Literal, TypedDict

class LiteResult(TypedDict):
    mode: Literal["lite"]
    version: str
    trust: float
    surprise: float
    joy: float
    fear: float
    confidence: float