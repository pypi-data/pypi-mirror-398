"""
Example 4: Multi-Page Signing
Pure Python PDF Digital Signature

Product by Axonate Tech - https://axonatetech.com/
"""

from AxPdfSigner import PdfSigner, SignatureConfig

def main():
    # Create signer instance
    signer = PdfSigner()
    
    # Sign specific pages
    config = SignatureConfig(
        input_pdf=r"D:\VM\spire\spire.pdf.python_11.12.1\blank.pdf",
        output_pdf=r"D:\VM\spire\spire.pdf.python_11.12.1\example_multipage_signed.pdf",
        pfx_path=r"D:\VM\spire\spire.pdf.python_11.12.1\privatekey.pfx",
        pfx_password="123",
        
        # Sign multiple pages
        pages="1",  # Change to "1,2,3" or "all" for multi-page PDFs
        fast_method=True,  # Set to False for true multi-page signing
        
        reason="Multi-Page Approval",
        location="Document Center",
        coordinates="50,50,200,100"
    )
    
    print("=" * 60)
    print("Multi-Page Signing Example")
    print("=" * 60)
    print(f"Pages to sign: {config.pages}")
    print(f"Fast method: {config.fast_method}")
    print("-" * 60)
    
    try:
        signer.sign(config)
        print("✓ Multi-page signing completed!")
        print(f"Output: {config.output_pdf}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
