import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Welcome</CardTitle>
          <CardDescription>Use your AI agent from the dashboard or via API</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-4">
          <Button asChild>
            <Link href="/dashboard/chat">Open Chat</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/dashboard/upload">Upload documents</Link>
          </Button>
        </CardContent>
      </Card>
    </>
  );
}
