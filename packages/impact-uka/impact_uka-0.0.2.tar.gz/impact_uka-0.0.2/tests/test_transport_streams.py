#!/usr/bin/env python
#
# ----------------------------------------------------------------------------

import pytest


# ----------------------------------------------------------------------------

from uka.transport.marshal_stream import MarshalStream
from uka.transport.unmarshal_stream import UnmarshalStream


# ----------------------------------------------------------------------------

def test_marshal_unmarshal_int_roundtrip() -> None:
    ms = MarshalStream()
    ms.write_int(123)
    ms.write_int(-456)

    us = UnmarshalStream(ms.get_buffer())
    assert us.read_int() == 123
    assert us.read_int() == -456

# ----------------------------------------------------------------------------

def test_marshal_unmarshal_double_roundtrip() -> None:
    ms = MarshalStream()
    ms.write_double(1.25)
    ms.write_double(-0.5)

    us = UnmarshalStream(ms.get_buffer())
    assert us.read_double() == pytest.approx(1.25)
    assert us.read_double() == pytest.approx(-0.5)

# ----------------------------------------------------------------------------

def test_unmarshal_request_raises_eoferror() -> None:
    us = UnmarshalStream(b"\x00\x01")
    with pytest.raises(EOFError):
        us.request(4)

# ----------------------------------------------------------------------------
