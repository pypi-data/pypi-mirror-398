from construct import Struct, Int8ub, PrefixedArray, Int16ub

from rtm_con.types_dataitem import DataItemAdapter

"""
GB/T 32960.3-2016 anxB.3.5.3.9 tableB.8
"""
pack_item_2016 = Struct(
    "index" / DataItemAdapter(Int8ub, ""),
    "probe_temps" / PrefixedArray(Int16ub, DataItemAdapter(Int8ub, "℃", 1, -40)),
)

"""
GB/T 32960.3-2016 anxB.3.5.3.9 tableB.7
"""
probe_temps_data_2016 = PrefixedArray(Int8ub, pack_item_2016)

"""
GB/T 32960.3-2025 chp7.2.4.3 table14
"""
pack_item_2025 = Struct(
    "index" / DataItemAdapter(Int8ub, ""),
    "probe_temps" / PrefixedArray(Int16ub, DataItemAdapter(Int8ub, "℃", 1, -40)),
)

"""
GB/T 32960.3-2025 chp7.2.4.3 table13
"""
probe_temps_data_2025 = PrefixedArray(Int8ub, pack_item_2025)