/**
 * Chat API client.
 * Calls the FastAPI backend: streaming (SSE) and non-streaming.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

/**
 * Send a message and stream the assistant response via SSE.
 * Yields incremental content; on completion, yields the full assistant message once.
 */
export async function streamChat(
  message: string,
  onChunk: (chunk: string) => void,
  onDone?: (fullMessage: string) => void
): Promise<string> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
          // SSE may send plain text or JSON
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

  onDone?.(fullMessage);
  return fullMessage;
}

/**
 * Send a message and get the full assistant response in one shot (no streaming).
 */
export async function chatCompletion(message: string): Promise<string> {
  const res = await fetch(`${API_BASE}/chat/completion`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  const json = await res.json();
  return json.response ?? "";
}
