
import os
import fitz  # pymupdf

RESOURCE_DIR = os.path.join("resources", "solo_play")

def convert_pdfs_to_md():
    if not os.path.exists(RESOURCE_DIR):
        print(f"Directory not found: {RESOURCE_DIR}")
        return

    files = [f for f in os.listdir(RESOURCE_DIR) if f.endswith(".pdf")]
    
    if not files:
        print("No PDF files found.")
        return

    print(f"Found {len(files)} PDF files to convert.")

    for filename in files:
        pdf_path = os.path.join(RESOURCE_DIR, filename)
        md_filename = filename.replace(".pdf", ".md")
        md_path = os.path.join(RESOURCE_DIR, md_filename)
        
        print(f"Converting {filename}...")
        
        try:
            doc = fitz.open(pdf_path)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(f"# {filename}\n\n")
                for page_num, page in enumerate(doc):
                    text = page.get_text()
                    # Basic cleanup - could be improved based on specific PDF layout
                    text = text.strip()
                    if text:
                        f.write(f"## Page {page_num + 1}\n\n")
                        f.write(text)
                        f.write("\n\n---\n\n")
            print(f"Saved to {md_filename}")
        except Exception as e:
            print(f"Failed to convert {filename}: {e}")

if __name__ == "__main__":
    convert_pdfs_to_md()
