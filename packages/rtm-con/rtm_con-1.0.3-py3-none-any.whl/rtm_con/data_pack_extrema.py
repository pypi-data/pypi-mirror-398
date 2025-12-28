from construct import Struct, Int8ub, Int16ub

from rtm_con.types_dataitem import DataItemAdapter

"""
GB/T 32960.3-2016 chp7.2.3.6 table16
"""
pack_extrema_data_2016 = Struct(
    "max_volt_pack_index" / DataItemAdapter(Int8ub, ""),
    "max_volt_cell_index" / DataItemAdapter(Int8ub, ""),
    "max_cell_volt" / DataItemAdapter(Int16ub, "V", 0.001),
    "min_volt_pack_index" / DataItemAdapter(Int8ub, ""),
    "min_volt_cell_index" / DataItemAdapter(Int8ub, ""),
    "min_cell_volt" / DataItemAdapter(Int16ub, "V", 0.001),
    "max_temp_pack_index" / DataItemAdapter(Int8ub, ""),
    "max_temp_cell_index" / DataItemAdapter(Int8ub, ""),
    "max_cell_temp" / DataItemAdapter(Int8ub, "℃", 1, -40),
    "min_temp_pack_index" / DataItemAdapter(Int8ub, ""),
    "min_temp_cell_index" / DataItemAdapter(Int8ub, ""),
    "min_cell_temp" / DataItemAdapter(Int8ub, "℃", 1, -40),
)

# This data item has been deleted in 2025 protocol