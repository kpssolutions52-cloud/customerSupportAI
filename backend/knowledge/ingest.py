"""
Knowledge base ingestion for tenants.

Each tenant has:
- Its own document files under: DATA_DIR/{tenant_id}/documents/
- Its own Chroma collection: tenant_{tenant_id}

We use LangChain loaders + text splitter + OpenAIEmbeddings + Chroma.
Only embeddings are stored; raw document text stays in files.
"""

import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Root where vector DB is stored; structure:
# {VECTOR_DB_ROOT}/tenant_1/, tenant_2/, ...
VECTOR_DB_ROOT = os.getenv("CHROMA_PERSIST_DIR", "./data/vector_db")


def _get_loader(file_path: str):
    """
    Choose appropriate loader based on file extension.
    Supported: .pdf, .txt, .md, .docx
    """
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return PyPDFLoader(file_path)
    if suffix in (".txt", ".md"):
        return TextLoader(file_path, encoding="utf-8")
    if suffix == ".docx":
        return Docx2txtLoader(file_path)
    raise ValueError(f"Unsupported file type for ingestion: {suffix}")


def _split_documents(docs: List[Document]) -> List[Document]:
    """Split long documents into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    return splitter.split_documents(docs)


def _get_vector_store(tenant_id: str) -> Chroma:
    """
    Create or load a Chroma collection for this tenant.
    Collection name: tenant_{tenant_id}
    All collections share the same VECTOR_DB_ROOT directory.
    """
    os.makedirs(VECTOR_DB_ROOT, exist_ok=True)
    embeddings = OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    return Chroma(
        collection_name=f"tenant_{tenant_id}",
        embedding_function=embeddings,
        persist_directory=VECTOR_DB_ROOT,
    )


def ingest_document(file_path: str, tenant_id: str) -> int:
    """
    Ingest a single document file into the tenant's knowledge base.

    Steps:
    1. Load document (PDF, text, docx)
    2. Split into chunks
    3. Embed and store in Chroma collection tenant_{tenant_id}

    Returns: number of chunks stored.
    """
    loader = _get_loader(file_path)
    docs = loader.load()
    if not docs:
        return 0
    chunks = _split_documents(docs)
    if not chunks:
        return 0
    vector_store = _get_vector_store(tenant_id)
    vector_store.add_documents(chunks)
    return len(chunks)

