#!/usr/bin/env python
#
# ----------------------------------------------------------------------------

import pytest
# ----------------------------------------------------------------------------

from uka.transport.deep_clone import DeepClone


# ----------------------------------------------------------------------------

def test_deep_clone_add_makes_independent_copy() -> None:
    dc = DeepClone()

    original = [[1.0, 2.0], [3.0, 4.0]]
    dc.add(1, original)

    original[0][0] = 999.0

    cloned = dc.get(1)
    assert cloned[0][0] == 1.0


# ----------------------------------------------------------------------------
