"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { uploadFile } from "@/lib/api";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ chunks_added: number } | null>(null);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const res = await uploadFile(file);
      setResult(res);
      setFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload documents</CardTitle>
        <CardDescription>Add .txt, .md, or .csv files to your knowledge base</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="file">File</Label>
            <Input
              id="file"
              type="file"
              accept=".txt,.md,.csv"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          {result && (
            <p className="text-sm text-muted-foreground">
              Added {result.chunks_added} chunks to your knowledge base.
            </p>
          )}
          <Button type="submit" disabled={!file || loading}>
            {loading ? "Uploading..." : "Upload"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
