/**
 * API client for multi-tenant backend.
 * Auth: Bearer token (from login/signup) for /auth, /upload, /chat.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type AuthInfo = {
  access_token: string;
  user_id: string;
  company_id: string;
  company_name: string;
  api_key: string;
};

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export async function signup(companyName: string, email: string, password: string): Promise<AuthInfo> {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ company_name: companyName, email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Signup failed");
  }
  const data = await res.json();
  localStorage.setItem("access_token", data.access_token);
  return data;
}

export async function login(email: string, password: string): Promise<AuthInfo> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Login failed");
  }
  const data = await res.json();
  localStorage.setItem("access_token", data.access_token);
  return data;
}

export function logout(): void {
  localStorage.removeItem("access_token");
}

export function getStoredToken(): string | null {
  return getToken();
}

export async function fetchMe(): Promise<AuthInfo | null> {
  const token = getToken();
  if (!token) return null;
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return null;
  const data = await res.json();
  return { ...data, access_token: token };
}

/** Authenticated fetch for chat (streaming). */
export async function streamChat(
  message: string,
  onChunk: (chunk: string) => void
): Promise<string> {
  const token = getToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");
  const decoder = new TextDecoder();
  let buffer = "";
  let fullMessage = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (data === "[DONE]" || data === "") continue;
        try {
          const text = data.startsWith("{") ? JSON.parse(data).data ?? data : data;
          const chunk = typeof text === "string" ? text : String(text);
          fullMessage += chunk;
          onChunk(chunk);
        } catch {
          fullMessage += data;
          onChunk(data);
        }
      }
    }
  }
  if (buffer.startsWith("data: ")) {
    const data = buffer.slice(6).trim();
    if (data && data !== "[DONE]") {
      fullMessage += data;
      onChunk(data);
    }
  }
  return fullMessage;
}

/** Upload file (auth required). */
export async function uploadFile(file: File): Promise<{ chunks_added: number }> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated");
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}
