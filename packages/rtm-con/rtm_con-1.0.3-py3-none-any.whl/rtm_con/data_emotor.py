from construct import (
    PrefixedArray,
    LazyBound,
    Struct,
    Enum,
    Int8ub,
    Int16ub,
    Int32ub,
)

from rtm_con.types_dataitem import DataItemAdapter

"""
GB/T 32960.3-2016 chp7.2.3.2 table10
"""
emotor_data_2016 = PrefixedArray(Int8ub, LazyBound(lambda: emotor_item_2016))

"""
GB/T 32960.3-2016 chp7.2.3.2 table11
"""
emotor_item_2016 = Struct(
    "index" / Int8ub,
    "state" / Enum(Int8ub, consuming_power=0x01, generating_power=0x02, off=0x03, idle=0x04, abnormal=0xfe, invalid=0xff),
    "ctrl_temp" / DataItemAdapter(Int8ub, "℃", 1, -40),
    # For some strange reason, the offset for speed and torque are marked without unit in GB/T 32960.3-2016
    # Which means, the offset is added before factor, this is different with any other date item
    "speed" / DataItemAdapter(Int16ub, "rpm", 1, -20000), # Not affected
    "torque" / DataItemAdapter(Int16ub, "N·m", 0.1, -2000), # Raw offset 20000 * factor 0.1
    "temp" / DataItemAdapter(Int8ub, "℃", 1, -40),
    "ctrl_volt" / DataItemAdapter(Int16ub, "V", 0.1),
    "ctrl_curr" / DataItemAdapter(Int16ub, "A", 0.1, -1000),
)

"""
GB/T 32960.3-2025 chp7.2.4.4 table15
"""
emotor_data_2025 = "emotors" / PrefixedArray(Int8ub, LazyBound(lambda: emotor_item_2025))

"""
GB/T 32960.3-2025 chp7.2.4.4 table16
"""
emotor_item_2025 = Struct(
    "index" / Int8ub,
    "state" / Enum(Int8ub, consuming_power=0x01, generating_power=0x02, off=0x03, idle=0x04, abnormal=0xfe, invalid=0xff),
    "ctrl_temp" / DataItemAdapter(Int8ub, "℃", 1, -40),
    "speed" / DataItemAdapter(Int16ub, "rpm", 1, -32000),
    "torque" / DataItemAdapter(Int32ub, "N·m", 0.1, -20000),
    "temp" / DataItemAdapter(Int8ub, "℃", 1, -40),
)