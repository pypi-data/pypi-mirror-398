"""
Example 3: Batch PDF Signing
Pure Python PDF Digital Signature

Product by Axonate Tech - https://axonatetech.com/
"""

from AxPdfSigner import PdfSigner, SignatureConfig
import os

def main():
    # Create signer instance
    signer = PdfSigner()
    
    # Prepare batch configurations
    configs = []
    
    base_input = r"D:\VM\spire\spire.pdf.python_11.12.1\blank.pdf"
    output_dir = r"D:\VM\spire\spire.pdf.python_11.12.1\batch_signed"
    pfx_path = r"D:\VM\spire\spire.pdf.python_11.12.1\privatekey.pfx"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create 5 signing tasks
    for i in range(1, 6):
        config = SignatureConfig(
            input_pdf=base_input,
            output_pdf=os.path.join(output_dir, f"document_{i}_signed.pdf"),
            pfx_path=pfx_path,
            pfx_password="123",
            reason=f"Batch Signing - Document {i}",
            location="Batch Processing Center",
            field_name=f"BatchSignature{i}"
        )
        configs.append(config)
    
    # Execute batch signing
    print("=" * 60)
    print("Batch PDF Signing Example")
    print("=" * 60)
    print(f"Total documents: {len(configs)}")
    print(f"Output directory: {output_dir}")
    print("-" * 60)
    
    results = signer.sign_batch(configs)
    
    print("\nResults:")
    print(f"  ✓ Success: {len(results['success'])}")
    print(f"  ✗ Failed:  {len(results['failed'])}")
    
    if results['success']:
        print("\nSuccessfully signed:")
        for item in results['success']:
            print(f"  [{item['index']+1}] {os.path.basename(item['output'])}")
    
    if results['failed']:
        print("\nFailed:")
        for item in results['failed']:
            print(f"  [{item['index']+1}] {os.path.basename(item['input'])}")
            print(f"      Error: {item['error']}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
