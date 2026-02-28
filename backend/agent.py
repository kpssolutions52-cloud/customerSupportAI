"""
AI agent — middleware flow: tenant KB + optional client API + OpenAI.

Flow:
1. Receive message, get tenant_id
2. Search tenant knowledge base (Chroma)
3. Detect if external data needed (e.g. order, customer) — if yes, call client API
4. Combine context (KB + client API response)
5. Send to OpenAI, return response

We do NOT store client business data; we only pass API responses through to the model.
"""

import os
import re
from typing import AsyncGenerator, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from db import get_vector_store
from integrations.client_api import call_client_api

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")


def _format_docs(docs):
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


def _get_kb_context(tenant_id: str, message: str, k: int = 4) -> str:
    """Retrieve relevant chunks from tenant's knowledge base."""
    try:
        store = get_vector_store(tenant_id)
        docs = store.similarity_search(message, k=k)
        return _format_docs(docs) if docs else ""
    except Exception:
        return ""


def _detect_and_fetch_client_data(tenant_id: str, message: str, db=None) -> str:
    """
    Detect if the message asks for live data (order, customer, etc.) and call client API.
    Returns a string to add to context (or empty). We do NOT store this data.
    """
    message_lower = message.lower()
    # Simple heuristic: look for "order" + number or "order #", "customer", "invoice"
    order_match = re.search(r"order\s*(?:#|number|id)?\s*[:\s]*(\d+)", message_lower, re.I)
    if order_match:
        order_id = order_match.group(1)
        result = call_client_api(tenant_id, f"/orders/{order_id}", "GET", db=db)
        if result.get("ok") and result.get("body"):
            return f"\n\n[Client system response for order {order_id}]:\n{result['body']}\n"
        if result.get("error"):
            return f"\n\n[Client system unavailable: {result['error']}]\n"

    if "customer" in message_lower or "my account" in message_lower:
        # Optional: extract customer id or use a generic /me or /customers endpoint
        result = call_client_api(tenant_id, "/customers/me", "GET", db=db)
        if result.get("ok") and result.get("body"):
            return f"\n\n[Client system response]:\n{result['body']}\n"
        if result.get("error"):
            return f"\n\n[Client system unavailable: {result['error']}]\n"

    return ""


def _build_system_prompt(kb_context: str, client_context: str) -> str:
    """Build system prompt from KB + optional client API context."""
    parts = [
        "You are a helpful customer support agent. Answer based on the following context.",
        "Be concise and professional.",
    ]
    if kb_context:
        parts.append("\nKnowledge base:\n" + kb_context)
    if client_context:
        parts.append("\nLive data from client system (use this to answer):\n" + client_context)
    parts.append(
        '\nIf the context does not contain enough information, say: "I will connect you to human support."'
    )
    return "\n".join(parts)


def _get_llm(streaming: bool = False):
    return ChatOpenAI(
        model=CHAT_MODEL,
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.3,
        streaming=streaming,
    )


def chat(tenant_id: str, message: str, db=None) -> str:
    """
    Non-streaming: get tenant KB context, optionally call client API, then OpenAI.
    """
    kb_context = _get_kb_context(tenant_id, message)
    client_context = _detect_and_fetch_client_data(tenant_id, message, db=db)
    system = _build_system_prompt(kb_context, client_context)
    llm = _get_llm(streaming=False)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "{question}"),
    ])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"question": message})


async def chat_stream(tenant_id: str, message: str, db=None) -> AsyncGenerator[str, None]:
    """Streaming: same flow, tokens streamed."""
    kb_context = _get_kb_context(tenant_id, message)
    client_context = _detect_and_fetch_client_data(tenant_id, message, db=db)
    system = _build_system_prompt(kb_context, client_context)
    llm = _get_llm(streaming=True)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "{question}"),
    ])
    chain = prompt | llm | StrOutputParser()
    async for chunk in chain.astream({"question": message}):
        yield chunk
