from construct import Adapter

"""
Handle Numbers with factor, offset and unit
"""
class DataItem(object):
    text_invalid = "invalid"
    text_abnormal = "abnormal"
    def __init__(self, value, unit, validity):
        self.value = value
        self.unit = unit
        self.valid = validity
    def __repr__(self):
        return f"DataItem({self.value}, {self.unit}, {self.valid})"
    
    def __str__(self):
        if self.valid:
            if self.unit:
                return "%s %s" % (self.value, self.unit)
            else:
                return "%s" % (self.value)
        elif self.valid==None:
            return f"{self.value} {self.text_invalid}"
        else:
            return f"{self.value} {self.text_abnormal}"
    
    def __int__(self):
        return int(self.value)
    
    def __float__(self):
        return float(self.value)
    
    def __bool__(self):
        return bool(self.value)
    
    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.value == other.value and self.unit == other.unit and self.valid == other.valid
        elif isinstance(other, (int, float)):
            return self.value == other
        else:
            return type(other)(self) == other

class DataItemAdapter(Adapter):
    def __init__(self, subcon, unit, factor=1, offset=0, *, validation=True):
        super().__init__(subcon)
        self.factor = factor
        self.offset = offset
        self.unit = unit
        self.validation = validation
        self.abnormal_value = 2**(self.sizeof()*8)-2
        self.invalid_value = 2**(self.sizeof()*8)-1
    
    def _decode(self, raw_value: int, context, path):
        validity = True
        if self.validation:
            if raw_value==self.abnormal_value:
                validity = False
            elif raw_value==self.invalid_value:
                validity = None
        return DataItem(raw_value*self.factor + self.offset, self.unit, validity)
    
    def _encode(self, phy_value: DataItem|int|float|str, context, path):
        if isinstance(phy_value, DataItem):
            phy_value = phy_value.value
        elif isinstance(phy_value, str):
            value_txt = phy_value.split(" ")[0]
            if "." in value_txt:
                phy_value = float(value_txt)
            else:
                phy_value = int(value_txt)
        raw_value = (phy_value-self.offset)/self.factor
        return int(round(raw_value))
