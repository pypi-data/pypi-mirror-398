from construct import Container, ListContainer

from rtm_con.types_data import data_types_2016, data_types_2025

class flat_msg(dict):
    def __init__(self, msg_obj):
        super().__init__()
        self.pathdict = {}
        for k_m, v_m in msg_obj.items():
            path = (f"{k_m}",)
            if k_m=="payload":
                if isinstance(v_m, Container):
                    # If payload is parsed, disassemble payload
                    for k_p, v_p in v_m.items():
                        payload_item_path = path + (k_p,)
                        if k_p=="data_list":
                            # Data blocks
                            self._flatten_data_list(v_p, payload_item_path)
                        elif isinstance(v_p, Container):
                            # For signature or other nested Containers
                            for k_s, v_s in v_p.items():
                                nested_path = payload_item_path + (k_s,)
                                self._checkout(k_s, v_s, path=nested_path, prefix=f"{k_p}-")
                        elif isinstance(v_p, ListContainer):
                            # For battery SNs
                            if v_p and all(isinstance(i, ListContainer) for i in v_p):
                                output = [list(item) for item in v_p]
                            else:
                                output = list(v_p)
                            self._checkout(k_p, output, path=payload_item_path)
                        else:
                            # Nromal items like timestamp
                            self._checkout(k_p, v_p, path=payload_item_path)
                else:
                    # For unkown payload
                    self._checkout(k_m, v_m, path=path)
            else:
                self._checkout(k_m, v_m, path=path)

    def _flatten_data_list(self, data_blocks, data_path):
        # Firstly check if there is dupilicated ones
        duplication_indexs = self._check_data_duplication(data_blocks)
        for block_index, data_block in enumerate(data_blocks):
            # Theoretically, we should have "date_content" here, but add data_block.data_type give more info
            data_block_path = data_path + (block_index, f"date_content-{data_block.data_type}")
            
            if d_index:=duplication_indexs[block_index]:
                duplication_prefix = f"(+{duplication_indexs[block_index]})"
            else:
                duplication_prefix = ""
            
            match data_block.data_type:
                case data_types_2016.emotor | data_types_2025.emotor:
                    self._flatten_emotor_block(data_block, duplication_prefix, data_block_path)
                case data_types_2016.warnings | data_types_2025.warnings:
                    self._flatten_warnings_block(data_block, duplication_prefix, data_block_path)
                case data_types_2016.cell_volts | data_types_2025.cell_volts:
                    self._flatten_cell_volts_block(data_block, duplication_prefix, data_block_path)
                case data_types_2016.probe_temps | data_types_2025.probe_temps:
                    self._flatten_probe_temps_block(data_block, duplication_prefix, data_block_path)
                case _:
                    if isinstance(data_block.data_content, Container):
                        # For a "normal" data block, which contains a lots of data items
                        for d_name, d_value in data_block.data_content.items():
                            data_item_path = data_block_path + (d_name,)
                            if isinstance(d_value, Container):
                                # For gear state, GNSS bits, and general warnings
                                # There are some unnecessary layers here, but just ignore them
                                for sub_d_name, sub_d_value in d_value.items():
                                    nested_path = data_item_path + (sub_d_name,)
                                    self._checkout(sub_d_name, sub_d_value, path=nested_path, prefix=duplication_prefix)
                            elif isinstance(d_value, ListContainer):
                                # For warning codes
                                self._checkout(d_name, list(d_value), path=data_item_path, prefix=duplication_prefix)
                            else:
                                # For a normal data item
                                self._checkout(d_name, d_value, path=data_item_path, prefix=duplication_prefix)
                    else:
                        # Self-defined data?
                        self._checkout(data_block.data_type, data_block.data_content, path=data_block_path, prefix=duplication_prefix)    

    def _check_data_duplication(self, data_blocks):
        '''
        Check if there is duplicated data blocks in the data list.
        return a dict of data block index and duplication index.
        '''
        results = {} # index: duplication_index
        count = {} # data_type: count
        for block_index, data_block in enumerate(data_blocks):
            if data_block.data_type not in count.keys():
                results[block_index] = count[data_block.data_type] = 0
            else:
                count[data_block.data_type] += 1
                results[block_index] = count[data_block.data_type]
        return results

    def _flatten_emotor_block(self, data_block_em, duplication_prefix, em_path):
        for em_index, em_block in enumerate(data_block_em.data_content):
            single_em_path = em_path + (em_index,)
            for k_em, v_em in em_block.items():
                em_item_path = single_em_path + (f"{k_em}",)
                self._checkout(k_em, v_em, path=em_item_path, prefix=f"{duplication_prefix}em{em_block.index}-")
    
    def _flatten_warnings_block(self, data_block_warnings, duplication_prefix, warning_path):
        gw_flags = {}
        for k_w, v_w in data_block_warnings.data_content.items():
            warning_item_path = warning_path + (f"{k_w}",)
            if k_w=="general_warnings":
                for w_name, w_flag in v_w.items():
                    warning_bit_path = warning_item_path + (f"{w_name}",)
                    self._checkout(w_name, w_flag, path=warning_bit_path, prefix=duplication_prefix)
                    gw_flags[w_name] = w_flag
            elif isinstance(v_w, ListContainer):
                # As the general warning flags and codes are seperated and linked, we have to put them together here
                # If no code for a general warning, it would be a boolean True/False
                # Else the general warning would be a level integer (positive/negative for flag True/False)
                if k_w=="general_warning_list":
                    for gw_info in v_w:
                        # No path update, the path is kept with the general_warnings part
                        if gw_flags.get(gw_info.warning, False):
                            self._checkout(gw_info.warning, gw_info.level, prefix=duplication_prefix)
                        else:
                            self._checkout(gw_info.warning, 0-gw_info.level, prefix=duplication_prefix)
                else: # For warning codes
                    self._checkout(k_w, list(v_w), path=warning_item_path, prefix=duplication_prefix)
            else:
                self._checkout(k_w, v_w, path=warning_item_path, prefix=duplication_prefix)

    def _flatten_cell_volts_block(self, data_block_cell_volts, duplication_prefix, cv_path):
        for pack_index, pack_block in enumerate(data_block_cell_volts.data_content):
            pcv_path = cv_path + (pack_index,) # pack_index might be different from pack_block.index
            pack_prefix = f"{duplication_prefix}p{pack_block.index}-"
            for k_pv, v_pv in pack_block.items():
                pcv_item_path = pcv_path + (f"{k_pv}",)
                if k_pv!="cell_volts":
                    self._checkout(k_pv, v_pv, path=pcv_item_path, prefix=pack_prefix)
                else:
                    cell_start_index = pack_block.cell_start_index if hasattr(pack_block, "cell_start_index") else 0
                    for cell_index, cell_volt in enumerate(pack_block.cell_volts):
                        single_cell_path = pcv_item_path + (cell_index,)
                        self._checkout(f"{pack_prefix}c{cell_start_index+cell_index}-volt", cell_volt, path=single_cell_path)
    
    def _flatten_probe_temps_block(self, data_block_probe_temps, duplication_prefix, pt_path):
        for pack_index, pack_block in enumerate(data_block_probe_temps.data_content):
            pack_path = pt_path + (pack_index,)
            pack_prefix = f"{duplication_prefix}p{pack_block.index}-"
            for probe_index, probe_temp in enumerate(pack_block.probe_temps):
                signal_temp_path = pack_path + ("probe_temps", probe_index)
                self._checkout(f"{pack_prefix}pr{probe_index}-temp", probe_temp, path=signal_temp_path)
    
    def _checkout(self, k, v, *, prefix="", postfix="", path=None):
        if not isinstance(k, str):
            k = str(k)
        if k.startswith("_"):
            return
        flat_key = f"{prefix}{k}{postfix}"
        self[flat_key] = v
        if path is not None:
            self.pathdict[flat_key] = path