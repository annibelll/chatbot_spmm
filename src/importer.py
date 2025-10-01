import os
import pdfplumber
from db import insert_file, init_db

def import_pdf(filepath):
    with pdfplumber.open(filepath) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    insert_file(os.path.basename(filepath), filepath, text)

if __name__ == "__main__":
    init_db()
    import_pdf("media/pdf/example.pdf")