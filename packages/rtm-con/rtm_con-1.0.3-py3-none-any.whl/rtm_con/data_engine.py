from construct import Struct, Enum, Int8ub, Int16ub

from rtm_con.types_dataitem import DataItemAdapter

"""
GB/T 32960.3-2016 chp7.2.3.4 table13
"""
engine_data_2016 = Struct(
    "engine_state" / Enum(Int8ub, on=0x01, off=0x02, abnormal=0xfe, invalid=0xff),
    "engine_torque" / DataItemAdapter(Int16ub, "rpm"),
    "fuel_consumption" / DataItemAdapter(Int16ub, "L/100km", 0.01),
)

"""
GB/T 32960.3-2025 chp7.2.4.7 table20
"""
engine_data_2025 = Struct(
    "engine_torque" / DataItemAdapter(Int16ub, "rpm"),
)