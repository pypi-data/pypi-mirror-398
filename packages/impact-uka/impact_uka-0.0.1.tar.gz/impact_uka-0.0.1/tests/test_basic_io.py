#!/usr/bin/env python
#
# ----------------------------------------------------------------------------

import pytest


# ----------------------------------------------------------------------------

from uka.transport.basic_io import BasicIO


# ----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "value",
    [
        0,
        1,
        -1,
        42,
        -42,
        2**31 - 1,
        -(2**31),
    ],
)


# ----------------------------------------------------------------------------

def test_basic_io_insert_extract_int_roundtrip(value: int) -> None:
    buf = bytearray(4)
    pos = BasicIO.insert(buf, 0, value)
    assert pos == 4
    assert BasicIO.extract_int(buf, 0) == value


# ----------------------------------------------------------------------------

