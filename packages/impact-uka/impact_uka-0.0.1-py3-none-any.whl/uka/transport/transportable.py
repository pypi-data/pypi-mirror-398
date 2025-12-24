#!/usr/bin/env python
#
# ----------------------------------------------------------------------------

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# ============================================================================

class Transportable(ABC):

    # ------------------------------------------------------------------------

    @abstractmethod
    def marshal_reference(self, s: Any) -> None:
        raise NotImplementedError

    # ------------------------------------------------------------------------

    @abstractmethod
    def marshal(self, s: Any) -> None:
        raise NotImplementedError

    # ------------------------------------------------------------------------

    @abstractmethod
    def unmarshal(self, s: Any) -> None:
        raise NotImplementedError

    # ------------------------------------------------------------------------


# ============================================================================