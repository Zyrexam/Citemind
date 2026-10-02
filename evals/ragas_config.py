import logging

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.integrations.langchain import LangchainLLMWrapper

from core.config import settings

logger = logging.getLogger(__name__)


def get_ragas_clients():

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
