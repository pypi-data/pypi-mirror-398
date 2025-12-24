"""
Python bindings for appwindows library

The appwindows library solves the problem of working with a graphical shell on different operating systems.
"""
from __future__ import annotations
import numpy
import numpy.typing
import typing
from . import exceptions
from . import geometry
__all__: list[str] = ['Finder', 'Window', 'exceptions', 'geometry', 'get_finder']
class Finder:
    """
    Interface for finding application windows
    """
    def get_all_titles(self) -> list[str]:
        """
        Get all window titles
        
        Returns:
            list[str]: Found titles
        """
    def get_all_windows(self) -> list[Window]:
        """
        Find all opened windows
        
        Returns:
            list[Window]: Found windows
        """
    def get_os(self) -> str:
        """
        Get os and graphical shell
        
        Returns:
            str: your <<os>>::<<graphical shell>>
        """
    def get_window_by_process_id(self, process_id: typing.SupportsInt) -> Window:
        """
        Find window by process id
        
        Args:
            process_id (int): Window title to search for
        
        Returns:
            Window | None: Found window or null if window does not exist
        
        Raises:
            appwindows.exceptions.WindowDoesNotFoundxception: If window is not found
        """
    def get_window_by_title(self, title: str) -> Window:
        """
        Find window by its title substring
        
        Args:
            title (str): Window title to search for
        
        Returns:
            Window: Found window
        
        Raises:
            appwindows.exceptions.WindowDoesNotFoundxception: If window is not found
        """
class Window:
    """
    Interface representing an application window
    """
    def close(self) -> None:
        """
        Close the window
        """
    def get_points(self) -> geometry.QuadPoints:
        """
        Get all points associated with the window
        
        Returns:
            appwindows.geometry.QuadPoints: QuadPoints object with all points
        
        Raises:
            appwindows.exceptions.WindowDoesNotValidException: If window is invalid
        """
    def get_process_id(self) -> int:
        """
        Get the window process id
        
        Returns:
            int: process id
        
        Raises:
            appwindows.exceptions.WindowDoesNotValidException: If window is invalid
        """
    def get_screenshot(self) -> numpy.typing.NDArray[numpy.uint8]:
        """
        Get current window image
        
        Returns:
            ndarray: image in ndarray
        
        Raises:
            appwindows.exceptions.WindowDoesNotValidException: If window is invalid
        """
    def get_size(self) -> geometry.Size:
        """
        Get current window size
        
        Returns:
            Size: Current window dimensions
        
        Raises:
            appwindows.exceptions.WindowDoesNotValidException: If window is invalid
        """
    def get_title(self) -> str:
        """
        Get the window title
        
        Returns:
            str: Window title
        
        Raises:
            appwindows.exceptions.WindowDoesNotValidException: If window is invalid
        """
    def is_valid(self) -> bool:
        """
        Is window valid
        
        Returns:
            bool: is valid
        
        Raises:
            appwindows.exceptions.WindowDoesNotValidException: If window is invalid
        """
    def move(self, point: geometry.Point) -> None:
        """
        Move window to specified position
        
        Args:
            point (appwindows.geometry.Point): New window position
        
        Raises:
            appwindows.exceptions.WindowDoesNotValidException: If window is invalid
        """
    def resize(self, size: geometry.Size) -> None:
        """
        Resize the window
        
        Args:
            size (appwindows.geometry.Size): New window dimensions
        
        Raises:
            appwindows.exceptions.InvalidSizeError: If size is invalid    appwindows.exceptions.WindowDoesNotValidException: If window is invalid
        """
    def set_fullscreen(self, is_maximize: bool) -> None:
        """
        Maximize or restore the window
        
        Args:
            is_fullscreen (bool): True to window on fullscreen
        
        Raises:
            appwindows.exceptions.WindowDoesNotValidException: If window is invalid
        """
    def set_minimize(self, is_minimize: bool) -> None:
        """
        Set window active state
        
        Args:
            is_minimize (bool): True to activate window
        
        Raises:
            appwindows.exceptions.WindowDoesNotValidException: If window is invalid
        """
    def to_background(self) -> None:
        """
        Moved window to background
        
        Raises:
            appwindows.exceptions.WindowDoesNotValidException: If window is invalid
        """
    def to_foreground(self) -> None:
        """
        Moved window to foreground
        
        Raises:
            appwindows.exceptions.WindowDoesNotValidException: If window is invalid
        """
def get_finder() -> Finder:
    """
    Get the window finder instance
    
    Returns:
        Finder: Instance of window finder interface
    """
