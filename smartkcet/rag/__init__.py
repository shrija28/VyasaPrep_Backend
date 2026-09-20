"""RAG pipeline package.

Houses the FAISS vector store, document parsing helpers (PDF/DOCX/TXT with
OCR fallback), the MCQ extractor, and the Groq LLM client wiring that
previously lived inside ``backend/app.py``.

Per-subject and institution vector store isolation (design.md §5) is exposed
via :data:`smartkcet.rag.stores` (subject vector stores) and top-level helpers.
"""

from .store import VectorStore, SubjectVectorStores, stores, store
from . import mcq_extractor

# Graceful degradation imports for groq_client and parsing
try:
    from . import groq_client
except Exception:
    groq_client = None

try:
    from . import parsing
except Exception:
    parsing = None

__all__ = [
    "VectorStore",
    "SubjectVectorStores",
    "stores",
    "store",
    "mcq_extractor",
    "groq_client",
    "parsing",
]
