import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from odf.opendocument import OpenDocumentText
from odf.text import P, H
from converter.engine import ConversionEngine
from core.registry import register_all_converters

def create_odt(path):
    doc = OpenDocumentText()
    h = H(outlinelevel=1)
    h.addText("Header 1")
    doc.text.addElement(h)
    p = P()
    p.addText("Paragraph test.")
    doc.text.addElement(p)
    doc.save(path)
    print(f"Created {path}")

def verify():
    input_file = "repro_test.odt"
    create_odt(input_file)
    
    engine = ConversionEngine()
    register_all_converters(engine)
    
    formats = ['txt', 'md', 'html', 'pdf', 'docx']
    
    for fmt in formats:
        output_file = f"repro_odt_out.{fmt}"
        if os.path.exists(output_file):
            os.remove(output_file)
            
        print(f"Converting ODT -> {fmt.upper()}...")
        try:
            converter = engine.get_converter('odt')
            success = converter.convert(input_file, output_file)
            if success and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"✅ Success: {output_file} ({os.path.getsize(output_file)} bytes)")
            else:
                print(f"❌ Failed: {output_file} (Success={success})")
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    verify()
