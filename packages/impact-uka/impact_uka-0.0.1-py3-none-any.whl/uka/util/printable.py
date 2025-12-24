#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
Printable interface from uka.util.

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License or (at your option) any later version.
"""
# -----------------------------------------------------------------------------

from abc import ABC


class Printable(ABC):
    """
    Marker interface for printable objects.
    
    Classes implementing this interface indicate they can be printed/serialized
    using the ToString utility class.
    
    In Python, this is implemented as an abstract base class (ABC) that can be
    used with isinstance() checks or as a mixin.
    
    Usage:
        class MyClass(Printable):
            def append_to(self, s: 'ToString') -> None:
                s.append("field_name", self.field_value)
    """
    pass

