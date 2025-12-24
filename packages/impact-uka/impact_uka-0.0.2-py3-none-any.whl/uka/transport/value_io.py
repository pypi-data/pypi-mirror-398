#!/usr/bin/env python
#
# ----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, List, Optional

# ----------------------------------------------------------------------------

from uka.transport.marshal_stream import MarshalStream
from uka.transport.unmarshal_stream import UnmarshalStream


# ============================================================================

class ValueIO:

    # ------------------------------------------------------------------------
    """
    Optional: Big-endian ValueIO matrix encoding
    
      If you decide on a simple encoding for double[][] / List[List[float]], a typical choice is:

      * write rows (int32)
      * write cols (int32)
      * write rows * cols doubles in row-major order
    """
    # ------------------------------------------------------------------------

    @staticmethod
    def write_value(stream: MarshalStream, ds: List[List[float]]) -> None:
        rows = len(ds)
        cols = len(ds[0]) if rows else 0
        stream.write_int(rows)
        stream.write_int(cols)
        for r in range(rows):
            if len(ds[r]) != cols:
                raise ValueError("ragged matrix not supported")
            for c in range(cols):
                stream.write_double(ds[r][c])

    # ------------------------------------------------------------------------

    @staticmethod
    def read_value_array_array_double(stream: UnmarshalStream) -> List[List[float]]:
        rows = stream.read_int()
        cols = stream.read_int()
        out: List[List[float]] = [[0.0] * cols for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                out[r][c] = stream.read_double()
        return out

    # ------------------------------------------------------------------------


# ============================================================================