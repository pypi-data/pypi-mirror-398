#!/usr/bin/env python
#
# ----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, Optional, Protocol

from uka.transport import MarshalStream

# ============================================================================

class PatchOutput(Protocol):

    # ------------------------------------------------------------------------
    # primitive diffs (Python uses int for byte/char/short/long)
    # ------------------------------------------------------------------------

    def write_diff_boolean(self, v: bool, c: bool) -> bool:
        ...

    def write_diff_byte(self, v: int, c: int) -> bool:
        ...

    def write_diff_char(self, v: int, c: int) -> bool:
        ...

    def write_diff_short(self, v: int, c: int) -> bool:
        ...

    def write_diff_int(self, v: int, c: int) -> bool:
        ...

    def write_diff_float(self, v: float, c: float) -> bool:
        ...

    def write_diff_long(self, v: int, c: int) -> bool:
        ...

    def write_diff_double(self, v: float, c: float) -> bool:
        ...

    # ------------------------------------------------------------------------
    # reference diffs
    # ------------------------------------------------------------------------

    def write_diff_object(self, r: Any, c: Any) -> Optional[Any]:
        ...

    def create_patch_anonymous(self, r: Any, c: Any) -> None:
        ...

    # ------------------------------------------------------------------------
    # low-level access
    # ------------------------------------------------------------------------

    def get_output(self, rank: int) -> MarshalStream:
        ...

    # ------------------------------------------------------------------------


# ============================================================================
