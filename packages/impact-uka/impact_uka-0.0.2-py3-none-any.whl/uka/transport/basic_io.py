#!/usr/bin/env python
#
# ----------------------------------------------------------------------------

from __future__ import annotations

import struct
from typing import Union

# ============================================================================

class BasicIO:

    SIZEOF_int = 4

    # ------------------------------------------------------------------------

    @staticmethod
    def insert(buffer: bytearray, pos: int, i: int) -> int:
        buffer[pos:pos + 4] = struct.pack(">i", int(i))
        return pos + 4

    # ------------------------------------------------------------------------

    @staticmethod
    def extract_int(buffer: Union[bytes, bytearray, memoryview], pos: int) -> int:
        return struct.unpack_from(">i", buffer, pos)[0]

    # ------------------------------------------------------------------------


# ============================================================================
