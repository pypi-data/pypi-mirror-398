from __future__ import annotations

from typing import Optional

# ============================================================================

class RemoteException(OSError):

    # ------------------------------------------------------------------------

    def __init__(self, message: Optional[str] = None, cause: Optional[BaseException] = None):
        
        if isinstance(message, BaseException) and cause is None:
            cause = message
            message = None

        if message is None:
            super().__init__()
        else:
            super().__init__(message)

        self.cause: Optional[BaseException] = cause
        if cause is not None:
            self.__cause__ = cause

    # ------------------------------------------------------------------------


# ============================================================================
