from construct import (
    Construct,
    Struct,
    Int16ub,
    Enum,
    Prefixed,
    Int8ub)
try:
    # Import cryptography only if signature checking is needed
    import cryptography
except:
    cryptography = None

from rtm_con.utilities import HexAdapter
from rtm_con.types_exceptions import PayloadSignatureVerificationError, MissingCryptographyError

sig_algos = Enum(Int8ub, 
    sm2=1,
    rsa=2,
    ecc=3,
)

"""
GB/T 32960.3-2025 chp7.2.2 table8
"""

sig_con = Struct(
    "algo" / sig_algos,
    "r_value" / Prefixed(Int16ub, HexAdapter()),
    "s_value" / Prefixed(Int16ub, HexAdapter()),
)

class Signature(Construct):
    """"
    Signature construct for verifying or generating signatures
    A pair of fields "data_start_key" and "data_end_key" with peek type should be provided in the context
    to indicate which part of the data is to be signed or verified.
    """
    pub_keyword = "public_key"
    pri_keyword = "private_key"

    def __init__(self, data_start_key, data_end_key):
        super().__init__()
        self.data_start_key = data_start_key
        self.data_end_key = data_end_key
        self.base_con = sig_con

    @staticmethod
    def _find_key_in_context(context, key):
        """Recursively search for keys in nested Context."""
        curr = context
        while curr is not None:
            if key in curr:
                return curr[key]
            # Construct stores the parent context in '_'
            curr = curr.get("_")
        return None

    def _find_data_in_context(self, context):
        raw_pos = context._io.tell()
        start = self._find_key_in_context(context, self.data_start_key)
        end = self._find_key_in_context(context, self.data_end_key)
        context._io.seek(start)
        data = context._io.read(end-start)
        context._io.seek(raw_pos)
        return data

    def _parse(self, stream, context, path):
        sig = self.base_con._parse(stream, context, path)
        public_key = self._find_key_in_context(context, self.pub_keyword)
        if public_key:
            if cryptography is None:
                raise MissingCryptographyError(f'If you need signature verification, install with extras "sig" or install cryptography manually')
            elif sig.algo==sig_algos.rsa:
                # Verify signature only if public_key found in context
                signature_bytes = bytes.fromhex(sig.r_value)
                data_to_verify = self._find_data_in_context(context)
                try:
                    public_key.verify(
                        signature_bytes,
                        data_to_verify,
                        cryptography.hazmat.primitives.asymmetric.padding.PKCS1v15(),
                        cryptography.hazmat.primitives.hashes.SHA256()
                    )
                except cryptography.exceptions.InvalidSignature:
                    raise PayloadSignatureVerificationError(f"RSA Signature verification failed at path {path}")
            elif sig.algo==sig_algos.sm2:
                # TBD: SM2, which is not supported by cryptography lib yet
                raise NotImplementedError("SM2 signature verification is not implemented yet")
            elif sig.algo==sig_algos.ecc:
                raise TypeError("ECC signature is not supported by RTM authority")
            else:
                raise TypeError("The algorighm specified is not supported by protocol")
        return sig

    def _build(self, obj, stream, context, path):
        private_key = self._find_key_in_context(context, self.pri_keyword)
        if private_key:
            # Auto generate signature only if private key is provided
            if cryptography is None:
                raise MissingCryptographyError(f'If you need signature generation, install with extras "sig" or install cryptography manually')
            elif isinstance(private_key, cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey):
                data_to_sign = self._find_data_in_context(context)
                signature = private_key.sign(
                    data_to_sign,
                    cryptography.hazmat.primitives.asymmetric.padding.PKCS1v15(),
                    cryptography.hazmat.primitives.hashes.SHA256()
                )
                build_res = self.base_con.build({
                    "algo": sig_algos.rsa,
                    "r_value": signature.hex(),
                    "s_value": "",
                })
                stream.write(build_res)
                return build_res
            else:
                raise NotImplementedError(f'The algorithm of private_key is not supported')
        # No private key, skip signing part
        return self.base_con._build(obj, stream, context, path)