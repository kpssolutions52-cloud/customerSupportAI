import ChatInterface from "./components/ChatInterface";

export default function Home() {
  return (
    <main className="min-h-screen p-6 md:p-8">
      <header className="text-center mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
          Customer Support AI
        </h1>
        <p className="text-[hsl(220_14%_65%)] mt-1 text-sm">
          Powered by RAG · Answers from your knowledge base or human support
        </p>
      </header>
      <ChatInterface />
    </main>
  );
}
