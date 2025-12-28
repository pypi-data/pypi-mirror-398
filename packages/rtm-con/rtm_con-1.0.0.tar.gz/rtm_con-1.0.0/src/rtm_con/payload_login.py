from construct import (
    Struct,
    Int16ub,
    PaddedString,
    Int8ub,
    Array,
    this,
)

from rtm_con.types_common import rtm_ts, enc_algos

"""
GB/T 32960.3-2016 chp7.1 table6
"""
login_2016 = Struct(
    "timestamp" / rtm_ts,
    "session_id" / Int16ub,
    "iccid" / PaddedString(20, "ascii"),
    "bms_total" / Int8ub,
    "pack_sn_len" / Int8ub,
    "pack_sn" / Array(
        this.bms_total,
        PaddedString(this.pack_sn_len, "ascii")
    ),
)

"""
GB/T 32960.3-2025 chp7.1 table6
"""
login_2025 = Struct(
    "timestamp" / rtm_ts,
    "session_id" / Int16ub,
    "iccid" / PaddedString(20, "ascii"),
    "bms_total" / Int8ub,
    "pack_per_bms" / Int8ub[this.bms_total],
    "pack_sn_list" / Array(
        this.bms_total,
        Array(
            lambda this: this.pack_per_bms[this._index],
            PaddedString(24, "ascii"),
        )
    ),
)

"""
GB/T 32960.3-2016 chp7.4 table21
GB/T 32960.3-2025 chp7.4 table29
"""
plt_login_2016 = plt_login_2025 = Struct(
    "timestamp" / rtm_ts,
    "session_id" / Int16ub,
    "username" / PaddedString(12, "ascii"),
    "password" / PaddedString(20, "ascii"),
    "enc" / enc_algos,
)