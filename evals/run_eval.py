import json
import logging
from datetime import datetime
from pathlib import Path

from agents.planner.agent import plan
from agents.retriever.agent import retrieve
from agents.writer.agent import write
from evals.ragas_config import get_ragas_clients

logger = logging.getLogger(__name__)

RESULTS_DIR = Path("evals/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_pipeline(question: str) -> dict:
    sub_queries = plan(question)
    sources = retrieve(sub_queries, max_results=3)
    report = write(question, sources)
    return {
        "question": question,
        "answer": report,
        "contexts": [s["content"] for s in sources],
        "sources": sources,
    }


def run_ragas_eval(questions: list[str], references: list[str] | None = None):
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
        from ragas.run_config import RunConfig
    except ImportError as e:
        raise ImportError("eval deps missing. Run: uv pip install -e '.[eval]'") from e

    evaluator_llm, evaluator_embeddings = get_ragas_clients()

    logger.info("Running pipeline on %d questions...", len(questions))
    rows: list[dict] = []
    for i, q in enumerate(questions):
        logger.info("[%d/%d] %s", i + 1, len(questions), q[:60])
        result = run_pipeline(q)
        row: dict = {
            "user_input": result["question"],
            "response": result["answer"],
            "retrieved_contexts": result["contexts"],
        }
        if references and i < len(references):
            row["reference"] = references[i]
        rows.append(row)

    dataset = Dataset.from_list(rows)

    metrics = [faithfulness, answer_relevancy, context_precision]
    if references:
        metrics.append(context_recall)

    for m in metrics:
        m.llm = evaluator_llm
    answer_relevancy.embeddings = evaluator_embeddings

    run_config = RunConfig(max_workers=1, timeout=600)

    logger.info("Running RAGAS evaluation...")
    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
        run_config=run_config,
    )

    df = result.to_pandas()

    summary: dict[str, float] = {}
    print("\n" + "=" * 60)
    print("RAGAS EVALUATION RESULTS")
    print("=" * 60)
    for col in df.columns:
        if col not in ["user_input", "response", "retrieved_contexts", "reference"]:
            mean_score = float(df[col].mean())
            summary[col] = round(mean_score, 4)
            print(f"  {col:25s} {mean_score:.4f}")

    print("\nThresholds:")
    faith = "PASS" if summary.get("faithfulness", 0) > 0.8 else "FAIL"
    relev = "PASS" if summary.get("answer_relevancy", 0) > 0.7 else "FAIL"
    prec = "PASS" if summary.get("context_precision", 0) > 0.6 else "FAIL"
    print(f"  Faithfulness > 0.8     {faith}")
    print(f"  Answer Relevancy > 0.7 {relev}")
    print(f"  Context Precision > 0.6{prec}")
    if references:
        rec = "PASS" if summary.get("context_recall", 0) > 0.7 else "FAIL"
        print(f"  Context Recall > 0.7    {rec}")
    print("=" * 60)

    output = {
        "summary": summary,
        "per_sample": df.to_dict(orient="records"),
        "timestamp": datetime.now().isoformat(),
    }
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"eval_{ts}.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults saved to {out_path}")

    return output
