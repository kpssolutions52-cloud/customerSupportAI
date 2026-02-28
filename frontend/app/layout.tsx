import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Customer Support AI",
  description: "Production-ready Customer Support AI Agent",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans antialiased bg-[hsl(var(--surface))] text-[hsl(220_14%_96%)]">
        {children}
      </body>
    </html>
  );
}
