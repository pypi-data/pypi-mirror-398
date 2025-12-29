"""
eSign 2.1 XML Request Factory for building eSign requests.
"""

from datetime import datetime
from typing import Optional, List
from lxml import etree
from esign_sdk.constants import (
    AuthMethods,
    ResponseSigType,
    HashAlgorithm,
    SignatureConsentFlag,
    KYCIdType,
)


class InputHash:
    """Represents a document hash input for eSign request."""

    def __init__(
        self,
        doc_id: str,
        doc_info: str,
        hash_value: str,
        hash_algorithm: str = HashAlgorithm.SHA256,
    ):
        """
        Initialize InputHash.

        Args:
            doc_id: Document identifier
            doc_info: Document description
            hash_value: Document hash value (hexadecimal)
            hash_algorithm: Hash algorithm (default: SHA256)
        """
        self.id = doc_id
        self.doc_info = doc_info
        self.value = hash_value
        self.hash_algorithm = hash_algorithm


class XMLRequestFactory:
    """
    Factory class for building eSign 2.1 XML requests.
    """

    def __init__(self):
        """Initialize eSign request factory with default values."""
        self.ver = "2.1"
        self.sc = SignatureConsentFlag.YES
        self.ts: Optional[str] = None
        self.txn: Optional[str] = None
        self.ekyc_id = ""
        self.ekyc_id_type = KYCIdType.AADHAAR
        self.asp_id: Optional[str] = None
        self.auth_mode: Optional[str] = None
        self.response_sig_type: Optional[str] = None
        self.response_url: Optional[str] = None
        self.documents: List[InputHash] = []

    def set_txn(self, txn: str) -> None:
        """Set transaction ID."""
        self.txn = txn

    def set_ts(self, ts: str) -> None:
        """Set timestamp."""
        self.ts = ts

    def set_asp_id(self, asp_id: str) -> None:
        """Set ASP ID."""
        self.asp_id = asp_id

    def set_auth_mode(self, auth_mode: str) -> None:
        """Set authentication mode."""
        self.auth_mode = auth_mode

    def set_response_sig_type(self, response_sig_type: str) -> None:
        """Set response signature type."""
        self.response_sig_type = response_sig_type.upper()  # eSign gateway requires uppercase

    def set_response_url(self, response_url: str) -> None:
        """Set response URL."""
        self.response_url = response_url

    def add_document(
        self,
        doc_id: str,
        doc_info: str,
        hash_value: str,
        hash_algorithm: str = HashAlgorithm.SHA256,
    ) -> None:
        """
        Add document hash to the request.

        Args:
            doc_id: Document identifier
            doc_info: Document description
            hash_value: Document hash value (hexadecimal)
            hash_algorithm: Hash algorithm (default: SHA256)
        """
        input_hash = InputHash(doc_id, doc_info, hash_value, hash_algorithm)
        self.documents.append(input_hash)

    def to_xml(self) -> str:
        """
        Build and return eSign 2.1 XML request.

        Returns:
            str: XML request as string

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        if not self.txn:
            raise ValueError("Transaction ID (txn) is required")
        if not self.ts:
            raise ValueError("Timestamp (ts) is required")
        if not self.asp_id:
            raise ValueError("ASP ID (aspId) is required")
        if not self.auth_mode:
            raise ValueError("Authentication mode (AuthMode) is required")
        if not self.response_sig_type:
            raise ValueError("Response signature type (responseSigType) is required")
        if not self.response_url:
            raise ValueError("Response URL (responseUrl) is required")
        if not self.documents:
            raise ValueError("At least one document is required")

        # Build XML
        root = etree.Element("Esign")
        root.set("ver", self.ver)
        root.set("sc", self.sc)
        root.set("ts", self.ts)
        root.set("txn", self.txn)
        root.set("ekycId", self.ekyc_id)
        root.set("ekycIdType", self.ekyc_id_type)
        root.set("aspId", self.asp_id)
        root.set("AuthMode", self.auth_mode)
        root.set("responseSigType", self.response_sig_type)
        root.set("responseUrl", self.response_url)

        # Add documents
        docs_element = etree.SubElement(root, "Docs")
        for doc in self.documents:
            input_hash_element = etree.SubElement(docs_element, "InputHash")
            input_hash_element.set("id", doc.id)
            input_hash_element.set("hashAlgorithm", doc.hash_algorithm)
            input_hash_element.set("docInfo", doc.doc_info)
            input_hash_element.text = doc.value

        # Convert to string
        xml_string = etree.tostring(
            root, pretty_print=False, xml_declaration=False, encoding="unicode"
        )

        return xml_string

    @staticmethod
    def generate_timestamp() -> str:
        """
        Generate current timestamp in ISO format.

        Returns:
            str: Current timestamp in ISO format
        """
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
