# About rtm_con
A python implementation for RTM Protocol based on `construct`, supports both `GB/T 32960-2016` and `GB/T 32960-2025`

RTM(Real-Time Monitoring) is a function which defined by China national standard `GB/T 32960`, it has defined a protocol which almost every China-sold NEV(New Energy Vehicle) must follow.

There are two versons of it, one defined at 2016 and the newer one defined at 2025, both of them are supported by `rtm_con`.

As `rtm_con` is built based on [construct](https://github.com/construct/construct), a powerful declarative and symmetrical parser and builder for binary data, it can be used for both parsing and building.

And since it's made by a declarative way, you can also easily customerize your protocol based on it, like define an oem-defined data, or modify a little bit the thing you think not enough for your solution.
## Inistallation
### By PyPI
- If you need only parsing and building feature, run command
```
pip install rtm_con
```
- If you need signature and excel related features, run command
```
pip install rtm_con[full]
```
### By Git repo
After clone the repo to your local, cd the root folder of the project
- If you need only parsing and building feature, run command
```
pip install .
```
- If you need signature and excel related features, run command
```
pip install .[full]
```
See `pyproject.toml` for other options
## Main Features
After `rtm_con` is intalled, check and run the `demo.py` in root folder to see features below:
- Auto identify and handle 2016 and 2025 protocol
- Convert bytes to objected data, or do vice versa
- Convert nested data object to a flat dict, refer to the `flat_msg` part of `demo.py`
- Convert logs to excel table, refer to the `MsgExcel` part of `demo.py`, or try command `rtmlog` after you have `rtm_con` installed
- A GUI for check/modify data content of a single RTM message, and generate/verify signature which introduced in 2025 protocol, try command `rtmgui` after you have `rtm_con` installed
<img width="2408" height="1868" alt="image" src="https://github.com/user-attachments/assets/627a69a7-5379-4d06-97f3-e343b0d0ced4" />

## Build/Parse Example
Refer to `demo.py` for all examples, and read [construct@readthedocs.io](https://construct.readthedocs.io/en/latest/) for more about `construct`
```pycon
>>> import pprint
>>> from rtm_con import msg, con_to_pyobj
>>> b = "242402FE484155563442474E365335303032323139010323190A1C0E2D2F010103010000000261061BE275464B011F199902020103477D0000030D404A0203497D0000030D3B45050102000000000000000006000000000000000003000800020009002500090026000701011BE2754600B40F750F780F760F790F770F760F790F7A0F7A0F7C0F7B0F7C0F7D0F7D0F7D0F7A0F7A0F7A0F7B0F7A0F7B0F7B0F7C0F7D0F7C0F7C0F7E0F7C0F7C0F7A0F7B0F7B0F7D0F7B0F7D0F7D0F7D0F7D0F7D0F7C0F7D0F7C0F7C0F7C0F7D0F790F780F760F7C0F7B0F7C0F7C0F7C0F7C0F7C0F770F7D0F780F7D0F7C0F7C0F7D0F7A0F7F0F7A0F7D0F7C0F7B0F7C0F7C0F7D0F7C0F7C0F7F0F7D0F7D0F7E0F7D0F7D0F7E0F7D0F7E0F7E0F7D0F7D0F7D0F7D0F7D0F7E0F7E0F7B0F7C0F7C0F7C0F7B0F7B0F780F7C0F7D0F7A0F7C0F7C0F7C0F7C0F7C0F7C0F7D0F7A0F7B0F7A0F7A0F7C0F7D0F7C0F7D0F7D0F7C0F7C0F7B0F7D0F790F7C0F7B0F7A0F7C0F7C0F7C0F7B0F7C0F7D0F7B0F7D0F7C0F7C0F7C0F790F7C0F7C0F7B0F7C0F7A0F7D0F7B0F7B0F7C0F7C0F7C0F7D0F7B0F7B0F7A0F7C0F7B0F7C0F7C0F7D0F7C0F7B0F7B0F7C0F7B0F7C0F7C0F7C0F7C0F7B0F7C0F7C0F7D0F7C0F7C0F7C0F7C0F7C0F7C0F7D0F7D0F7D0F7D0F7D0801010030464646454646464645444545464645444646464646464646464746464646464645444646444544434546454545454645820023000004190104230103DD0103F70100010001000100010101000105DB0100FFFFFF0101FF0201005F28A29FC19044A46D51A315D954697BA0E9F09E0AEC8C12F8CB14DDBA8B34339F4F5DFA18631041F0809E94110C41EB69DD8ACFF99461390C1157785E9E3353969A86C4AC1BA92BCF0AA9E347633B1EF9AA448C7601C65DCF62F61FCC3B05CE398C0ECE6D72F30D656F7769DD93C2D9FEE50838BAACEEBD1B983F8CB644E358544570E04C8B637304E38EA5877E387098056C6D648074E3130889DB420311A62072CA57E435610C47F980A8603E984285FE300A27BCF2A7E52F8CB10B2F80BD9D9C4D68280FD7D6642DA7EFB590BEEFD3C3D7E8A72B3BFF8DD619E1229D128B1787C69CC8E3A1922695666C80D9C6A50EFD1A46FE80EDE2D6246EB4F9582F8B0000E7"
>>> msg_obj = msg.fromhex(b)
>>> pydata_obj = con_to_pyobj(msg_obj) # For better present here, msg_obj is a dict-like object with raw objected data
>>> pprint.pp(pydata_obj) # if you handle bytes instead of hex string, use msg.parse(bytes_obj)
{'starter': 'protocol_2025',
 'msg_type': 'realtime',
 'ack': 'command',
 'vin': 'HAUV4BGN6S5002219',
 'enc': 'uncrypted',
 'payload': {'timestamp': datetime.datetime(2025, 10, 28, 14, 45, 47),
             'data_list': [{'data_type': 'whole_vehicle',
                            'data_content': {'vehicle_state': 'on',
                                             'charge_state': 'uncharged',
                                             'operate_state': 'pure_electric',
                                             'vehicle_speed': '0.0 km/h',
                                             'mileage_total': '15591.0 km',
                                             'voltage_total': '713.8000000000001 '
                                                              'V',
                                             'current_total': '2.200000000000273 '
                                                              'A',
                                             'soc': '75 %',
                                             'dcdc_state': 'on',
                                             'gear_state': {'gear_postion_validity': 'valid',
                                                            'driving_force': 0,
                                                            'braking_force': 1,
                                                            'gear': 'P'},
                                             'insulation_resistance': '6553 '
                                                                      'kΩ'}},
                           {'data_type': 'emotor',
                            'data_content': [{'index': 1,
                                              'state': 'off',
                                              'ctrl_temp': '31 ℃',
                                              'speed': '0 rpm',
                                              'torque': '0.0 N·m',
                                              'temp': '34 ℃'},
                                             {'index': 2,
                                              'state': 'off',
                                              'ctrl_temp': '33 ℃',
                                              'speed': '0 rpm',
                                              'torque': '-0.5 N·m',
                                              'temp': '29 ℃'}]},
                           {'data_type': 'gnss',
                            'data_content': {'gnss_state': {'gnss_e_w': 'e',
                                                            'gnss_n_s': 'n',
                                                            'gnss_valid': 1},
                                             'gnss_gcs': 'gcj02',
                                             'gnss_lng': '0.0 °',
                                             'gnss_lat': '0.0 °'}},
                           {'data_type': 'warnings',
                            'data_content': {'max_warning_level': 0,
                                             'general_warnings': {'temp_differentce_warning': 0,
                                                                  'pack_high_temp_warning': 0,
                                                                  'pack_over_volt_warning': 0,
                                                                  'pack_under_volt_warning': 0,
                                                                  'soc_low_warning': 0,
                                                                  'cell_over_volt_warning': 0,
                                                                  'cell_under_volt_warning': 0,
                                                                  'soc_high_warning': 0,
                                                                  'soc_jump_warning': 0,
                                                                  'pack_unmatched_warning': 0,
                                                                  'cell_poor_consistency_warning': 0,
                                                                  'insulation_warning': 0,
                                                                  'dcdc_temp_warning': 0,
                                                                  'brake_system_wanring': 0,
                                                                  'dcdc_state_warning': 0,
                                                                  'emotor_driver_temp_warning': 0,
                                                                  'hv_interlock_warning': 0,
                                                                  'emotor_temp_warning': 0,
                                                                  'pack_over_charged_warning': 0,
                                                                  'emotor_over_speed_warning': 0,
                                                                  'emotor_over_curr_warning': 0,
                                                                  'super_capacitor_over_temp_warning': 0,
                                                                  'super_capacitor_over_pressure_warning': 0,
                                                                  'pack_thermal_event_warning': 0,
                                                                  'hydrogen_leakage_warning': 0,
                                                                  'hydrogen_system_presure_abnormal_warning': 0,
                                                                  'hydrogen_system_temp_abnormal_warning': 0,
                                                                  'fuel_cell_stack_over_temp_warning': 0},
                                             'pack_failures': [],
                                             'emotor_failures': [],
                                             'engine_failures': [],
                                             'other_failures': ['00080002',
                                                                '00090025',
                                                                '00090026'],
                                             'general_warning_list': []}},
                           {'data_type': 'cell_volts',
                            'data_content': [{'index': '1',
                                              'volt': '713.8000000000001 V',
                                              'curr': '2.200000000000273 V',
                                              'cell_volts': ['3.9570000000000003 '
                                                             'V',
                                                             '3.96 V',
                                                             '3.958 V',
                                                             '3.9610000000000003 '
                                                             'V',
                                                             '3.959 V',
                                                             '3.958 V',
                                                             '3.9610000000000003 '
                                                             'V',
                                                             '3.962 V',
                                                             '3.962 V',
                                                             '3.964 V',
                                                             '3.963 V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.962 V',
                                                             '3.962 V',
                                                             '3.962 V',
                                                             '3.963 V',
                                                             '3.962 V',
                                                             '3.963 V',
                                                             '3.963 V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.966 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.962 V',
                                                             '3.963 V',
                                                             '3.963 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.963 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9610000000000003 '
                                                             'V',
                                                             '3.96 V',
                                                             '3.958 V',
                                                             '3.964 V',
                                                             '3.963 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.959 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.96 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.962 V',
                                                             '3.967 V',
                                                             '3.962 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.964 V',
                                                             '3.963 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.967 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.966 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.966 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.966 V',
                                                             '3.966 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.966 V',
                                                             '3.966 V',
                                                             '3.963 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.963 V',
                                                             '3.963 V',
                                                             '3.96 V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.962 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.962 V',
                                                             '3.963 V',
                                                             '3.962 V',
                                                             '3.962 V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.963 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9610000000000003 '
                                                             'V',
                                                             '3.964 V',
                                                             '3.963 V',
                                                             '3.962 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.963 V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.963 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.9610000000000003 '
                                                             'V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.963 V',
                                                             '3.964 V',
                                                             '3.962 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.963 V',
                                                             '3.963 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.963 V',
                                                             '3.963 V',
                                                             '3.962 V',
                                                             '3.964 V',
                                                             '3.963 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.964 V',
                                                             '3.963 V',
                                                             '3.963 V',
                                                             '3.964 V',
                                                             '3.963 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.963 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.964 V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V',
                                                             '3.9650000000000003 '
                                                             'V']}]},
                           {'data_type': 'probe_temps',
                            'data_content': [{'index': '1',
                                              'probe_temps': ['30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '29 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '29 ℃',
                                                              '28 ℃',
                                                              '29 ℃',
                                                              '29 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '29 ℃',
                                                              '28 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '31 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '29 ℃',
                                                              '28 ℃',
                                                              '30 ℃',
                                                              '30 ℃',
                                                              '28 ℃',
                                                              '29 ℃',
                                                              '28 ℃',
                                                              '27 ℃',
                                                              '29 ℃',
                                                              '30 ℃',
                                                              '29 ℃',
                                                              '29 ℃',
                                                              '29 ℃',
                                                              '29 ℃',
                                                              '30 ℃',
                                                              '29 ℃']}]},
                           {'data_type': 130,
                            'data_content': '000004190104230103dd0103f70100010001000100010101000105db0100ffffff0101'}],
             'sig_starter': 'ff',
             'sig': {'algo': 'rsa',
                     'r_value': '5f28a29fc19044a46d51a315d954697ba0e9f09e0aec8c12f8cb14ddba8b34339f4f5dfa18631041f0809e94110c41eb69dd8acff99461390c1157785e9e3353969a86c4ac1ba92bcf0aa9e347633b1ef9aa448c7601c65dcf62f61fcc3b05ce398c0ece6d72f30d656f7769dd93c2d9fee50838baaceebd1b983f8cb644e358544570e04c8b637304e38ea5877e387098056c6d648074e3130889db420311a62072ca57e435610c47f980a8603e984285fe300a27bcf2a7e52f8cb10b2f80bd9d9c4d68280fd7d6642da7efb590beefd3c3d7e8a72b3bff8dd619e1229d128b1787c69cc8e3a1922695666c80d9c6a50efd1a46fe80ede2d6246eb4f9582f8b',
                     's_value': ''}},
 'checksum': 231}
>>> msg.tohex(pydata_obj) # Same for msg.tohex(msg_obj), if you need bytes instead of hex string, use msg.build(pydata_obj) or msg.build(msg_obj)
'242402fe484155563442474e365335303032323139010323190a1c0e2d2f010103010000000261061be275464b011f199902020103477d0000030d404a0203497d0000030d3b45050102000000000000000006000000000000000003000800020009002500090026000701011be2754600b40f750f780f760f790f770f760f790f7a0f7a0f7c0f7b0f7c0f7d0f7d0f7d0f7a0f7a0f7a0f7b0f7a0f7b0f7b0f7c0f7d0f7c0f7c0f7e0f7c0f7c0f7a0f7b0f7b0f7d0f7b0f7d0f7d0f7d0f7d0f7d0f7c0f7d0f7c0f7c0f7c0f7d0f790f780f760f7c0f7b0f7c0f7c0f7c0f7c0f7c0f770f7d0f780f7d0f7c0f7c0f7d0f7a0f7f0f7a0f7d0f7c0f7b0f7c0f7c0f7d0f7c0f7c0f7f0f7d0f7d0f7e0f7d0f7d0f7e0f7d0f7e0f7e0f7d0f7d0f7d0f7d0f7d0f7e0f7e0f7b0f7c0f7c0f7c0f7b0f7b0f780f7c0f7d0f7a0f7c0f7c0f7c0f7c0f7c0f7c0f7d0f7a0f7b0f7a0f7a0f7c0f7d0f7c0f7d0f7d0f7c0f7c0f7b0f7d0f790f7c0f7b0f7a0f7c0f7c0f7c0f7b0f7c0f7d0f7b0f7d0f7c0f7c0f7c0f790f7c0f7c0f7b0f7c0f7a0f7d0f7b0f7b0f7c0f7c0f7c0f7d0f7b0f7b0f7a0f7c0f7b0f7c0f7c0f7d0f7c0f7b0f7b0f7c0f7b0f7c0f7c0f7c0f7c0f7b0f7c0f7c0f7d0f7c0f7c0f7c0f7c0f7c0f7c0f7d0f7d0f7d0f7d0f7d0801010030464646454646464645444545464645444646464646464646464746464646464645444646444544434546454545454645820023000004190104230103dd0103f70100010001000100010101000105db0100ffffff0101ff0201005f28a29fc19044a46d51a315d954697ba0e9f09e0aec8c12f8cb14ddba8b34339f4f5dfa18631041f0809e94110c41eb69dd8acff99461390c1157785e9e3353969a86c4ac1ba92bcf0aa9e347633b1ef9aa448c7601c65dcf62f61fcc3b05ce398c0ece6d72f30d656f7769dd93c2d9fee50838baaceebd1b983f8cb644e358544570e04c8b637304e38ea5877e387098056c6d648074e3130889db420311a62072ca57e435610c47f980a8603e984285fe300a27bcf2a7e52f8cb10b2f80bd9d9c4d68280fd7d6642da7efb590beefd3c3d7e8a72b3bff8dd619e1229d128b1787c69cc8e3a1922695666c80d9c6a50efd1a46fe80ede2d6246eb4f9582f8b0000e7'
```
