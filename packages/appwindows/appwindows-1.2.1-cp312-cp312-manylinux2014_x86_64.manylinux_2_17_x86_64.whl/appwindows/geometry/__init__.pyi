"""
classes for work with geometry
"""
from __future__ import annotations
import typing
__all__: list[str] = ['Point', 'QuadPoints', 'Size']
class Point:
    """
    Represents a 2D point with x and y coordinates
    """
    __hash__: typing.ClassVar[None] = None
    def __add__(self, arg0: Point) -> Point:
        """
        Add two points
        """
    def __eq__(self, arg0: Point) -> bool:
        """
        Points is equal
        """
    def __init__(self, x: typing.SupportsInt, y: typing.SupportsInt) -> None:
        """
        Create a point with specified coordinates
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
    def __mul__(self, arg0: Point) -> Point:
        """
        Multiply two points
        """
    def __sub__(self, arg0: Point) -> Point:
        """
        Subtract two points
        """
    def __truediv__(self, arg0: Point) -> Point:
        """
        Divide two points
        """
    @property
    def x(self) -> int:
        """
        X coordinate
        """
    @property
    def y(self) -> int:
        """
        Y coordinate
        """
class QuadPoints:
    """
    Vertices of a quadrilateral
    """
    def __init__(self, left_top: Point, right_top: Point, right_bottom: Point, left_bottom: Point) -> None:
        """
        QuadPoints constructor
        
        Args:
            left_top (appwindows.geometry.Point): left top point
            right_top (appwindows.geometry.Point): right top point
            right_bottom (appwindows.geometry.Point): right bottom point
            left_bottom (appwindows.geometry.Point): left bottom point
        """
    @property
    def left_bottom(self) -> Point:
        """
        Left bottom point
        """
    @property
    def left_top(self) -> Point:
        """
        Left top point
        """
    @property
    def right_bottom(self) -> Point:
        """
        Right bottom point
        """
    @property
    def right_top(self) -> Point:
        """
        Right top point
        """
class Size:
    """
    Represents dimensions with width and height
    """
    def __init__(self, width: typing.SupportsInt, height: typing.SupportsInt) -> None:
        """
        Create size with specified dimensions
        
        Args:
            width (int): Width dimension
            height (int): Height dimension
        
        Raises:
            InvalidSizeError: If width or height are invalid
        """
    @property
    def height(self) -> int:
        """
        Height dimension
        """
    @property
    def width(self) -> int:
        """
        Width dimension
        """
