# ---------------------------------------------------------------------
# Gufo NOC Speedup: NOC Speedup Library
# ---------------------------------------------------------------------
# Copyright (C) 2023-25, Gufo Labs
# See LICENSE.md for details
# ---------------------------------------------------------------------

"""NOC Speedup Library.

Attributes:
    __version__: Current version
"""

# Gufo Labs modules
from ._fast import encode_int, encode_oid, parse_p_oid, parse_tlv_header

__version__: str = "0.1.1"
__all__ = ["encode_int", "encode_oid", "parse_p_oid", "parse_tlv_header"]
