from construct import (
    BitsSwapped,
    ByteSwapped,
    BitStruct,
    Flag,
    Padding,
    Struct,
    Int8ub,
    PrefixedArray,
    Enum,
)

from rtm_con.utilities import HexAdapter

"""
GB/T 32960.3-2016 chp7.2.3.7 table18
"""
general_warnings_2016 = {
    0: "temp_differentce_warning",
    1: "pack_high_temp_warning",
    2: "pack_over_volt_warning",
    3: "pack_under_volt_warning",
    4: "soc_low_warning",
    5: "cell_over_volt_warning",
    6: "cell_under_volt_warning",
    7: "soc_high_warning",
    8: "soc_jump_warning",
    9: "pack_unmatched_warning",
    10: "cell_poor_consistency_warning",
    11: "insulation_warning",
    12: "dcdc_temp_warning",
    13: "brake_system_wanring",
    14: "dcdc_state_warning",
    15: "emotor_driver_temp_warning",
    16: "hv_interlock_warning",
    17: "emotor_temp_warning",
    18: "pack_over_charged_warning",
}

general_warning_flags_2016 = BitsSwapped(ByteSwapped(BitStruct(
    *(name/Flag for index, name in sorted(general_warnings_2016.items())),
    "_reserved" / Padding(32-len(general_warnings_2016)),
)))

"""
GB/T 32960.3-2016 chp7.2.3.7 table17
"""
warnings_data_2016 = Struct(
    "max_warning_level" / Int8ub,
    "general_warnings" / general_warning_flags_2016,
    "pack_failures" / PrefixedArray(Int8ub, HexAdapter(4)),
    "emotor_failures" / PrefixedArray(Int8ub, HexAdapter(4)),
    "engine_failures" / PrefixedArray(Int8ub, HexAdapter(4)),
    "other_failures" / PrefixedArray(Int8ub, HexAdapter(4)),
)

"""
GB/T 32960.3-2025 chp7.2.4.9 table24
"""
general_warnings_2025 = general_warnings_2016 | {
    19: "emotor_over_speed_warning",
    20: "emotor_over_curr_warning",
    21: "super_capacitor_over_temp_warning",
    22: "super_capacitor_over_pressure_warning",
    23: "pack_thermal_event_warning",
    24: "hydrogen_leakage_warning",
    25: "hydrogen_system_presure_abnormal_warning",
    26: "hydrogen_system_temp_abnormal_warning",
    27: "fuel_cell_stack_over_temp_warning",
}

general_warning_flags_2025 = BitsSwapped(ByteSwapped(BitStruct(
    *(name/Flag for index, name in sorted(general_warnings_2025.items())),
    "_reserved" / Padding(32-len(general_warnings_2025)),
)))

"""
GB/T 32960.3-2025 chp7.2.4.9 table23
"""
warnings_data_2025 = Struct(
    "max_warning_level" / Int8ub,
    "general_warnings" / general_warning_flags_2025,
    "pack_failures" / PrefixedArray(Int8ub, HexAdapter(4)),
    "emotor_failures" / PrefixedArray(Int8ub, HexAdapter(4)),
    "engine_failures" / PrefixedArray(Int8ub, HexAdapter(4)),
    "other_failures" / PrefixedArray(Int8ub, HexAdapter(4)),
    "general_warning_list" / PrefixedArray(Int8ub,
        Struct(
            "warning" / Enum(Int8ub, **{name: index for index, name in general_warnings_2025.items()}),
            "level" / Int8ub,
        ),
    ),
)