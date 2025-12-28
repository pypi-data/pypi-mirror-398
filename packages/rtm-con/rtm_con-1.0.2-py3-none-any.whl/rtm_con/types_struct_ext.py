
from construct import Struct

class StructExt(Struct):
    """Extended Struct for some useful features for RTM message processing"""
    def check(self, byt_data, pubkey):
        """
        Equal to msg.parse(..., public_key=...),
        but a more safer way to pass-in the pubkey for signature checking.
        As former will not report any error for mis-spelled keyword or a empty key
        """
        if pubkey==None:
            raise TypeError("pubkey is None!")
        return self.parse(byt_data, public_key=pubkey)

    def sign(self, obj_data, prikey):
        """
        Equal to msg.build(..., private_key=...),
        but a more safer way to pass-in the prikey for signature generation
        As former will not report any error for mis-spelled keyword or a empty key
        """
        if prikey==None:
            raise TypeError("prikey is None!")
        return self.build(obj_data, private_key=prikey)
    
    def fromhex(self, hexstr, pubkey=None):
        """A helper function to parse from hex string directly with optional signature checking"""
        return self.parse(bytes.fromhex(hexstr), public_key=pubkey)
    
    def tohex(self, obj_data, prikey=None):
        """A helper function to build to hex string directly with optional signature generation"""
        return self.build(obj_data, private_key=prikey).hex()