"use client";

import * as React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Loader2, ExternalLink, Check, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8123";

type Citation = { title: string; url: string | null; snippet?: string | null };
type Status = "idle" | "loading" | "success" | "error";

const MAX = 2000;

const EXAMPLES = [
  "When does retrieval beat fine-tuning?",
  "How should a RAG system be evaluated?",
  "What does hybrid search actually buy you?",
  "Where does agentic retrieval break down?",
];

/*
 * The writer is asked for "[n]" but the model tends to answer 【n†L1-L4】 --
 * a source figure plus a line pinpoint. Both forms are real citations, so both
 * become keys; the pinpoint is lifted out of the text into the margin card,
 * where it belongs.
 */
const CITE = /[【[]\s*(\d{1,2})\s*(?:†[^】\]]*)?[】\]]/g;
const PIN = /[【[]\s*(\d{1,2})\s*†\s*([^】\]]+?)\s*[】\]]/g;

function tidyCitations(md: string) {
  return md.replace(CITE, (_m, n) => `[${n}]`);
}

function useCitationKeys(active: number | null, setActive: (n: number | null) => void) {
  return React.useCallback(
    function transform(node: React.ReactNode): React.ReactNode {
      if (typeof node === "string") {
        const parts: React.ReactNode[] = [];
        let last = 0;
        for (const m of node.matchAll(CITE)) {
          const i = m.index ?? 0;
          if (i > last) parts.push(node.slice(last, i));
          const n = Number(m[1]);
          parts.push(
            <button
              key={`${n}-${i}`}
              type="button"
              onClick={() => setActive(active === n ? null : n)}
              onMouseEnter={() => setActive(n)}
              aria-label={`Source ${n}`}
              className="key"
              data-active={active === n ? "true" : undefined}
            >
              {n}
            </button>
          );
          last = i + m[0].length;
        }
        if (last < node.length) parts.push(node.slice(last));
        return parts.length ? parts : node;
      }
      if (Array.isArray(node)) {
        return node.map((c, i) => <React.Fragment key={i}>{transform(c)}</React.Fragment>);
      }
      if (React.isValidElement(node)) {
        const el = node as React.ReactElement<{ children?: React.ReactNode }>;
        const kids = el.props?.children;
        if (kids && kids !== node) {
          return React.cloneElement(el, { children: transform(kids) } as never);
        }
      }
      return node;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [active]
  );
}

function domainOf(url: string | null) {
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
  const [active, setActive] = React.useState<number | null>(null);
  const [elapsed, setElapsed] = React.useState(0);
  const [copied, setCopied] = React.useState(false);

  const withKeys = useCitationKeys(active, setActive);
  const reportRef = React.useRef<HTMLDivElement>(null);

  const pinpoints = React.useMemo(() => {
    const map: Record<number, string> = {};
    for (const m of report.matchAll(PIN)) {
      map[Number(m[1])] = m[2].replace(/-/g, "–");
    }
    return map;
  }, [report]);

  React.useEffect(() => {
    if (status !== "loading") return;
    setElapsed(0);
    const t = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(t);
  }, [status]);

  async function runResearch(q: string) {
    const trimmed = q.trim();
    if (trimmed.length < 3) {
      setError("Add a little more to the question before asking.");
      setStatus("error");
      return;
    }
    setStatus("loading");
    setError(null);
    setReport("");
    setCitations([]);
    setActive(null);
    try {
      const res = await fetch(`${API_URL}/agent/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: trimmed }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `The request failed (${res.status}).`);
      }
      const data = await res.json();
      setReport(data.report || "");
      setCitations(data.citations || []);
      setStatus("success");
      requestAnimationFrame(() =>
        reportRef.current?.scrollIntoView({ behavior: "instant", block: "start" })
      );
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
      setStatus("error");
    }
  }

  async function copyReport() {
    await navigator.clipboard.writeText(tidyCitations(report));
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  function downloadReport() {
    const sources = citations
      .map((c, i) => `${i + 1}. [${c.title || "Untitled source"}](${c.url ?? ""})`)
      .join("\n");
    const md = `# ${query.trim()}\n\n${tidyCitations(report)}\n\n## Sources\n\n${sources}\n`;
    const url = URL.createObjectURL(new Blob([md], { type: "text/markdown" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `${query.trim().slice(0, 60).replace(/[^\w\s-]/g, "") || "research"}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const activeCitation = active != null ? citations[active - 1] : undefined;

  const keyed = (Tag: "p" | "li" | "td" | "th") =>
    function Renderer({ children }: { children?: React.ReactNode }) {
      return React.createElement(Tag, null, withKeys(children));
    };

  const markdown = {
    p: keyed("p"),
    li: keyed("li"),
    td: keyed("td"),
    th: keyed("th"),
    table: ({ children }: { children?: React.ReactNode }) => (
      <div className="-mx-1 overflow-x-auto px-1">
        <table>{children}</table>
      </div>
    ),
  };

  return (
    <div className="max-w-5xl">
      <form onSubmit={(e) => { e.preventDefault(); runResearch(query); }}>
        <label
          htmlFor="research"
          className="ledger-label block border-b border-rule-strong pb-1.5"
        >
          Your question
        </label>
        <div className="slip mt-2 rounded-[3px] border border-rule px-4 py-3">
          <Textarea
            id="research"
            value={query}
            onChange={(e) => setQuery(e.target.value.slice(0, MAX))}
            rows={3}
            placeholder="What are the tradeoffs between retrieval and fine-tuning for enterprise question answering?"
          />
        </div>

        <div className="mt-4 flex flex-wrap items-baseline gap-x-5 gap-y-2">
          <Button type="submit" disabled={status === "loading"}>
            {status === "loading" ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : null}
            {status === "loading" ? "Working" : "Research"}
          </Button>
          {status !== "loading" && (
            <Button type="button" variant="quiet" size="quiet" onClick={() => { setQuery(""); setStatus("idle"); setReport(""); setCitations([]); setError(null); setActive(null); }}>
              Clear
            </Button>
          )}
          <span className="tnum ml-auto font-ui text-[12px] text-ink-faint">
            {query.length} / {MAX}
          </span>
        </div>
      </form>

      <div className="mt-8">
        <p className="ledger-label border-b border-rule pb-1.5">Or start from a question</p>
        <ul className="mt-1">
          {EXAMPLES.map((ex, i) => (
            <li key={ex}>
              <button
                type="button"
                onClick={() => setQuery(ex)}
                className="flex w-full items-baseline gap-3 border-b border-rule/70 py-2.5 text-left transition-colors duration-75 hover:bg-leaf"
              >
                <span className="tnum font-ui text-[12px] text-ink-faint">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="font-text text-[0.9375rem] text-ink-soft transition-colors duration-75 hover:text-ink">
                  {ex}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>

      {citations.length > 0 && (
        <section className="mt-12" aria-label="Sources">
          <h2 className="ledger-label border-b border-rule-strong pb-1.5">Sources</h2>
          <ol className="mt-1">
            {citations.map((c, i) => {
              const n = i + 1;
              return (
                <li key={`${c.url}-${n}`}>
                  <button
                    type="button"
                    onClick={() => setActive(active === n ? null : n)}
                    onMouseEnter={() => setActive(n)}
                    className="legend-row w-full transition-colors duration-75"
                    data-active={active === n ? "true" : undefined}
                  >
                    <span className="tnum pt-[0.15em] font-ui text-[12px] text-ink-faint">
                      {n}
                    </span>
                    <span className="min-w-0">
                      <span className="block font-text text-[0.9375rem] leading-snug text-ink">
                        {c.title || domainOf(c.url)}
                      </span>
                      <span className="mt-0.5 block truncate font-ui text-[12px] text-ink-faint">
                        {domainOf(c.url)}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>
        </section>
      )}

      <section className="mt-14" aria-label="Report" ref={reportRef}>
        <div className="flex items-start justify-between gap-8 border-b border-rule-strong pb-4">
          <div className="min-w-0">
            <p className="ledger-label">The report</p>
            <h2 className="mt-2.5 max-w-measure font-text text-[1.75rem] font-semibold leading-[1.22] tracking-[-0.018em] text-ink">
              {status === "success" ? query.trim() : "Your report will appear here"}
            </h2>
          </div>
          {status === "success" && report && (
            <span className="flex shrink-0 items-baseline gap-4 pt-1">
              <Button type="button" variant="quiet" size="quiet" onClick={downloadReport}>
                <Download className="h-3.5 w-3.5" />
                Download
              </Button>
              <Button type="button" variant="quiet" size="quiet" onClick={copyReport}>
                {copied ? <Check className="h-3.5 w-3.5" /> : null}
                {copied ? "Copied" : "Copy"}
              </Button>
            </span>
          )}
        </div>

        {status === "idle" && <Specimen withKeys={withKeys} />}

        {status === "loading" && (
          <div className="pt-6">
            <p className="font-ui text-[13px] text-ink-soft" role="status">
              Planning, retrieving, writing.
              <span className="tnum text-ink-faint" aria-hidden="true">
                {" "}
                {elapsed}s
              </span>
            </p>
            <div className="mt-5 space-y-3" aria-hidden="true">
              {[92, 78, 96, 61, 88, 70].map((w, i) => (
                <div
                  key={i}
                  className="step-in h-3 rounded-[2px] bg-rule/55"
                  style={{ width: `${w}%`, animationDelay: `${i * 70}ms` }}
                />
              ))}
            </div>
          </div>
        )}

        {status === "error" && error && (
          <div className="step-in pt-6">
            <p className="flex gap-2.5 font-text text-[1.0625rem] text-ink">
              <span aria-hidden="true" className="font-ui text-rubric">
                ✳
              </span>
              <span>{error}</span>
            </p>
            <p className="mt-2 pl-7 font-text text-[0.9375rem] text-ink-soft">
              Edit the question above and ask again.
            </p>
          </div>
        )}

        {status === "success" && (
          <div className="grid gap-x-8 pt-6 lg:grid-cols-[minmax(0,70ch)_16rem]">
            <div className="report max-w-measure">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdown}>{report}</ReactMarkdown>
            </div>
            <aside className="mt-8 lg:mt-0">
              <div className="lg:sticky lg:top-8">
                {activeCitation ? (
                  <div className="step-in">
                    <div className="flex items-baseline justify-between gap-4 border-b border-rule-strong pb-2">
                      <span className="ledger-label">Source</span>
                      <span className="tnum font-text text-[2rem] font-semibold leading-none text-primary">
                        {active}
                      </span>
                    </div>
                    <p className="mt-3 font-text text-[1rem] leading-snug text-ink">
                      {activeCitation.title || domainOf(activeCitation.url)}
                    </p>
                    {activeCitation.url && (
                      <a
                        href={activeCitation.url}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-2.5 inline-flex items-center gap-1.5 font-ui text-[12px] text-ink-soft underline decoration-rule-strong underline-offset-[0.2em] transition-colors duration-75 hover:text-primary hover:decoration-primary"
                      >
                        {domainOf(activeCitation.url)}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                    {active !== null && pinpoints[active] && (
                      <p className="mt-4 border-t border-rule pt-2.5 font-ui text-[11px] text-ink-faint">
                        Cited at {pinpoints[active]} of the source
                      </p>
                    )}
                    {activeCitation.snippet && (
                      <blockquote className="mt-4 border-t border-rule pt-3 font-text text-[0.875rem] italic leading-relaxed text-ink-soft">
                        {activeCitation.snippet.trim()}
                      </blockquote>
                    )}
                  </div>
                ) : (
                  <div className="border-t border-rule pt-3">
                    <p className="ledger-label">Apparatus</p>
                    <p className="mt-2 font-text text-[0.9375rem] leading-relaxed text-ink-soft">
                      Select a numbered figure in the report to see the source
                      it came from.
                    </p>
                  </div>
                )}
              </div>
            </aside>
          </div>
        )}
      </section>
    </div>
  );
}

function Specimen({ withKeys }: { withKeys: (n: React.ReactNode) => React.ReactNode }) {
  return (
    <div className="pt-6">
      <p className="ledger-label">A specimen, not a result</p>
      <div className="mt-4 grid gap-x-8 lg:grid-cols-[minmax(0,70ch)_16rem]">
        <div className="report max-w-measure">
          <p>
            Every claim carries the figure of the source it came from.{" "}
            {withKeys("[1]")}Select a figure and its source opens beside the text.
          </p>
          <p>
            A report that cannot be checked is an assertion. {withKeys("[2]")}The figure
            is the audit trail, and the sources are the {withKeys("[3]")}evidence.
          </p>
        </div>
        <div className="mt-6 lg:mt-0">
          <p className="font-ui text-[12px] leading-relaxed text-ink-faint">
            Here is where a selected source will open. Yours will name the real
            article and link to it.
          </p>
        </div>
      </div>
      <p className="mt-5 font-ui text-[12px] text-ink-faint">
        Ask a question to replace this with your own.
      </p>
    </div>
  );
}
