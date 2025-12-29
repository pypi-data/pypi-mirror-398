import os
import sys
from PyPDF2 import PdfReader

# Ensure we can run conversio logic if needed, but for now just validation
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def validate_pdf(path):
    print(f"Validating {path}...")
    
    if not os.path.exists(path):
        print("❌ File does not exist")
        return False
        
    size = os.path.getsize(path)
    print(f"Size: {size} bytes")
    
    if size < 10:
        print("❌ File too small")
        return False
        
    with open(path, 'rb') as f:
        header = f.read(5)
        print(f"Header: {header}")
        if header != b'%PDF-':
            print("❌ Invalid PDF header")
            return False
            
    try:
        reader = PdfReader(path)
        print(f"Pages: {len(reader.pages)}")
        print("✅ PDF Structure valid (PyPDF2 read success)")
        return True
    except Exception as e:
        print(f"❌ PyPDF2 failed to read: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        validate_pdf(sys.argv[1])
    else:
        print("Usage: python scripts/verify_pdf_validity.py <pdf_path>")
