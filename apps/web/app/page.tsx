"use client";

import * as React from "react";
import ReactMarkdown from "react-markdown";
import { Search, Sparkles, Loader2, ExternalLink, Copy, Check, Shield, FileText, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";

type Citation = { title: string; url: string | null };
type Status = "idle" | "loading" | "success" | "error";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const EXAMPLES = [
  "What is retrieval-augmented generation and when should I use it over fine-tuning?",
  "Compare RAG evaluation methods for enterprise use",
  "Latest developments in AI agents 2026",
  "How does hybrid search (BM25 + dense) improve retrieval quality?",
];

function getDomain(url: string | null) {
  if (!url) return "";
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export default function Page() {
  const [query, setQuery] = React.useState("");
  const [status, setStatus] = React.useState<Status>("idle");
  const [report, setReport] = React.useState("");
  const [citations, setCitations] = React.useState<Citation[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [copied, setCopied] = React.useState(false);

  async function runResearch(q: string) {
    const trimmed = q.trim();
    if (trimmed.length < 3) {
      setError("Query too short. Add a bit more detail.");
      return;
    }
    setStatus("loading");
    setError(null);
    setReport("");
    setCitations([]);
    try {
      const res = await fetch(`${API_URL}/agent/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: trimmed }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${res.status})`);
      }
      const data = await res.json();
      setReport(data.report || "");
      setCitations(data.citations || []);
      setStatus("success");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong");
      setStatus("error");
    }
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    runResearch(query);
  }

  async function copyReport() {
    await navigator.clipboard.writeText(report);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Ask a research question. Get a cited report.</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Planner breaks your question into sub-queries, retriever pulls web sources via Tavily, writer synthesizes a markdown report with citations. Guardrails validate input, scrub PII, and check output shape.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge className="gap-1.5">
            <Shield className="h-3 w-3" /> guardrails on
          </Badge>
          <Badge variant="outline" className="gap-1.5">
            <Globe className="h-3 w-3" /> Groq {process.env.NEXT_PUBLIC_LLM_MODEL || "openai/gpt-oss-120b"}
          </Badge>
          <Badge variant="outline" className="gap-1.5">
            <FileText className="h-3 w-3" /> citations included
          </Badge>
        </div>
      </div>

      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Search className="h-4 w-4 text-muted-foreground" /> Research query
          </CardTitle>
          <CardDescription>Ask as you would a colleague. Be specific for better sources.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-3">
            <Textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. What are the tradeoffs between RAG and fine-tuning for enterprise QA?"
              rows={3}
              aria-label="Research query"
            />
            <div className="flex flex-wrap items-center gap-2">
              <Button type="submit" disabled={status === "loading"} className="gap-2">
                {status === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {status === "loading" ? "Researching..." : "Research"}
              </Button>
              <Button type="button" variant="secondary" onClick={() => setQuery("")} disabled={status === "loading"}>
                Clear
              </Button>
              <span className="ml-auto text-xs text-muted-foreground">{query.length} / 2000</span>
            </div>
          </form>
          <div className="mt-4 flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => setQuery(ex)}
                className="rounded-full border bg-secondary px-3 py-1 text-xs hover:bg-secondary/80 text-left"
              >
                {ex}
              </button>
            ))}
          </div>
          {error && (
            <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {status === "loading" && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-3">
              <div className="h-5 w-3/4 animate-pulse rounded bg-muted" />
              <div className="h-4 w-full animate-pulse rounded bg-muted" />
              <div className="h-4 w-5/6 animate-pulse rounded bg-muted" />
              <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
            </div>
            <p className="mt-4 text-xs text-muted-foreground">Planner and retriever are working. Writer is composing.</p>
          </CardContent>
        </Card>
      )}

      {status === "success" && (
        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm">Report</CardTitle>
              <Button variant="ghost" size="icon" onClick={copyReport} aria-label="Copy report" title="Copy">
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </CardHeader>
            <CardContent>
              <div className="prose max-w-none">
                <ReactMarkdown>{report}</ReactMarkdown>
              </div>
            </CardContent>
          </Card>

          <Card className="h-fit">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Globe className="h-4 w-4 text-muted-foreground" /> Sources
              </CardTitle>
              <CardDescription>{citations.length} sources · deduplicated</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {citations.length === 0 ? (
                <p className="text-sm text-muted-foreground">No sources returned for this query.</p>
              ) : (
                citations.map((c, i) => (
                  <a
                    key={`${c.url}-${i}`}
                    href={c.url || "#"}
                    target="_blank"
                    rel="noreferrer"
                    className="block rounded-lg border p-3 hover:bg-muted transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium leading-5 line-clamp-2">{c.title || getDomain(c.url)}</p>
                      <span className="shrink-0 text-xs text-muted-foreground">[{i + 1}]</span>
                    </div>
                    {c.url && (
                      <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground break-all">
                        {getDomain(c.url)} <ExternalLink className="h-3 w-3 shrink-0" />
                      </p>
                    )}
                  </a>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {status === "idle" && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">How it works</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground leading-6">
              1. Planner turns your question into 3 to 5 search queries.<br />
              2. Retriever fetches and dedupes web results.<br />
              3. Writer builds a cited markdown report.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Guardrails</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground leading-6">
              Input length and injection check return 400. PII is scrubbed before the LLM. Output length is validated before it reaches you.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Try it</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground leading-6">
              Hit an example chip above, then Research. API lives at <code className="rounded bg-muted px-1 py-0.5">{API_URL}</code>.
            </CardContent>
          </Card>
        </div>
      )}
    </main>
  );
}
