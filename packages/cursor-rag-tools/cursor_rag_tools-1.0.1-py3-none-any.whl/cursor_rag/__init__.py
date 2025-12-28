"""
cursor-rag-tools: RAG indexing and search for Cursor IDE via MCP
"""

__version__ = "1.0.1"

from .config import get_db_path, get_model
from .indexer import Indexer, auto_detect_project_name

__all__ = [
    "Indexer",
    "auto_detect_project_name",
    "get_db_path",
    "get_model",
    "__version__",
]
