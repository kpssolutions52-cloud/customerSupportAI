"""
Knowledge base search for tenants.

search_documents(query, tenant_id) returns top 5 relevant chunks
from the tenant's Chroma collection.
"""

import os
from typing import List

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

VECTOR_DB_ROOT = os.getenv("CHROMA_PERSIST_DIR", "./data/vector_db")


def _get_vector_store(tenant_id: str) -> Chroma:
    """Load Chroma collection for this tenant."""
    embeddings = OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    return Chroma(
        collection_name=f"tenant_{tenant_id}",
        embedding_function=embeddings,
        persist_directory=VECTOR_DB_ROOT,
    )


def search_documents(query: str, tenant_id: str, k: int = 5) -> List[Document]:
    """
    Search the tenant's knowledge base for relevant chunks.

    Returns: list of LangChain Document objects (top-k).
    """
    try:
        store = _get_vector_store(tenant_id)
        return store.similarity_search(query, k=k)
    except Exception:
        return []

