import logging

from core.config import settings

logger = logging.getLogger(__name__)


def get_ragas_clients():
    try:
        from langchain_groq import ChatGroq
        from langchain_huggingface import HuggingFaceEmbeddings
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from ragas.llms import LangchainLLMWrapper
    except ImportError as e:
        raise ImportError(
            "eval deps missing. Run: uv pip install -e '.[eval]'"
        ) from e

    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY not set. Add it to .env.")

    judge_llm = ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=settings.groq_api_key,
        temperature=0.0,
    )

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    return (
        LangchainLLMWrapper(judge_llm),
        LangchainEmbeddingsWrapper(embeddings),
    )
