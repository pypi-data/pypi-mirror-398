"""
PDF Factory - Native PDF Signing Implementation
High-performance PDF digital signature operations
"""

import hashlib
import os
import sys
from typing import Optional
from pathlib import Path

# Get SDK root and native libraries directory
SDK_ROOT = Path(__file__).parent.absolute()
NATIVE_LIB_DIR = SDK_ROOT / "lib" / "native"

# Load native PDF signing library
_NATIVE_LIB_AVAILABLE = False
try:
    import clr

    # Add native library directory to path
    sys.path.append(str(NATIVE_LIB_DIR))
    clr.AddReference("System")
    clr.AddReference(str(NATIVE_LIB_DIR / "pdf_core"))
    clr.AddReference(str(NATIVE_LIB_DIR / "pdf_signer"))

    # Import native signing module (v1.1.0+ uses PdfPlaceholderLib)
    from PdfPlaceholderLib import PdfPlaceholderFactory

    _NATIVE_LIB_AVAILABLE = True
except Exception as e:
    _NATIVE_LIB_AVAILABLE = False
    print(f"Warning: Native PDF library not available: {e}")


class PdfFactoryNative:
    """
    PDF Factory - Native PDF digital signature implementation.

    Provides deferred signing capabilities for eSign integration.
    """

    def __init__(self):
        if not _NATIVE_LIB_AVAILABLE:
            raise RuntimeError(
                "Native PDF library is not available. Please ensure:\n"
                "1. pythonnet is installed: pip install pythonnet\n"
                f"2. Native libraries exist in: {NATIVE_LIB_DIR}\n"
                "3. Required files: pdf_core.dll, pdf_core_lic.dll, pdf_signer.dll"
            )

    def empty_signature(
        self,
        src: str,
        dest: str,
        field_name: str,
        page_nums: list = None,
        page_num: int = 1,
        visible: bool = True,
        signer_name: Optional[str] = "",
        reason: Optional[str] = "",
        location: Optional[str] = "",
        custom_text: Optional[str] = "",
        include_subject: bool = False,
        disable_green_tick: bool = False,
        lock_pdf: bool = False,
        rect: tuple = (10, 10, 200, 100),
        estimated_size: int = 15000,
        cert_path: Optional[str] = "",
        cert_password: Optional[str] = "",
    ) -> str:
        """
        Create PDF with empty signature placeholder for deferred signing.

        Args:
            src: Source PDF file path
            dest: Destination PDF with placeholder
            field_name: Signature field name
            page_num: Page number (1-indexed)
            visible: True for visible signature, False for invisible
            signer_name: Signer name (empty = use certificate CN)
            reason: Reason for signing (optional)
            location: Location of signing (optional)
            custom_text: Custom text to show in signature (optional)
            include_subject: Include certificate DN in signature (default: False)
            disable_green_tick: True to disable green tick, False to enable (default: False)
            lock_pdf: True to certify/lock PDF (default: False)
            rect: (x, y, width, height) for signature box position
            estimated_size: Estimated PKCS7 signature size in bytes
            cert_path: Path to certificate (.pfx) for extracting CN/DN (optional)
            cert_password: Certificate password (optional)

        Returns:
            SHA-256 hash (hex, lowercase) of the byte range to be signed
        """
        # Convert rect tuple to coordinates string
        x, y, width, height = rect
        coordinates = f"{x},{y},{width},{height}"

        # Prepare parameters - pass empty string if None
        signer_name = signer_name or ""
        reason = reason or ""
        location = location or ""

        try:
            # v1.1.0: Use PdfPlaceholderFactory.CreatePlaceholder
            # Convert coordinates to rect components
            x, y, width, height = rect
            llx, lly, urx, ury = x, y, x + width, y + height

            # Determine page specification
            if page_nums and len(page_nums) > 1:
                # Multiple pages: convert to string like "1,3,5"
                pages_str = ",".join(str(p) for p in page_nums)
            else:
                # Single page
                actual_page = page_nums[0] if page_nums else page_num
                pages_str = str(actual_page)

            # Call new DLL
            hash_value = PdfPlaceholderFactory.CreatePlaceholder(
                srcPdf=src,
                destPdf=dest,
                fieldName=field_name,
                signerName=signer_name,
                reason=reason or "",
                location=location or "",
                customText=custom_text or "",
                pages=pages_str,
                llx=float(llx),
                lly=float(lly),
                urx=float(urx),
                ury=float(ury),
                isGreenTicked=not disable_green_tick,
                certify=lock_pdf,
                estimatedSize=estimated_size
            )

            return hash_value

        except Exception as e:
            raise RuntimeError(f"Failed to create empty signature: {e}")

    def embed_signature(
        self,
        src: str,
        dest: str,
        field_name: str,
        pkcs7_signature: str,
        cert_path: Optional[str] = None,
        cert_password: Optional[bytes] = None,
        signer_name: str = "eSign User",
        reason: str = "eSign Document Signing",
        location: str = "India",
    ) -> None:
        """
        Embed PKCS7 signature into the placeholder.

        Args:
            src: PDF with empty signature placeholder
            dest: Destination signed PDF
            field_name: Signature field name
            pkcs7_signature: Base64-encoded PKCS7 from eSign server
            Other params: Ignored (already set in placeholder)
        """
        try:
            # v1.1.0: Use PdfPlaceholderFactory.EmbedSignature
            PdfPlaceholderFactory.EmbedSignature(
                placeholderPdf=src,
                signedPdf=dest,
                fieldName=field_name,
                pkcs7Base64=pkcs7_signature
            )

        except Exception as e:
            raise RuntimeError(f"Failed to embed signature: {e}")

    def calculate_hash_from_file(self, file_path: str) -> str:
        """Calculate SHA-256 hash of PDF file."""
        with open(file_path, 'rb') as f:
            return self.calculate_hash_from_bytes(f.read())

    def calculate_hash_from_bytes(self, pdf_bytes: bytes) -> str:
        """Calculate SHA-256 hash of PDF bytes."""
        return hashlib.sha256(pdf_bytes).hexdigest().lower()
