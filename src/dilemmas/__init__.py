"""
Dilemma loaders for moral decision consistency research.

V1: loader.py - Classic moral dilemmas (trolley, AV, etc.)
V2: loader_v2.py - Novel OOD dilemmas with probe questions
"""

from .loader import DilemmaLoader
from .loader_v2 import DilemmaLoaderV2

__all__ = [
    "DilemmaLoader",
    "DilemmaLoaderV2",
]
