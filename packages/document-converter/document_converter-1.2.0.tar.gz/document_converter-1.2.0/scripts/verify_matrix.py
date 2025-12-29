import os
import sys
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from converter.engine import ConversionEngine
from core.registry import register_all_converters

# Setup logging to avoid clutter
logging.basicConfig(level=logging.CRITICAL)

def create_sample_files():
    samples = {}
    
    # TXT
    with open('sample.txt', 'w') as f:
        f.write("Sample text")
    samples['txt'] = 'sample.txt'
    
    # MD
    with open('sample.md', 'w') as f:
        f.write("# Sample MD\nText")
    samples['md'] = 'sample.md'
    
    # HTML
    with open('sample.html', 'w') as f:
        f.write("<html><body><h1>Sample HTML</h1></body></html>")
    samples['html'] = 'sample.html'
    
    # DOCX
    try:
        import docx
        doc = docx.Document()
        doc.add_paragraph("Sample DOCX")
        doc.save('sample.docx')
        samples['docx'] = 'sample.docx'
    except ImportError:
        print("Skipping DOCX creation (python-docx not found)")

    # ODT
    try:
        from odf.opendocument import OpenDocumentText
        from odf.text import P
        textdoc = OpenDocumentText()
        p = P(text="Sample ODT")
        textdoc.text.addElement(p)
        textdoc.save("sample.odt")
        samples['odt'] = 'sample.odt'
    except ImportError:
         print("Skipping ODT creation (odfpy not found)")

    # PDF
    try:
        from reportlab.pdfgen import canvas
        c = canvas.Canvas("sample.pdf")
        c.drawString(100, 750, "Sample PDF")
        c.save()
        samples['pdf'] = 'sample.pdf'
    except ImportError:
        print("Skipping PDF creation (reportlab not found)")
        
    return samples

def verify():
    engine = ConversionEngine()
    register_all_converters(engine)
    
    formats = sorted(engine.get_supported_formats())
    print(f"Supported formats in registry: {formats}")
    
    samples = create_sample_files()
    
    results = {}
    
    for input_fmt in formats:
        if input_fmt not in samples:
            print(f"⚠ Skipping input format {input_fmt} (no sample file)")
            continue
            
        results[input_fmt] = {}
        input_file = samples[input_fmt]
        
        for output_fmt in formats:
            if input_fmt == output_fmt:
                continue
                
            output_file = f"output.{output_fmt}"
            if os.path.exists(output_file):
                os.remove(output_file)
                
            try:
                converter = engine.get_converter(input_fmt)
                if converter.convert(input_file, output_file):
                    results[input_fmt][output_fmt] = "✅ OK"
                else:
                    results[input_fmt][output_fmt] = "❌ Failed (False)"
            except Exception as e:
                results[input_fmt][output_fmt] = f"❌ Error: {str(e)}"
            finally:
                if os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                    except:
                        pass

    # Print Matrix
    print("\nconversion Matrix (Input -> Output):")
    header = "       " + " ".join([f"{f:>6}" for f in formats])
    print(header)
    print("-" * len(header))
    
    for input_fmt in formats:
        if input_fmt not in results:
            continue
        row = f"{input_fmt:>6} "
        for output_fmt in formats:
            if input_fmt == output_fmt:
                row += "   --  "
            else:
                res = results[input_fmt].get(output_fmt, "   ?  ")
                symbol = "  OK  " if "OK" in res else " FAIL "
                row += symbol
        print(row)
        
    # Print details for failures
    print("\nDetailed Failures:")
    for input_fmt, outputs in results.items():
        for output_fmt, status in outputs.items():
            if "OK" not in status:
                print(f"{input_fmt} -> {output_fmt}: {status}")

if __name__ == "__main__":
    verify()
