"""
Main SDK class providing factory methods for eSign functionality.
"""

from esign_sdk.pdf_factory_native import PdfFactoryNative
from esign_sdk.xml_request_factory import XMLRequestFactory


class SDK:
    """
    Main SDK class providing factory methods to access eSign functionality.
    Provides PDF signing and XML request generation for Indian eSign integration.
    """

    @staticmethod
    def get_pdf_factory_instance():
        """
        Returns PDF factory instance for digital signature operations.

        Returns:
            PdfFactoryNative: Instance for PDF signing operations
        """
        return PdfFactoryNative()

    @staticmethod
    def get_xml_request_factory_instance():
        """
        Returns XML factory instance for eSign 2.1 request generation.

        Returns:
            XMLRequestFactory: Instance for building eSign XML requests
        """
        return XMLRequestFactory()
