from construct import (
    Struct,
    Enum,
    Int8ub,
    Int16ub,
    Int32ub,
    LazyBound,
    BitStruct,
    Padding,
    Flag,
    BitsInteger,
)

from rtm_con.types_dataitem import DataItemAdapter

"""
GB/T 32960.3-2016 chp7.2.3.1 table9
GB/T 32960.3-2016 anxB.3.5.3.1 tableB.4
"""
whole_vehicle_data_2016 = Struct(
    "vehicle_state" / Enum(Int8ub, on=0x01, off=0x02, other=0x03, abnormal=0xfe, invalid=0xff),
    "charge_state" / Enum(Int8ub, parking_charging=0x01, driving_charging=0x02, uncharged=0x03, completed_charging=0x04, abnormal=0xfe, invalid=0xff),
    "operate_state" / Enum(Int8ub, pure_electric=0x01, hybrid=0x02, fuel=0x03, abnormal=0xfe, invalid=0xff),
    "vehicle_speed" / DataItemAdapter(Int16ub, "km/h", 0.1),
    "mileage_total" / DataItemAdapter(Int32ub, "km", 0.1),
    "voltage_total" / DataItemAdapter(Int16ub, "V", 0.1),
    "current_total" / DataItemAdapter(Int16ub, "A", 0.1, -1000),
    "soc" / DataItemAdapter(Int8ub, "%"),
    "dcdc_state" / Enum(Int8ub, on=0x01, off=0x02, abnormal=0xfe, invalid=0xff),
    "gear_state" / LazyBound(lambda: gear_state_2016),
    # No abnormal/invalid defined here anyway
    "insulation_resistance" / DataItemAdapter(Int16ub, "kΩ", validation=False),
    "accelerator_padel" / DataItemAdapter(Int8ub, "%"),
    # This one is special, which one may be a boolean(off=0/on=101) or int(0~100%), but I see no necessarity to handle the boolean.
    "brake_padel" / DataItemAdapter(Int8ub, "%"),
)

"""
GB/T 32960.3-2016 anxA.1 tableA.1
"""
gear_state_2016 = BitStruct(
    "_reserved" / Padding(2),
    "driving_force" / Flag,
    "braking_force" / Flag,
    "gear" / Enum(BitsInteger(4), N=0,
        gp1=1, gp2=2, gp3=3, gp4=4,
        gp5=5, gp6=6, gp7=7, gp8=8,
        gp9=9, gp10=10, gp11=11, gp12=12,
        R=13, D=14, P=15
    )
)

"""
GB/T 32960.3-2025 chp7.2.4.1 table10
"""
whole_vehicle_data_2025 = Struct(
    "vehicle_state" / Enum(Int8ub, on=0x01, off=0x02, other=0x03, abnormal=0xfe, invalid=0xff),
    "charge_state" / Enum(Int8ub, parking_charging=0x01, driving_charging=0x02, uncharged=0x03, completed_charging=0x04, abnormal=0xfe, invalid=0xff),
    "operate_state" / Enum(Int8ub, pure_electric=0x01, hybrid=0x02, fuel=0x03, abnormal=0xfe, invalid=0xff),
    "vehicle_speed" / DataItemAdapter(Int16ub, "km/h", 0.1),
    "mileage_total" / DataItemAdapter(Int32ub, "km", 0.1),
    "voltage_total" / DataItemAdapter(Int16ub, "V", 0.1),
    "current_total" / DataItemAdapter(Int16ub, "A", 0.1, -3000), # different with 2016 protocol
    "soc" / DataItemAdapter(Int8ub, "%"),
    "dcdc_state" / Enum(Int8ub, on=0x01, off=0x02, abnormal=0xfe, invalid=0xff),
    "gear_state" / LazyBound(lambda: gear_state_2025),
    "insulation_resistance" / DataItemAdapter(Int16ub, "kΩ"), # 2025 protocol has defined abnormal/invalid
)

"""
GB/T 32960.3-2025 anxA.1 tableA.1
"""
gear_state_2025 = BitStruct(
    "gear_postion_validity" / Enum(BitsInteger(1), valid=0,invalid=1),
    "_reserved" / Padding(1),
    "driving_force" / Flag,
    "braking_force" / Flag,
    "gear" / Enum(BitsInteger(4), N=0,
        gp1=1, gp2=2, gp3=3, gp4=4,
        gp5=5, gp6=6, gp7=7, gp8=8,
        gp9=9, gp10=10, gp11=11, gp12=12,
        R=13, D=14, P=15
    )
)