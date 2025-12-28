from construct import ExplicitError

class PayloadSignatureVerificationError(ExplicitError):
    """If signature verification fails."""
    pass

class MissingCryptographyError(ExplicitError):
    """If the dependency of cryptography is missing."""
    pass