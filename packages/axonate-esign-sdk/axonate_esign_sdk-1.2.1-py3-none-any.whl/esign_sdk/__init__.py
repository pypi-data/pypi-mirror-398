"""
eSign SDK - Python
Simple library for Indian eSign 2.1 PDF signing with deferred signature workflow.

Features:
- Create PDF with signature placeholder
- Generate eSign 2.1 XML request
- Embed PKCS7 signature from gateway response

Author: Axonate Tech
"""

from esign_sdk.sdk import SDK
from esign_sdk.pdf_factory_native import PdfFactoryNative
from esign_sdk.xml_request_factory import XMLRequestFactory
from esign_sdk.constants import AuthMethods, ResponseSigType, HashAlgorithm

__version__ = "1.0.1"
__author__ = "Axonate Tech"
__email__ = "info@axonatetech.com"

__all__ = [
    "SDK",
    "PdfFactoryNative",
    "XMLRequestFactory",
    "AuthMethods",
    "ResponseSigType",
    "HashAlgorithm",
]
