import argparse
import logging

from evals.golden_set import GOLDEN_QUESTIONS, GOLDEN_REFERENCES
from evals.run_eval import run_ragas_eval

logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="Number of questions to evaluate")
    parser.add_argument(
        "--with-references", action="store_true", help="Include context_recall"
    )
    args = parser.parse_args()

    questions = GOLDEN_QUESTIONS[: args.limit]
    references = GOLDEN_REFERENCES[: args.limit] if args.with_references else None

    run_ragas_eval(questions, references)


if __name__ == "__main__":
    main()
