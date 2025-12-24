from PyPDF2 import PdfReader

# You'll need a test PDF - create one or download any PDF
reader = PdfReader("test.pdf")
print(f"Pages: {len(reader.pages)}")
for i, page in enumerate(reader.pages[0:3]):
    text = page.extract_text() or ""
    print(f"Page {i+1} text: {text[:200]}")
