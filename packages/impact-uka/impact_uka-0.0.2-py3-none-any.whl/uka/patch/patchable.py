#!/usr/bin/env python
#
# ----------------------------------------------------------------------------

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from uka.patch.patch_input import PatchInput
    from uka.patch.patch_output import PatchOutput


# ============================================================================

class Patchable(ABC):

    # ------------------------------------------------------------------------

    @abstractmethod
    def create_patch(self, copy: Any, out: "PatchOutput") -> None:
        raise NotImplementedError

    # ------------------------------------------------------------------------

    @abstractmethod
    def apply_patch(self, copy: Any, inp: "PatchInput") -> None:
        raise NotImplementedError

    # ------------------------------------------------------------------------


# ============================================================================
