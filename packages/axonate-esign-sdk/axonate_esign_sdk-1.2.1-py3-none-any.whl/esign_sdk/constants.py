"""
Constants for eSign 2.1 specification.
"""


class AuthMethods:
    """Authentication methods supported by eSign 2.1."""

    OTP_OR_TOTP = "1"
    FINGERPRINT = "2"
    IRIS = "3"
    FACE = "4"


class ResponseSigType:
    """Response signature types for eSign callback."""

    RAW_RSA = "rawrsa"
    PKCS7 = "PKCS7"
    PKCS7_PDF = "PKCS7pdf"
    PKCS7_COMPLETE = "PKCS7complete"


class HashAlgorithm:
    """Supported hash algorithms."""

    SHA256 = "SHA256"
    SHA512 = "SHA512"


class SignatureConsentFlag:
    """Signature consent flag values."""

    YES = "Y"
    NO = "N"


class KYCIdType:
    """KYC identifier types."""

    AADHAAR = "A"
