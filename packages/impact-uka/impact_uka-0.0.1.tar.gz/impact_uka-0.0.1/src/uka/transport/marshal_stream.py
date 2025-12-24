#!/usr/bin/env python
#
# ----------------------------------------------------------------------------

from __future__ import annotations

import struct


# ============================================================================

class MarshalStream:

    # ------------------------------------------------------------------------

    def __init__(self) -> None:
        self._buffer = bytearray()
        self._pos = 0

    # ------------------------------------------------------------------------

    def reserve(self, size: int) -> None:
        if size < 0:
            raise ValueError("size must be >= 0")
        required = self._pos + size
        if required > len(self._buffer):
            self._buffer.extend(b"\x00" * (required - len(self._buffer)))

    # ------------------------------------------------------------------------

    def get_buffer(self) -> bytearray:
        return self._buffer

    # ------------------------------------------------------------------------

    def get_position(self) -> int:
        return self._pos

    # ------------------------------------------------------------------------

    def deliver(self, size: int) -> None:
        if size < 0:
            raise ValueError("size must be >= 0")
        self._pos += size

    # ------------------------------------------------------------------------
    # big-endian Implementation
    # ------------------------------------------------------------------------

    def write_int(self, value: int) -> None:
        self.reserve(4)
        struct.pack_into(">i", self._buffer, self._pos, int(value))
        self.deliver(4)

    # ------------------------------------------------------------------------

    def write_double(self, value: float) -> None:
        self.reserve(8)
        struct.pack_into(">d", self._buffer, self._pos, float(value))
        self.deliver(8)

    # ------------------------------------------------------------------------

    def write_bytes(self, data: bytes | bytearray | memoryview) -> None:
        data = bytes(data)
        self.reserve(len(data))
        self._buffer[self._pos:self._pos + len(data)] = data
        self.deliver(len(data))

    # ------------------------------------------------------------------------


# ============================================================================

