#!/usr/bin/env python
#
# ----------------------------------------------------------------------------

from __future__ import annotations

import struct

from typing import Any, Dict, Optional

# ============================================================================

class UnmarshalStream:

    # ------------------------------------------------------------------------

    def __init__(self, buffer: Optional[bytes | bytearray | memoryview] = None) -> None:
        self._buffer = bytearray(buffer) if buffer is not None else bytearray()
        self._pos = 0
        self._registry: Dict[int, Any] = {}

    # ------------------------------------------------------------------------

    def request(self, size: int) -> None:
        if size < 0:
            raise ValueError("size must be >= 0")
        required = self._pos + size
        if required > len(self._buffer):
            raise EOFError(f"requested {size} bytes but only {len(self._buffer) - self._pos} available")

    # ------------------------------------------------------------------------

    def get_buffer(self) -> bytearray:
        return self._buffer

    # ------------------------------------------------------------------------

    def get_position(self) -> int:
        return self._pos

    # ------------------------------------------------------------------------

    def accept(self, size: int) -> None:
        if size < 0:
            raise ValueError("size must be >= 0")
        self.request(size)
        self._pos += size

    # ------------------------------------------------------------------------

    def register(self, matrix: Any, _id: int) -> None:
        self._registry[int(_id)] = matrix

    # ------------------------------------------------------------------------
    # add big-endian readers
    # ------------------------------------------------------------------------

    def read_int(self) -> int:
        self.request(4)
        value = struct.unpack_from(">i", self._buffer, self._pos)[0]
        self.accept(4)
        return value

    # ------------------------------------------------------------------------

    def read_double(self) -> float:
        self.request(8)
        value = struct.unpack_from(">d", self._buffer, self._pos)[0]
        self.accept(8)
        return value

    # ------------------------------------------------------------------------

    def read_bytes(self, n: int) -> bytes:
        self.request(n)
        data = bytes(self._buffer[self._pos:self._pos + n])
        self.accept(n)
        return data

    # ------------------------------------------------------------------------

# ============================================================================

"""
Notes:
1)  Java imports Jama.Matrix; in Python we don’t have that, so register() just stores any object keyed by id.

    * request() raises EOFError if the buffer doesn’t contain enough bytes—this is the most Pythonic
      equivalent of “can’t read more”.

2)  Optional follow-up (after encoding is decided)

    Once you confirm endianness/format, we can add convenience methods:

    * read_int(), 
    * read_double(), 
    * maybe read_matrix()

    that use struct.unpack_from(...) and call accept(n) internally.
"""