#!/usr/bin/env python
#
# ----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, Protocol

from uka.transport import UnmarshalStream


# ============================================================================

class PatchInput(Protocol):

    # ------------------------------------------------------------------------
    # diff presence
    # ------------------------------------------------------------------------

    def has_diff(self) -> bool:
        ...

    # ------------------------------------------------------------------------
    # primitive diffs (Python uses int for byte/char/short)
    # ------------------------------------------------------------------------

    def get_diff_as_boolean(self) -> bool:
        ...

    def get_diff_as_byte(self) -> int:
        ...

    def get_diff_as_char(self) -> int:
        ...

    def get_diff_as_short(self) -> int:
        ...

    def get_diff_as_int(self) -> int:
        ...

    def get_diff_as_float(self) -> float:
        ...

    def get_diff_as_long(self) -> int:
        ...

    def get_diff_as_double(self) -> float:
        ...

    # ------------------------------------------------------------------------
    # reference diff
    # ------------------------------------------------------------------------

    def get_diff_as_object(self) -> Any:
        ...

    # ------------------------------------------------------------------------
    # patch application helper
    # ------------------------------------------------------------------------

    def apply_patch_anonymous(self, r: Any, c: Any) -> None:
        ...

    # ------------------------------------------------------------------------
    # low-level access
    # ------------------------------------------------------------------------

    def get_input(self) -> UnmarshalStream:
        ...

    def get_from_rank(self) -> int:
        ...

    # ------------------------------------------------------------------------


# ============================================================================
