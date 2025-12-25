"""
AxPdfSigner - Professional PDF Digital Signature SDK
=====================================================

A powerful, enterprise-grade Python SDK for digitally signing PDF documents
with advanced features including LTV, timestamping, and custom appearances.

Developed by Axonate Tech - https://axonatetech.com/

Features:
---------
- Digital signature with X.509 certificates (PFX/P12)
- Long-Term Validation (LTV) support
- RFC 3161 timestamping
- Custom signature appearance
- Multi-page signing
- Invisible signatures
- PDF metadata control
- Certificate locking
- Pure Python implementation

Usage:
------
    from AxPdfSigner import PdfSigner, SignatureConfig
    
    # Create configuration
    config = SignatureConfig(
        input_pdf="input.pdf",
        output_pdf="output.pdf",
        pfx_path="certificate.pfx",
        pfx_password="password"
    )
    
    # Sign the PDF
    signer = PdfSigner()
    signer.sign(config)

Product by: Axonate Tech
Website: https://axonatetech.com/
Version: 1.0.0
License: Commercial
"""

__version__ = "1.0.4"
__author__ = "Axonate Tech"
__license__ = "Commercial"
__website__ = "https://axonatetech.com/"

from .signer import PdfSigner, SignatureConfig, SignatureException

__all__ = ['PdfSigner', 'SignatureConfig', 'SignatureException']
