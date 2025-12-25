"""
Example 2: Advanced PDF Signing with Custom Appearance
Pure Python PDF Digital Signature

Product by Axonate Tech - https://axonatetech.com/
"""

from AxPdfSigner import PdfSigner, SignatureConfig

def main():
    # Create signer instance
    signer = PdfSigner()
    
    # Advanced configuration
    config = SignatureConfig(
        input_pdf=r"D:\VM\spire\spire.pdf.python_11.12.1\blank.pdf",
        output_pdf=r"D:\VM\spire\spire.pdf.python_11.12.1\example_advanced_signed.pdf",
        pfx_path=r"D:\VM\spire\spire.pdf.python_11.12.1\privatekey.pfx",
        pfx_password="123",
        
        # Signature details
        reason="Contract Approval",
        location="New Delhi, India",
        custom_text="Digitally Signed using axBridgeiTextSigner",
        signer_name="Aniket Kumar",
        
        # Position and appearance
        coordinates="100,650,350,750",  # x1,y1,x2,y2
        field_name="ApprovalSignature",
        
        # Security features
        enable_ltv=True,
        enable_timestamp=True,
        lock_pdf=True,
        disable_green_tick=False,
        
        # PDF metadata
        title="Contract Document",
        author="Legal Department",
        subject="Employment Contract",
        keywords="contract,legal,employment,signed"
    )
    
    # Sign the document
    try:
        print("=" * 60)
        print("Advanced PDF Signing Example")
        print("=" * 60)
        print(f"Input:  {config.input_pdf}")
        print(f"Output: {config.output_pdf}")
        print(f"Reason: {config.reason}")
        print(f"Location: {config.location}")
        print("-" * 60)
        
        signer.sign(config)
        
        print("✓ PDF signed successfully!")
        print("\nFeatures applied:")
        print("  ✓ Custom signature appearance")
        print("  ✓ Long-Term Validation (LTV)")
        print("  ✓ RFC 3161 Timestamp")
        print("  ✓ PDF locked after signing")
        print("  ✓ Custom metadata")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
