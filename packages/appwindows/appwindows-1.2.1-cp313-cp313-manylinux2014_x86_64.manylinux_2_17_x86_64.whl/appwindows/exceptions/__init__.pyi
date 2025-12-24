"""
exception classes
"""
from __future__ import annotations
__all__: list[str] = ['InvalidSizeException', 'WindowDoesNotFoundException', 'WindowDoesNotValidException']
class InvalidSizeException(Exception):
    pass
class WindowDoesNotFoundException(Exception):
    pass
class WindowDoesNotValidException(Exception):
    pass
