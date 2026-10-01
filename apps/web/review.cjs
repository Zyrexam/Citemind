const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const OUT = path.join(__dirname, "..", "..", ".impeccable", "review");
fs.mkdirSync(OUT, { recursive: true });

const REPORT = `## Overview

Retrieval-augmented generation grounds a language model in retrieved documents before it writes [1]. The model is not retrained; instead the relevant passages are placed in the context window at inference time, which makes the answer traceable to specific sources.

## When retrieval beats fine-tuning

Fine-tuning changes what the model *knows* and is the right tool when the behaviour itself is wrong — tone, format, refusal policy [2]. Retrieval changes what the model is *shown*, and is the right tool when the knowledge changes faster than you can retrain [3].

| Approach | Latency | Freshness | Attribution |
| --- | --- | --- | --- |
| Fine-tuning | Low | Stale | Poor |
| Retrieval | Moderate | Current | Good |
| Both | Moderate | Current | Good |

## Cost and complexity

Retrieval adds a pipeline: chunking, embedding, an index, and a reranker [1]. That infrastructure is the real cost, not the token spend. Teams that skip evaluation usually discover the failure at the point a user does [4].`;

const CITATIONS = [
  { title: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", url: "https://arxiv.org/abs/2005.11401" },
  { title: "Fine-Tuning or Retrieval? Choosing the Right Tool", url: "https://www.example.com/choosing" },
  { title: "Keeping a knowledge base current without retraining", url: "https://engineering.example.com/freshness" },
  { title: "Evaluating RAG systems in production", url: "https://www.example.com/rag-eval" },
];

(async () => {
  const browser = await chromium.launch();

  const stub = async (page) => {
    await page.route("**/agent/run", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ report: REPORT, citations: CITATIONS }),
      })
    );
  };

  const shots = [
    { name: "desktop-idle", w: 1440, h: 940, mode: "idle" },
    { name: "desktop-report", w: 1440, h: 940, mode: "report" },
    { name: "mobile-idle", w: 390, h: 844, mode: "idle" },
    { name: "mobile-report", w: 390, h: 844, mode: "report" },
  ];

  for (const s of shots) {
    const page = await browser.newPage({ viewport: { width: s.w, height: s.h }, deviceScaleFactor: 2 });
    await stub(page);
    await page.goto("http://localhost:3000/", { waitUntil: "networkidle" });
    await page.waitForTimeout(700);

    if (s.mode === "report") {
      await page.fill("textarea", "What are the tradeoffs between retrieval and fine-tuning for enterprise question answering?");
      await page.click('button[type="submit"]');
      await page.waitForSelector(".report p", { timeout: 15000 });
      await page.waitForTimeout(400);
      // open a source so the margin column is exercised
      await page.hover(".report .key >> nth=0");
      await page.waitForTimeout(300);
    }

    await page.screenshot({ path: path.join(OUT, `${s.name}.png`), fullPage: s.mode === "report" });
    await page.close();
  }

  await browser.close();
  console.log("shots written to", OUT);
})();
