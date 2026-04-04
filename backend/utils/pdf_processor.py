# """
# PDF Processor for AI Study Assistant
# Handles PDF extraction, cleaning, and chunking for RAG pipeline
# """

# import PyPDF2
# import re
# import fitz  # PyMuPDF (pip install PyMuPDF)
# from typing import List, Dict, Any
# from pathlib import Path

# class PDFProcessor:
#     def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
#         """
#         Initialize PDF Processor
        
#         Args:
#             chunk_size: Number of characters per chunk
#             chunk_overlap: Overlap between chunks for context
#         """
#         self.chunk_size = chunk_size
#         self.chunk_overlap = chunk_overlap
    
#     def extract_text_pymupdf(self, pdf_path: str) -> str:
#         """Extract text using PyMuPDF (better than PyPDF2)"""
#         try:
#             doc = fitz.open(pdf_path)
#             text = ""
#             for page in doc:
#                 text += page.get_text()
#             doc.close()
#             return text
#         except ImportError:
#             return self.extract_text_pypdf2(pdf_path)
    
#     def extract_text_pypdf2(self, pdf_path: str) -> str:
#         """Fallback extraction using PyPDF2"""
#         text = ""
#         with open(pdf_path, 'rb') as file:
#             pdf_reader = PyPDF2.PdfReader(file)
#             for page_num, page in enumerate(pdf_reader.pages):
#                 try:
#                     page_text = page.extract_text()
#                     if page_text:
#                         text += page_text + "\n"
#                 except Exception:
#                     continue
#         return text
    
#     def clean_text(self, text: str) -> str:
#         """Clean and preprocess extracted text"""
#         if not text:
#             return ""
        
#         # Remove multiple spaces, newlines, tabs
#         text = re.sub(r'\s+', ' ', text)
#         text = re.sub(r'[ \t]+', ' ', text)
        
#         # Remove page numbers and headers/footers patterns
#         text = re.sub(r'Page \d+', '', text)
#         text = re.sub(r'\n\s*\n', '\n', text)
        
#         # Remove special characters but keep important ones
#         text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\$\$]', '', text)
        
#         return text.strip()
    
#     def split_into_sentences(self, text: str) -> List[str]:
#         """Split text into sentences"""
#         sentence_endings = r'[.!?]+'
#         sentences = re.split(sentence_endings, text)
#         sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
#         return sentences
    
#     def create_sliding_chunks(self, text: str) -> List[str]:
#         """Create overlapping text chunks"""
#         if len(text) <= self.chunk_size:
#             return [text]
        
#         chunks = []
#         start = 0
        
#         while start < len(text):
#             end = start + self.chunk_size
#             chunk = text[start:end]
            
#             # Ensure chunk ends at sentence boundary if possible
#             if end < len(text):
#                 next_period = text.find('.', end - 100)
#                 if 0 <= next_period < end:
#                     end = next_period + 1
            
#             if len(chunk.strip()) > 100:  # Only add meaningful chunks
#                 chunks.append(chunk.strip())
            
#             start = end - self.chunk_overlap
        
#         return chunks
    
#     def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
#         """
#         Complete PDF processing pipeline for RAG
        
#         Returns:
#             List of document chunks with metadata
#         """
#         if not Path(pdf_path).exists():
#             raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
#         print(f"🔄 Processing PDF: {pdf_path}")
        
#         # Extract text (prefer PyMuPDF)
#         raw_text = self.extract_text_pymupdf(pdf_path)
        
#         if len(raw_text) < 50:
#             raw_text = self.extract_text_pypdf2(pdf_path)
        
#         if len(raw_text) < 50:
#             raise ValueError("Could not extract meaningful text from PDF")
        
#         # Clean text
#         cleaned_text = self.clean_text(raw_text)
#         print(f"📄 Extracted {len(cleaned_text)} chars")
        
#         # Create chunks
#         chunks = self.create_sliding_chunks(cleaned_text)
#         print(f"✂️ Created {len(chunks)} chunks")
        
#         # Create document objects with metadata
#         documents = []
#         for i, chunk in enumerate(chunks):
#             documents.append({
#                 "content": chunk,
#                 "chunk_id": f"chunk_{i}",
#                 "source": Path(pdf_path).name,
#                 "page": i // 10 + 1,  # Approximate page
#                 "metadata": {
#                     "filename": Path(pdf_path).name,
#                     "chunk_index": i,
#                     "char_count": len(chunk)
#                 }
#             })
        
#         return documents

# # Test the processor
# if __name__ == "__main__":
#     processor = PDFProcessor()
#     # docs = processor.process_pdf("sample.pdf")
#     # print(f"Processed {len(docs)} chunks")
#     pass
"""
PDF Processor for AI Study Assistant
Handles PDF extraction, cleaning, and chunking for the RAG pipeline.
"""

import re
from typing import List, Dict, Any
from pathlib import Path

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False


