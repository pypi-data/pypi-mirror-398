#!/usr/bin/env python
#
# ----------------------------------------------------------------------------

import pytest


# ----------------------------------------------------------------------------

from uka.transport.marshal_stream import MarshalStream
from uka.transport.unmarshal_stream import UnmarshalStream
from uka.transport.value_io import ValueIO


# ----------------------------------------------------------------------------

def test_value_io_matrix_roundtrip() -> None:
    matrix = [
        [1.0, 2.0],
        [3.5, -4.25],
    ]

    ms = MarshalStream()
    ValueIO.write_value(ms, matrix)

    us = UnmarshalStream(ms.get_buffer())
    decoded = ValueIO.read_value_array_array_double(us)

    # assert decoded == pytest.approx(matrix)

    decoded_flat = [x for row in decoded for x in row]
    expected_flat = [x for row in matrix for x in row]
    assert decoded_flat == pytest.approx(expected_flat)


# ----------------------------------------------------------------------------

def test_value_io_ragged_matrix_raises() -> None:
    ragged = [
        [1.0, 2.0],
        [3.0],
    ]

    ms = MarshalStream()
    with pytest.raises(ValueError):
        ValueIO.write_value(ms, ragged)


# ----------------------------------------------------------------------------
