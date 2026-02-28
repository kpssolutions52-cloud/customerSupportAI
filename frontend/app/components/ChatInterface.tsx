"use client";

import { useState, useRef, useEffect } from "react";
import { streamChat } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setError(null);
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    // Placeholder assistant message; we'll stream into it
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      await streamChat(
        text,
        (chunk) => {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last?.role === "assistant") {
              next[next.length - 1] = { ...last, content: last.content + chunk };
            }
            return next;
          });
        }
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      setError(message);
      setMessages((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last?.role === "assistant" && last.content === "") {
          next[next.length - 1] = { ...last, content: "Sorry, I couldn't get a response. Please try again or contact human support." };
        }
        return next;
      });
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-3xl mx-auto">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--surface-muted))] p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-[hsl(220_14%_65%)] py-12">
            <p className="text-lg font-medium">Customer Support AI</p>
            <p className="text-sm mt-1">Ask anything. I’ll use the knowledge base when possible, or connect you to human support.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                msg.role === "user"
                  ? "bg-[hsl(var(--accent))] text-white"
                  : "bg-[hsl(220_14%_16%)] text-[hsl(220_14%_96%)] border border-[hsl(var(--border))]"
              }`}
            >
              <p className="whitespace-pre-wrap break-words text-sm">{msg.content || (msg.role === "assistant" && loading ? "..." : "")}</p>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {error && (
        <p className="text-red-400 text-sm mt-2 text-center">{error}</p>
      )}

      {/* Input form */}
      <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          placeholder="Type your message..."
          rows={1}
          className="flex-1 resize-none rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--surface-muted))] px-4 py-3 text-sm text-white placeholder-[hsl(220_14%_50%)] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--accent))]"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-xl bg-[hsl(var(--accent))] px-5 py-3 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
        >
          {loading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}
