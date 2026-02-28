import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6">
      <div className="max-w-2xl text-center space-y-8">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
          Customer Support AI
        </h1>
        <p className="text-lg text-muted-foreground">
          Multi-tenant SaaS. Give each company its own AI agent, knowledge base, and API key.
        </p>
        <div className="flex flex-wrap gap-4 justify-center">
          <Button asChild size="lg">
            <Link href="/login">Log in</Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/signup">Sign up</Link>
          </Button>
        </div>
      </div>
    </main>
  );
}
