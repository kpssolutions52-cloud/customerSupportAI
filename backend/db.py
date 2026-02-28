"""
Database and vector store setup for the Customer Support AI.
Handles Chroma vector DB initialization and document storage.
"""

import os
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Collection name for the knowledge base in Chroma
COLLECTION_NAME = "customer_support_kb"

# Directory where Chroma persists embeddings (created automatically)
PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")


def get_embeddings() -> OpenAIEmbeddings:
    """
    Create OpenAI embeddings instance.
    Uses text-embedding-3-small for cost-effectiveness; switch to text-embedding-3-large for higher quality.
    """
    return OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def get_vector_store():
    """
    Get or create the Chroma vector store with persistence.
    Uses the same collection and persist directory so data survives restarts.
    """
    persist_path = Path(PERSIST_DIR)
    persist_path.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=str(persist_path.absolute()),
    )


def get_text_splitter(chunk_size: int = 1000, chunk_overlap: int = 200):
    """
    Returns a text splitter for breaking documents into chunks.
    Overlap helps preserve context across chunk boundaries.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def load_documents_from_texts(texts: list[str], metadatas: list[dict] | None = None) -> list[Document]:
    """
    Convert raw text strings into LangChain Document objects.
    Optionally attach metadata (e.g. source file name) to each document.
    """
    if metadatas is None:
        metadatas = [{}] * len(texts)
    if len(metadatas) != len(texts):
        metadatas = [{}] * len(texts)
    return [
        Document(page_content=text, metadata=meta)
        for text, meta in zip(texts, metadatas)
    ]


def add_documents_to_kb(texts: list[str], metadatas: list[dict] | None = None) -> int:
    """
    Split texts into chunks, embed them, and add to the Chroma knowledge base.
    Returns the number of chunks added.
    """
    vector_store = get_vector_store()
    splitter = get_text_splitter()
    docs = load_documents_from_texts(texts, metadatas)
    chunks = splitter.split_documents(docs)
    if not chunks:
        return 0
    vector_store.add_documents(chunks)
    return len(chunks)
