from construct import (
    Int16ub,
    Int8ub,
    PaddedString,
    Prefixed,
    Tell,
    Switch,
)

from rtm_con.types_checksum import RtmChecksum
from rtm_con.types_common import enc_algos, rtm_ver, ack_flags
from rtm_con.types_msg import payload_mapping, msg_types
from rtm_con.types_struct_ext import StructExt
from rtm_con.utilities import GoThoughDict

"""
GB/T 32960.3-2016 chp6.2 table2
GB/T 32960.3-2025 chp6.2 table2
"""
msg = StructExt( # Only parse the message without verifying the checksum
    "starter" / rtm_ver, 
    "msg_type" / msg_types,
    "ack" / ack_flags,
    "vin" / PaddedString(17, "ascii"),
    "enc" / enc_algos,
    "payload" / Prefixed(Int16ub, Switch(payload_mapping, GoThoughDict())),
    "checksum" / Int8ub,
)

msg_checked = StructExt( # Calculate and verify automatically the checksum
    "starter" / rtm_ver, 
    "_checking_start" / Tell,
    "msg_type" / msg_types,
    "ack" / ack_flags,
    "vin" / PaddedString(17, "ascii"),
    "enc" / enc_algos,
    "payload" / Prefixed(Int16ub, Switch(payload_mapping, GoThoughDict())),
    "_checking_end" / Tell,
    "checksum" / RtmChecksum("_checking_start", "_checking_end"),
)