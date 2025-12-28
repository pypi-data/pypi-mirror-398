from functools import reduce

from construct import Checksum, Int8ub, this


class RtmChecksum(Checksum):
    def __init__(self, data_start_key, data_end_key):
        self.data_start_key = data_start_key
        self.data_end_key = data_end_key
        super().__init__(Int8ub, self.check_body, this)
    
    def check_body(self, this): # Find the data to be checksummed
        raw_pos = this._io.tell()
        this._io.seek(this[self.data_start_key])
        body = this._io.read(this[self.data_end_key]-this[self.data_start_key])
        this._io.seek(raw_pos)
        return reduce(lambda x,y: x^y, body)
