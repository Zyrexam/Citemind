import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ResearchMind",
  description: "Multi-agent research assistant that plans, retrieves, and writes cited reports",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background">
        <header className="sticky top-0 z-10 border-b bg-white/80 backdrop-blur">
          <div className="mx-auto flex max-w-6xl items-center gap-3 px-6 py-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
              R
            </div>
            <span className="text-sm font-semibold tracking-tight">ResearchMind</span>
            <span className="ml-2 hidden text-xs text-muted-foreground sm:inline">
              plan · retrieve · write · cite
            </span>
            <div className="ml-auto text-xs text-muted-foreground">Groq + Tavily</div>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
