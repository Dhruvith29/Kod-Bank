import os
import sys
import traceback

from dotenv import load_dotenv
load_dotenv()

with open("jswel_debug.txt", "w") as out:
    try:
        with open("../JSWEL-Annual-Report-Integrated-2024-25.pdf", "rb") as f:
            file_bytes = f.read()
        
        out.write(f"Read PDF, size: {len(file_bytes)} bytes\n")
        
        from fundamental import extract_text, chunk_pages
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

        out.write("Extracting text...\n")
        pages = extract_text(file_bytes)
        out.write(f"Extracted {len(pages)} pages.\n")
        
        out.write("Chunking...\n")
        chunks = chunk_pages(pages)
        out.write(f"Created {len(chunks)} chunks.\n")
        
        if not chunks:
            out.write("No chunks found.\n")
            sys.exit(0)
        
        out.write("Embedding first chunk as a test...\n")
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=chunks[0]["text"],
            task_type="retrieval_document",
            title="test"
        )
        
        if "embedding" in result:
            out.write(f"Successfully embedded first chunk, length: {len(result['embedding'])}\n")
        
        out.write(f"\nAttempting to embed ALL chunks (as it does in fundamental.py)... Sending {len(chunks)} strings...\n")
        texts_to_embed = [c["text"] for c in chunks]
        
        all_results = genai.embed_content(
            model="models/gemini-embedding-001",
            content=texts_to_embed,
            task_type="retrieval_document",
            title="JSWEL-Annual-Report-Integrated-2024-25.pdf"
        )
        
        if "embedding" in all_results:
            out.write(f"Successfully embedded all chunks. Got {len(all_results['embedding'])} vectors.\n")
            
    except Exception as e:
        out.write(f"FATAL ERROR: {str(e)}\n")
        out.write(traceback.format_exc())
