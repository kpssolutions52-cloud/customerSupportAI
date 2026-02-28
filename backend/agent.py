"""
AI Agent logic: RAG (Retrieval-Augmented Generation) for Customer Support.
Searches the knowledge base, then asks OpenAI (GPT-4o) to answer. Falls back to human support when no relevant context.
"""

import os
from typing import AsyncGenerator

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from db import get_vector_store

# Model for chat (GPT-4o as requested)
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")


def _format_docs(docs):
    """Turn retrieved documents into a single context string for the prompt."""
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


def get_rag_chain():
    """
    Build the RAG chain: retrieve relevant chunks from Chroma, then generate an answer with GPT-4o.
    """
    vector_store = get_vector_store()
    # Retriever: get top 4 most relevant chunks
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful customer support agent. Answer ONLY based on the following context from the company knowledge base. Be concise and professional.

If the context does not contain enough information to answer the question, respond with exactly: "I will connect you to human support."

Context:
{context}"""),
        ("human", "{question}"),
    ])

    llm = ChatOpenAI(
        model=CHAT_MODEL,
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.3,
    )

    # Chain: retrieve -> format context -> prompt -> LLM -> string
    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


def get_rag_chain_streaming():
    """
    Same as get_rag_chain but returns a chain that streams tokens (for real-time UI).
    """
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful customer support agent. Answer ONLY based on the following context from the company knowledge base. Be concise and professional.

If the context does not contain enough information to answer the question, respond with exactly: "I will connect you to human support."

Context:
{context}"""),
        ("human", "{question}"),
    ])

    llm = ChatOpenAI(
        model=CHAT_MODEL,
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.3,
        streaming=True,
    )

    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


async def chat_stream(message: str) -> AsyncGenerator[str, None]:
    """
    Stream the AI response token by token for real-time chat.
    """
    chain = get_rag_chain_streaming()
    async for chunk in chain.astream(message):
        yield chunk


def chat(message: str) -> str:
    """
    Non-streaming chat: get full response in one go.
    """
    chain = get_rag_chain()
    return chain.invoke(message)
