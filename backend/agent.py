"""
RAG agent — multi-tenant: per-company knowledge base and GPT-4o.
"""

import os
from typing import AsyncGenerator

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from db import get_vector_store

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")


def _format_docs(docs):
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


def get_rag_chain(company_id: str):
    """RAG chain for this company's Chroma collection."""
    vector_store = get_vector_store(company_id)
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
    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


def get_rag_chain_streaming(company_id: str):
    """Streaming RAG chain for this company."""
    vector_store = get_vector_store(company_id)
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


async def chat_stream(company_id: str, message: str) -> AsyncGenerator[str, None]:
    """Stream AI response for the company."""
    chain = get_rag_chain_streaming(company_id)
    async for chunk in chain.astream(message):
        yield chunk


def chat(company_id: str, message: str) -> str:
    """Non-streaming chat for the company."""
    chain = get_rag_chain(company_id)
    return chain.invoke(message)
