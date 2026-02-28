"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchMe, logout } from "@/lib/api";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [info, setInfo] = useState<{ company_name: string; api_key: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMe()
      .then((data) => {
        if (data) setInfo({ company_name: data.company_name, api_key: data.api_key });
        else router.replace("/login");
      })
      .catch(() => router.replace("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  function handleLogout() {
    logout();
    router.replace("/login");
    router.refresh();
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6">
      <header className="max-w-4xl mx-auto flex items-center justify-between mb-8">
        <h1 className="text-xl font-semibold">{info?.company_name ?? "Dashboard"}</h1>
        <Button variant="outline" size="sm" onClick={handleLogout}>
          Log out
        </Button>
      </header>
      <nav className="max-w-4xl mx-auto flex flex-wrap gap-4 mb-8">
        <Button asChild>
          <Link href="/dashboard">Dashboard</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/dashboard/chat">Chat</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/dashboard/upload">Upload documents</Link>
        </Button>
      </nav>
      <div className="max-w-4xl mx-auto space-y-8">
        <Card>
          <CardHeader>
            <CardTitle>API key</CardTitle>
            <CardDescription>Use this key for API and WhatsApp webhook (X-API-Key header)</CardDescription>
          </CardHeader>
          <CardContent>
            <code className="block p-4 rounded-md bg-muted text-sm break-all">
              {info?.api_key ?? "—"}
            </code>
          </CardContent>
        </Card>
        {children}
      </div>
    </div>
  );
}
