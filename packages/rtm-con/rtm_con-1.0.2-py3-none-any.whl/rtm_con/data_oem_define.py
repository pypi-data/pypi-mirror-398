from functools import partial

from construct import Prefixed, Int16ub

from rtm_con.utilities import HexAdapter

"""
GB/T 32960.3-2016 chp7.2.3.8 table19
GB/T 32960.3-2025 chp7.2.4.12 table27
"""
OemDefineData = partial(Prefixed, Int16ub)
oem_define_data_dummy = OemDefineData(HexAdapter())