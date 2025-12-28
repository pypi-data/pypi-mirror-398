from construct import Struct, this, Int16ub

from rtm_con.utilities import HexAdapter
from rtm_con.types_common import enc_algos, rtm_ts

"""
GB/T 32960.3-2025 chp7.6 table31
"""
payload_key_sync_2025 = Struct(
    "payload_enc" / enc_algos,
    "payload_key_len" / Int16ub,
    "payload_key" / HexAdapter(this.payload_key_len),
    "key_starttime" / rtm_ts,
    "key_endtime" / rtm_ts,
)