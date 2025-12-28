from construct import BitStruct, Padding, BitsInteger, Enum, Flag, Struct, Int32ub, Int8ub

from rtm_con.types_dataitem import DataItemAdapter

"""
GB/T 32960.3-2016 chp7.2.3.5 table15
GB/T 32960.3-2025 chp7.2.4.8 table22
"""
gnss_states = BitStruct(
    "_reserved" / Padding(5),
    "gnss_e_w" /Enum(BitsInteger(1), e=0, w=1),
    "gnss_n_s" / Enum(BitsInteger(1), n=0, s=1),
    "gnss_valid" / Flag,
)

"""
GB/T 32960.3-2016 chp7.2.3.5 table14, table15
"""
gnss_data_2016 = Struct(
    "gnss_state" / gnss_states,
    "gnss_lng" / DataItemAdapter(Int32ub, "°", 0.000001),
    "gnss_lat" / DataItemAdapter(Int32ub, "°", 0.000001),
)

"""
GB/T 32960.3-2025 chp7.2.4.8 table21, table22
"""
gnss_data_2025 = Struct(
    "gnss_state" / gnss_states,
    "gnss_gcs" / Enum(Int8ub, wgs84=1, gcj02=2, other=3),
    "gnss_lng" / DataItemAdapter(Int32ub, "°", 0.000001),
    "gnss_lat" / DataItemAdapter(Int32ub, "°", 0.000001),
)
