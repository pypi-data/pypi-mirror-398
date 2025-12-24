#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
ToString utility class from uka.util.

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License or (at your option) any later version.
"""
# -----------------------------------------------------------------------------

from typing import Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    # Avoid circular import - Element will be from run package
    pass


class ToString:
    """
    Utility class for building string representations of objects.
    
    Used by Printable objects to construct their string representation
    by appending named field values.
    
    Usage:
        s = ToString()
        s.append("name", "value")
        s.append("matrix", [[1, 2], [3, 4]])
        print(str(s))
    """
    
    def __init__(self):
        """Initialize an empty ToString builder."""
        self._parts: List[str] = []
    
    def append(self, name: str, value: Any) -> None:
        """
        Append a named value to the string representation.
        
        This method handles multiple types:
        - str: string values
        - List[List[float]]: 2D arrays (matrices)
        - Element: run.Element objects (stubbed)
        - Any other type: uses str() conversion
        
        Args:
            name: The field/attribute name.
            value: The value to append.
        """
        if value is None:
            self._parts.append(f"{name}=None")
        elif isinstance(value, str):
            self._append_string(name, value)
        elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], list):
            self._append_2d_array(name, value)
        else:
            # Generic handling for other types including Element
            self._parts.append(f"{name}={value}")
    
    def _append_string(self, name: str, value: str) -> None:
        """
        Append a string value.
        
        Args:
            name: The field name.
            value: The string value.
        """
        self._parts.append(f'{name}="{value}"')
    
    def _append_2d_array(self, name: str, a: List[List[float]]) -> None:
        """
        Append a 2D array (matrix).
        
        Args:
            name: The field name.
            a: The 2D array of floats.
        """
        if not a:
            self._parts.append(f"{name}=[]")
            return
        
        rows = len(a)
        cols = len(a[0]) if a else 0
        
        # Format as compact matrix representation
        formatted = f"{name}=[{rows}x{cols} matrix]"
        self._parts.append(formatted)
    
    def __str__(self) -> str:
        """
        Return the complete string representation.
        
        Returns:
            A string with all appended name=value pairs.
        """
        if not self._parts:
            return "{}"
        return "{" + ", ".join(self._parts) + "}"
    
    def __repr__(self) -> str:
        """Return a detailed representation."""
        return f"ToString({self._parts})"




