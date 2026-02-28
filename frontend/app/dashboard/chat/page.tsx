"use client";

import { useState, useRef, useEffect } from "react";
import { streamChat } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

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
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    setLoading(true);
    try {
      await streamChat(text, (chunk) => {
        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          if (last?.role === "assistant")
            next[next.length - 1] = { ...last, content: last.content + chunk };
          return next;
        });
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setMessages((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last?.role === "assistant" && last.content === "")
          next[next.length - 1] = { ...last, content: "Sorry, I couldn't get a response. Try again or contact support." };
        return next;
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Chat</CardTitle>
        <CardDescription>Chat with your company&apos;s AI agent (streaming)</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg border bg-muted/30 p-4 min-h-[320px] max-h-[50vh] overflow-y-auto space-y-3">
          {messages.length === 0 && (
            <p className="text-muted-foreground text-sm">Send a message to start.</p>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-foreground"
                }`}
              >
                {msg.content || (msg.role === "assistant" && loading ? "..." : "")}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <Button type="submit" disabled={loading || !input.trim()}>
            {loading ? "..." : "Send"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
