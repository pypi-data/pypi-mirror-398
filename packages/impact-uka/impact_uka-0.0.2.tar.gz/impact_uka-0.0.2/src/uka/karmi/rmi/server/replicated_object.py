#!/usr/bin/env python
#
# ----------------------------------------------------------------------------

from __future__ import annotations

from typing import Iterable, List, Optional

from .remote_stub import RemoteStub

# ============================================================================

class ReplicatedObject:

    # ------------------------------------------------------------------------

    def __init__(self, stubs: Optional[Iterable[RemoteStub]] = None) -> None:
        self._stubs: List[RemoteStub] = list(stubs) if stubs is not None else []

    # ------------------------------------------------------------------------

    def collective_update(self) -> None:
        raise NotImplementedError

    # ------------------------------------------------------------------------

    def exclusive_update(self) -> None:
        raise NotImplementedError

    # ------------------------------------------------------------------------


# ============================================================================
