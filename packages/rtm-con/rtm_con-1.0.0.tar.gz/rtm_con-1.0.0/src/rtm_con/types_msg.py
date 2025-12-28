from construct import (
    Enum,
    Int8ub,
    GreedyBytes,
    Struct,
)

from rtm_con.payload_login import login_2016, plt_login_2016, login_2025, plt_login_2025
from rtm_con.payload_logout import logout_2016, plt_logout_2016, logout_2025, plt_logout_2025
from rtm_con.payload_data import data_2016, data_2025
from rtm_con.payload_activation import activation_2025, activation_response_2025
from rtm_con.payload_payload_key_sync import payload_key_sync_2025
from rtm_con.types_common import ack_flags, rtm_ts, rtm_ver

"""
GB/T 32960.3-2016 chp6.3.1 table3
GB/T 32960.3-2016 anxB.3.3.1 tableB.2
GB/T 32960.3-2025 chp6.3.1 table3
GB/T 32960.3-2025 anxB.3.3.1 tableB.2
"""
msg_types = Enum(Int8ub, 
    login=0x01,
    realtime=0x02,
    supplimentary=0x03,
    logout=0x04,
    plt_login=0x05,
    plt_logout=0x06,
    heartbeat=0x07,
    time_sync=0x08,
    # start of newly defined in 2025 protocol
    activation=0x09,
    activation_response=0x0a,
    payload_key_sync=0x0b,
    # end of newly defined in 2025 protocol
    get=0x80,
    set=0x81,
    control=0x82,
    # GB/T 32960.3-2016 chp6.3.1 table3
        # 0x09~0x7f uplink reserve
        # 0x83~0xbf downlink reserve
        # 0xc0~0xfe platform reserve
    # GB/T 32960.3-2025 chp6.3.1 table3
        # 0x0c~0x7f uplink reserve
        # 0x80~0x82 client reserve
        # 0x83~0xbf downlink reserve
        # 0xc0~0xfe platform reserve
)

"""
GB/T 32960.3-2016 chp6.3.1 table3
"""
MSG_TYPE_MAPPING_2016 = {
    msg_types.login: login_2016,
    msg_types.realtime: data_2016,
    msg_types.supplimentary: data_2016,
    msg_types.logout: logout_2016,
    msg_types.plt_login: plt_login_2016,
    msg_types.plt_logout: plt_logout_2016,
}

"""
GB/T 32960.3-2025 chp6.3.1 table3
"""
MSG_TYPE_MAPPING_2025 = {
    msg_types.login: login_2025,
    msg_types.realtime: data_2025,
    msg_types.supplimentary: data_2025,
    msg_types.logout: logout_2025,
    msg_types.plt_login: plt_login_2025,
    msg_types.plt_logout: plt_logout_2025,
    msg_types.activation: activation_2025,
    msg_types.activation_response: activation_response_2025,
    msg_types.payload_key_sync: payload_key_sync_2025,
}

def payload_mapping(ths):
    if ths.ack==ack_flags.command:
        if ths.starter==rtm_ver.protocol_2016 and ths.msg_type in MSG_TYPE_MAPPING_2016:
            # For 2016 protocol known message types
            return MSG_TYPE_MAPPING_2016[ths.msg_type]
        elif ths.starter==rtm_ver.protocol_2025 and ths.msg_type in MSG_TYPE_MAPPING_2025:
            # For 2025 protocol known message types
            return MSG_TYPE_MAPPING_2025[ths.msg_type]
        else:
            # For unkown message types
            return GreedyBytes
    else:
        # Normally the ack message contains only timestamp
        return Struct("timestamp"/rtm_ts)