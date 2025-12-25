"""
PDF Signer Module - Main signing interface
Pure Python implementation for professional PDF digital signatures

Product by Axonate Tech - https://axonatetech.com/
"""

import os
import sys
from typing import Optional, List
from dataclasses import dataclass, field
from ._core import _CoreSigner


class SignatureException(Exception):
    """Exception raised for signature-related errors"""
    pass


@dataclass
class SignatureConfig:
    """
    Configuration for PDF digital signature
    
    Required Parameters:
    -------------------
    input_pdf : str
        Path to input PDF file
    output_pdf : str
        Path to output signed PDF file
    pfx_path : str
        Path to PFX/P12 certificate file
    pfx_password : str
        Password for the PFX certificate
    
    Optional Parameters:
    -------------------
    pages : str
        Pages to sign (default: "1")
        Examples: "1", "1,3,5", "1-5", "all"
    
    field_name : str
        Signature field name (default: "Signature1")
    
    reason : str
        Reason for signing (default: "Document Signing")
    
    location : str
        Location of signing (default: "")
    
    custom_text : str
        Custom text to display in signature (default: "")
    
    signer_name : str
        Override signer name (default: from certificate CN)
    
    coordinates : str
        Signature position "x1,y1,x2,y2" (default: "100,100,300,150")
    
    enable_ltv : bool
        Enable Long-Term Validation (default: True)
    
    enable_timestamp : bool
        Enable RFC 3161 timestamping (default: True)
    
    disable_green_tick : bool
        Disable green tick in Adobe Reader (default: False)
    
    lock_pdf : bool
        Lock PDF after signing (default: True)
    
    include_subject : bool
        Include certificate subject DN (default: False)
    
    invisible_signature : bool
        Make signature invisible (default: False)
    
    fast_method : bool
        Use fast signing method (default: True)
    
    title : str
        PDF document title (default: "")
    
    author : str
        PDF document author (default: "")
    
    subject : str
        PDF document subject (default: "")
    
    keywords : str
        PDF document keywords (default: "")
    """
    
    # Required fields
    input_pdf: str
    output_pdf: str
    pfx_path: str
    pfx_password: str
    
    # Optional fields with defaults
    pages: str = "1"
    field_name: str = "Signature1"
    reason: str = "Document Signing"
    location: str = ""
    custom_text: str = ""
    signer_name: str = ""
    coordinates: str = "100,100,300,150"
    enable_ltv: bool = True
    enable_timestamp: bool = True
    disable_green_tick: bool = False
    lock_pdf: bool = True
    include_subject: bool = False
    invisible_signature: bool = False
    fast_method: bool = True
    title: str = ""
    author: str = ""
    subject: str = ""
    keywords: str = ""
    
    def validate(self):
        """Validate configuration parameters"""
        if not os.path.exists(self.input_pdf):
            raise SignatureException(f"Input PDF not found: {self.input_pdf}")
        
        if not os.path.exists(self.pfx_path):
            raise SignatureException(f"PFX certificate not found: {self.pfx_path}")
        
        if not self.pfx_password:
            raise SignatureException("PFX password is required")
        
        # Validate coordinates format
        try:
            coords = self.coordinates.split(',')
            if len(coords) != 4:
                raise ValueError
            [float(c) for c in coords]
        except:
            raise SignatureException(f"Invalid coordinates format: {self.coordinates}. Expected: 'x1,y1,x2,y2'")
        
        return True


class PdfSigner:
    """
    Professional PDF Digital Signature Engine
    
    This class provides a high-level interface for signing PDF documents
    with digital certificates using industry-standard cryptographic methods.
    
    Example:
    --------
        signer = PdfSigner()
        
        config = SignatureConfig(
            input_pdf="document.pdf",
            output_pdf="signed_document.pdf",
            pfx_path="certificate.pfx",
            pfx_password="mypassword",
            reason="Contract Approval",
            location="New York",
            enable_ltv=True,
            enable_timestamp=True
        )
        
        signer.sign(config)
    """
    
    def __init__(self):
        """Initialize PDF Signer"""
        self._core = _CoreSigner()
    
    def sign(self, config: SignatureConfig) -> bool:
        """
        Sign a PDF document with digital certificate
        
        Parameters:
        -----------
        config : SignatureConfig
            Signature configuration object
        
        Returns:
        --------
        bool
            True if signing was successful
        
        Raises:
        -------
        SignatureException
            If signing fails for any reason
        """
        try:
            # Validate configuration
            config.validate()
            
            # Execute signing through core engine
            self._core.execute_sign(config)
            
            # Verify output was created
            if not os.path.exists(config.output_pdf):
                raise SignatureException("Signing failed: Output PDF was not created")
            
            return True
            
        except SignatureException:
            raise
        except Exception as e:
            raise SignatureException(f"Signing failed: {str(e)}")
    
    def sign_batch(self, configs: List[SignatureConfig]) -> dict:
        """
        Sign multiple PDF documents in batch
        
        Parameters:
        -----------
        configs : List[SignatureConfig]
            List of signature configurations
        
        Returns:
        --------
        dict
            Dictionary with results: {'success': [...], 'failed': [...]}
        """
        results = {'success': [], 'failed': []}
        
        for i, config in enumerate(configs):
            try:
                self.sign(config)
                results['success'].append({
                    'index': i,
                    'input': config.input_pdf,
                    'output': config.output_pdf
                })
            except Exception as e:
                results['failed'].append({
                    'index': i,
                    'input': config.input_pdf,
                    'error': str(e)
                })
        
        return results
    
    @staticmethod
    def get_version() -> str:
        """Get SDK version"""
        from . import __version__, __website__
        return f"AxPdfSigner v{__version__} by Axonate Tech ({__website__})"
    
    @staticmethod
    def validate_certificate(pfx_path: str, pfx_password: str) -> dict:
        """
        Validate a PFX certificate
        
        Parameters:
        -----------
        pfx_path : str
            Path to PFX file
        pfx_password : str
            PFX password
        
        Returns:
        --------
        dict
            Certificate information
        """
        if not os.path.exists(pfx_path):
            raise SignatureException(f"Certificate not found: {pfx_path}")
        
        # Basic validation - file exists and has content
        size = os.path.getsize(pfx_path)
        if size == 0:
            raise SignatureException("Certificate file is empty")
        
        return {
            'path': pfx_path,
            'size': size,
            'valid': True
        }
