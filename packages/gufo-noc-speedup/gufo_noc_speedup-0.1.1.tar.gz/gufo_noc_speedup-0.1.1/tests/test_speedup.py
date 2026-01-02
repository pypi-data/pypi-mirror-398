# ---------------------------------------------------------------------
# Speedup tests
# ---------------------------------------------------------------------
# NOC Copyright (C) 2022-25, Gufo Labs
# See LICENSE.md for details
# ---------------------------------------------------------------------

# Third-party modules
import pytest

# Gufo Labs modules
from gufo.noc.speedup import encode_oid, parse_p_oid


@pytest.mark.parametrize(
    ("oid", "expected"),
    [(b"1.3.6.1.2.1.1.5.0", b"\x06\x08+\x06\x01\x02\x01\x01\x05\x00")],
)
def test_encode_oid(oid: bytes, expected: bytes) -> None:
    assert encode_oid(oid) == expected


@pytest.mark.parametrize(
    ("msg", "expected"),
    [(b"+\x06\x01\x02\x01\x01\x05\x00", b"1.3.6.1.2.1.1.5.0")],
)
def test_parse_p_oid(msg: bytes, expected: bytes) -> None:
    assert parse_p_oid(msg) == expected
