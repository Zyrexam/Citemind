GOLDEN_QUESTIONS = [
    "What is RAG and how does it reduce hallucinations?",
    "What is the difference between machine learning and deep learning?",
    "How do transformers use self-attention?",
    "What are the main evaluation metrics for RAG systems?",
    "What is the role of a vector database in RAG?",
    "How does prompt engineering affect LLM output quality?",
    "What is the difference between fine-tuning and RAG?",
    "What are AI agents and how do they use tools?",
    "How does chunking strategy affect retrieval quality?",
    "What is the purpose of guardrails in AI systems?",
]

GOLDEN_REFERENCES = [
    (
        "RAG combines retrieval with generation, using retrieved documents as context "
        "to ground the LLM's answer and reduce hallucination."
    ),
    "Deep learning is a subset of machine learning that uses multi-layer neural networks.",
    (
        "Transformers use self-attention to process all positions in parallel, "
        "unlike RNNs which process sequentially."
    ),
    (
        "Core RAGAS metrics: Context Precision, Context Recall (retriever); "
        "Faithfulness, Answer Relevancy (generator)."
    ),
    (
        "A vector database stores embeddings and enables similarity search "
        "over document chunks."
    ),
    (
        "Prompt engineering shapes how LLMs interpret tasks; clear instructions "
        "and examples improve output consistency."
    ),
    (
        "Fine-tuning updates model weights; RAG adds external knowledge "
        "at inference without changing weights."
    ),
    "AI agents use LLMs to reason and call tools to accomplish goals autonomously.",
    (
        "Chunking affects retrieval granularity; smaller chunks improve "
        "precision but may lose context."
    ),
    (
        "Guardrails validate inputs and outputs to prevent prompt injection, "
        "PII leakage, and malformed responses."
    ),
]
