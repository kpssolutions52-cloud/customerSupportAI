"""
Vector store (Chroma) and document ingestion — multi-tenant.
Each tenant has its own Chroma collection. We store only embeddings here; metadata (file_path) in knowledge_documents.
"""

import os
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")


def get_embeddings():
    return OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def _collection_name(tenant_id: str) -> str:
    return f"tenant_{tenant_id.replace('-', '_')}"


def get_vector_store(tenant_id: str):
    """Get or create Chroma vector store for this tenant."""
    persist_path = Path(PERSIST_DIR)
    persist_path.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=_collection_name(tenant_id),
        embedding_function=get_embeddings(),
        persist_directory=str(persist_path.absolute()),
    )


def get_text_splitter(chunk_size: int = 1000, chunk_overlap: int = 200):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def load_documents_from_texts(texts: list[str], metadatas: list[dict] | None = None) -> list[Document]:
    if metadatas is None:
        metadatas = [{}] * len(texts)
    if len(metadatas) != len(texts):
        metadatas = [{}] * len(texts)
    return [Document(page_content=t, metadata=m) for t, m in zip(texts, metadatas)]


def add_documents_to_kb(tenant_id: str, texts: list[str], file_path: str | None = None, metadatas: list[dict] | None = None) -> int:
    """
    Add documents to tenant's knowledge base (Chroma only). Optionally record file_path in knowledge_documents (caller can do that).
    Returns number of chunks added.
    """
    if not texts:
        return 0
    vector_store = get_vector_store(tenant_id)
    splitter = get_text_splitter()
    docs = load_documents_from_texts(texts, metadatas)
    chunks = splitter.split_documents(docs)
    if not chunks:
        return 0
    vector_store.add_documents(chunks)
    return len(chunks)