class PDFProcessor:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        """
        Initialize PDF Processor.

        Args:
            chunk_size:    Target characters per chunk.
            chunk_overlap: Overlap between consecutive chunks for context continuity.
        """
        if not PYMUPDF_AVAILABLE and not PYPDF2_AVAILABLE:
            raise ImportError(
                "No PDF library found. Install PyMuPDF: pip install PyMuPDF  "
                "or PyPDF2: pip install PyPDF2"
            )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # ─────────────────────────────────────────
    #  EXTRACTION
    # ─────────────────────────────────────────

    def extract_text_pymupdf(self, pdf_path: str) -> str:
        """Extract text page-by-page using PyMuPDF (preferred)."""
        doc = fitz.open(pdf_path)
        pages = []
        for page in doc:
            text = page.get_text("text")  # plain-text mode
            if text.strip():
                pages.append(text)
        doc.close()
        return "\n\n".join(pages)

    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2 (fallback)."""
        pages = []
        with open(pdf_path, 'rb') as fh:
            reader = PyPDF2.PdfReader(fh)
            for page in reader.pages:
                try:
                    text = page.extract_text() or ""
                    if text.strip():
                        pages.append(text)
                except Exception:
                    continue
        return "\n\n".join(pages)

    def extract_text(self, pdf_path: str) -> str:
        """Try PyMuPDF first, fall back to PyPDF2."""
        if PYMUPDF_AVAILABLE:
            text = self.extract_text_pymupdf(pdf_path)
            if len(text.strip()) >= 50:
                return text

        if PYPDF2_AVAILABLE:
            return self.extract_text_pypdf2(pdf_path)

        return ""

    # ─────────────────────────────────────────
    #  CLEANING
    # ─────────────────────────────────────────

    def clean_text(self, text: str) -> str:
        """Normalize whitespace and remove low-value noise from extracted text."""
        if not text:
            return ""

        # Collapse runs of whitespace/newlines
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove lone page-number lines (e.g. "  12  " on its own line)
        text = re.sub(r'^\s*\d{1,4}\s*$', '', text, flags=re.MULTILINE)

        # Remove common header/footer noise
        text = re.sub(r'(?i)\bpage\s+\d+\s+of\s+\d+\b', '', text)

        # Keep only printable ASCII + common unicode letters/punctuation
        # (removes non-printable control chars while preserving accented chars)
        text = re.sub(r'[^\x20-\x7E\u00A0-\u024F\n]', ' ', text)

        return text.strip()

    # ─────────────────────────────────────────
    #  CHUNKING
    # ─────────────────────────────────────────

    def create_chunks(self, text: str) -> List[str]:
        """
        Split cleaned text into overlapping chunks, preferring sentence boundaries.
        """
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) <= self.chunk_size:
            return [text] if len(text) >= 50 else []

        chunks: List[str] = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            # Try to end on a sentence boundary within the last 20 % of the chunk
            if end < len(text):
                boundary_search_start = start + int(self.chunk_size * 0.8)
                period_pos = text.rfind('. ', boundary_search_start, end)
                if period_pos != -1:
                    end = period_pos + 2  # include the space after the period

            chunk = text[start:end].strip()
            if len(chunk) >= 50:
                chunks.append(chunk)

            # Advance start, ensuring we always make progress
            next_start = end - self.chunk_overlap
            start = next_start if next_start > start else start + 1

        return chunks

    # ─────────────────────────────────────────
    #  PUBLIC API
    # ─────────────────────────────────────────

    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Full pipeline: extract → clean → chunk → annotate.

        Returns:
            List of dicts with 'content', 'chunk_id', 'source', and 'metadata'.

        Raises:
            FileNotFoundError: if the PDF path does not exist.
            ValueError:        if no meaningful text could be extracted.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        print(f"[PDFProcessor] Processing: {path.name}")

        raw_text = self.extract_text(pdf_path)
        if len(raw_text.strip()) < 50:
            raise ValueError(
                f"Could not extract meaningful text from '{path.name}'. "
                "The PDF may be scanned/image-only or password-protected."
            )

        cleaned = self.clean_text(raw_text)
        print(f"[PDFProcessor] Extracted {len(cleaned):,} characters")

        chunks = self.create_chunks(cleaned)
        if not chunks:
            raise ValueError("Text was extracted but chunking produced no usable segments.")

        print(f"[PDFProcessor] Created {len(chunks)} chunks")

        return [
            {
                "content": chunk,
                "chunk_id": f"chunk_{i}",
                "source": path.name,
                "page": (i * self.chunk_size) // 2000 + 1,  # rough page estimate
                "metadata": {
                    "filename": path.name,
                    "chunk_index": i,
                    "char_count": len(chunk),
                    "total_chunks": len(chunks),
                },
            }
            for i, chunk in enumerate(chunks)
        ]


# ─────────────────────────────────────────────────────────────────────────────
#  Quick smoke-test
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_processor.py <path/to/file.pdf>")
        sys.exit(0)

    proc = PDFProcessor(chunk_size=800, chunk_overlap=100)
    docs = proc.process_pdf(sys.argv[1])
    print(f"\nProcessed {len(docs)} chunks")
    print(f"First chunk preview:\n{docs[0]['content'][:300]}...")
