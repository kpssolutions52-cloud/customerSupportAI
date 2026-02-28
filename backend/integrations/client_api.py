"""
Client system integration — call tenant's APIs dynamically.

We do NOT store client business data. We only store integration config (base_url, api_key).
When the customer asks (e.g. "Where is my order 1234?"), we call the client's API
and pass the result to the AI. No orders/customers/invoices are stored in our DB.
"""

import requests
from typing import Any, Optional
from sqlalchemy.orm import Session

from models import Integration


def get_tenant_integration(db: Session, tenant_id: str, integration_type: Optional[str] = None) -> Optional[Integration]:
    """
    Load tenant's integration config from DB.
    If integration_type is given (e.g. "orders", "crm"), return that type; else return first available.
    """
    q = db.query(Integration).filter(Integration.tenant_id == tenant_id)
    if integration_type:
        q = q.filter(Integration.type == integration_type)
    return q.first()


def _build_headers(integration: Integration) -> dict:
    """Build request headers from integration config (API key / Bearer)."""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    auth_type = (integration.auth_type or "api_key").lower()
    if integration.api_key:
        if auth_type == "bearer":
            headers["Authorization"] = f"Bearer {integration.api_key}"
        else:
            headers["X-API-Key"] = integration.api_key
    return headers


def call_client_api(
    tenant_id: str,
    endpoint: str,
    method: str = "GET",
    params: Optional[dict] = None,
    body: Optional[dict] = None,
    integration_type: Optional[str] = None,
    db: Optional[Session] = None,
) -> dict[str, Any]:
    """
    Call the tenant's client system API.

    Steps:
    1. Load tenant integration config from DB (base_url, api_key, auth_type).
    2. Build full URL: base_url + endpoint.
    3. Make HTTP request using tenant's API key.
    4. Return response (status_code, body, ok). We do NOT store it.

    :param tenant_id: Tenant ID.
    :param endpoint: Path to append to base_url (e.g. "/orders/1234").
    :param method: GET, POST, etc.
    :param params: Query params.
    :param body: JSON body for POST/PUT.
    :param integration_type: Optional filter ("orders", "crm", "custom_api").
    :param db: DB session (if None, a temporary one is used).
    """
    if db is None:
        from database import SessionLocal
        db = SessionLocal()
        try:
            return _call_impl(db, tenant_id, endpoint, method, params, body, integration_type)
        finally:
            db.close()
    return _call_impl(db, tenant_id, endpoint, method, params, body, integration_type)


def _call_impl(
    db: Session,
    tenant_id: str,
    endpoint: str,
    method: str,
    params: Optional[dict],
    body: Optional[dict],
    integration_type: Optional[str],
) -> dict[str, Any]:
    integration = get_tenant_integration(db, tenant_id, integration_type)
    if not integration:
        return {"ok": False, "error": "No integration configured", "status_code": None, "body": None}

    base = integration.base_url.rstrip("/")
    path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    url = f"{base}{path}"
    headers = _build_headers(integration)

    try:
        if method.upper() == "GET":
            r = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            r = requests.post(url, headers=headers, params=params, json=body, timeout=30)
        elif method.upper() == "PUT":
            r = requests.put(url, headers=headers, params=params, json=body, timeout=30)
        else:
            r = requests.request(method, url, headers=headers, params=params, json=body, timeout=30)
    except requests.RequestException as e:
        return {"ok": False, "error": str(e), "status_code": None, "body": None}

    try:
        response_body = r.json()
    except Exception:
        response_body = r.text

    return {
        "ok": 200 <= r.status_code < 300,
        "status_code": r.status_code,
        "body": response_body,
        "error": None if r.ok else str(response_body),
    }
