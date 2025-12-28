from datetime import datetime, timezone, timedelta

from construct import (
    Adapter,
    Bytes,
    Enum,
    Int8ub,
    Int16ub,
)

"""
GB/T 32960.3-2016 chp6.2 table2
GB/T 32960.3-2025 chp6.2 table2
"""
rtm_ver = Enum(Int16ub,
    protocol_2016=0x2323,
    protocol_2025=0x2424,
)

"""
GB/T 32960.3-2016 chp6.2 table2
GB/T 32960.3-2025 chp6.2 table2
"""
enc_algos = Enum(Int8ub,
    uncrypted=0x01,
    rsa=0x02,
    aes=0x03,
    # start of newly defined in 2025 protocol
    sm2=0x04, 
    sm4=0x05,
    # end of newly defined in 2025 protocol
    abnormal=0xfe,
    invalid=0xff,
)

"""
GB/T 32960.3-2016 chp6.3.2 table4
GB/T 32960.3-2025 chp6.3.2 table4
"""
ack_flags = Enum(Int8ub,
    ok=0x01,
    nok=0x02,
    vin_duplicate=0x03,
    vin_unkown=0x04,
    # start of newly defined in 2025 protocol
    signature_invalid=0x05,
    structure_invalid=0x06,
    decryption_failed=0x07,
    # end of newly defined in 2025 protocol
    command=0xfe,
)

"""
GB/T 32960.3-2016 chp6.4 table5
GB/T 32960.3-2025 chp6.4 table5
"""
BEIJING_TZ = timezone(timedelta(hours=8))

class RtmTsAdapter(Adapter):
    def __init__(self):
        super().__init__(Bytes(6))
    
    def _decode(self, msg_ts, context, path):
        ts_obj_bj = datetime(msg_ts[0]+2000, msg_ts[1],msg_ts[2],msg_ts[3],msg_ts[4],msg_ts[5]).replace(tzinfo=BEIJING_TZ)
        ts_obj_local = ts_obj_bj.astimezone()
        return ts_obj_local.replace(tzinfo=None)
    
    def _encode(self, ts_obj_local, context, path):
        ts_obj_bj = ts_obj_local.astimezone(BEIJING_TZ)
        return bytes((ts_obj_bj.year%100, ts_obj_bj.month, ts_obj_bj.day, ts_obj_bj.hour, ts_obj_bj.minute, ts_obj_bj.second))

rtm_ts = RtmTsAdapter()