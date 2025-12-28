from construct import (
    Struct,
    PaddedString,
    Int16ub,
    Enum,
    Int8ub,
    Prefixed,
    Tell,
)

from rtm_con.utilities import HexAdapter
from rtm_con.types_common import rtm_ts
from rtm_con.types_sig import Signature

"""
GB/T 32960.3-2025 anxB.3.5.5 tableB.3
"""
activation_2025 = Struct(
    "_signing_start" / Tell,
    "timestamp" / rtm_ts,
    "sec_chip_id" / PaddedString(16, "ascii"),
    "pubkey" / Prefixed(Int16ub, HexAdapter()),
    "vin" / PaddedString(17, "ascii"),
    "_signing_end" / Tell,
    "sig" / Signature("_signing_start", "_signing_end"),
)


""" 
GB/T 32960.3-2025 anxB.3.5.6 tableB.4
"""
activation_response_2025 = Struct(
    "activation_result" / Enum(Int8ub, ok=1, nok=2),
    "activation_info" / Enum(Int8ub, ok=1, sec_chip_used=2, vin_duplicate=3),
)