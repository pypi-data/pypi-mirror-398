"""
Example 1: Basic PDF Signing
Pure Python PDF Digital Signature

Product by Axonate Tech - https://axonatetech.com/
"""

from AxPdfSigner import PdfSigner, SignatureConfig

def main():
    # Create signer instance
    signer = PdfSigner()
    
    # Configure signature
    config = SignatureConfig(
        input_pdf=r"D:\VM\spire\spire.pdf.python_11.12.1\blank.pdf",
        output_pdf=r"D:\VM\spire\spire.pdf.python_11.12.1\example_basic_signed.pdf",
        pfx_path=r"D:\VM\spire\spire.pdf.python_11.12.1\privatekey.pfx",
        pfx_password="123"
    )
    
    # Sign the document
    try:
        print("Signing PDF...")
        signer.sign(config)
        print("✓ PDF signed successfully!")
        print(f"Output: {config.output_pdf}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
