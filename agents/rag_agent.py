"""
agents/rag_agent.py — Document QA using ChromaDB retrieval + LangChain.

"""
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.llm import get_llm
from core.vectorstore import similarity_search_with_scores
from guardrails.confidence import compute_confidence, should_refuse
from config import TOP_K

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an enterprise AI assistant. Answer the user's question using ONLY the provided context.

Rules:
1. Base your answer strictly on the context — do not use outside knowledge or make assumptions
   beyond what is written.
2. If the context fully answers the question, answer directly and concisely.
3. If the context only partially answers the question, answer the part you can and explicitly
   state which part is not covered by the available documents.
4. If the context doesn't contain enough information to answer at all, say: "I don't have enough
   information in the provided documents to answer this question."
5. Do NOT include a "Sources:" line or list filenames yourself — sources are tracked separately.
6. Use bullet points for multi-step processes or lists of conditions.
7. If quoting specific thresholds, amounts, dates, or names, cite them exactly as written in the
   context — do not paraphrase numbers.

Context:
{context}
"""),
    ("human", "{query}")
])


def run_rag_agent(query: str) -> Dict[str, Any]:
    """
    Retrieve relevant document chunks and generate a grounded answer.

    Returns dict with: response, sources, confidence, confidence_label
    """
    # retrieve top-k chunks with similarity scores
    results = similarity_search_with_scores(query, k=TOP_K)

    if not results:
        return {
            "response": "No documents found in the knowledge base. Please ensure documents are ingested.",
            "sources": [],
            "confidence": 0.0,
            "confidence_label": "no_docs",
        }

    # compute confidence from retrieval scores
    scores = [score for _, score in results]
    confidence, label = compute_confidence(scores)

    # refuse if confidence is below threshold
    if should_refuse(confidence):
        return {
            "response": (
                "I don't have enough information in the provided documents to answer "
                "this question confidently. Please check if the topic is covered in the "
                "available documents, or rephrase your question."
            ),
            "sources": [],
            "confidence": confidence,
            "confidence_label": label,
        }

    # build context string from retrieved chunks
    context_parts = []
    sources = []
    for doc, score in results:
        src = doc.metadata.get("source", "unknown")
        section = doc.metadata.get("section", "")
        context_parts.append(f"[Source: {src}, Section: {section}]\n{doc.page_content}")
        source_entry = {"file": src, "section": section, "score": score}
        if source_entry not in sources:
            sources.append(source_entry)

    context = "\n\n---\n\n".join(context_parts)

    # generate answer
    llm = get_llm(temperature=0.0)
    chain = RAG_PROMPT | llm | StrOutputParser()
    response = chain.invoke({"context": context, "query": query})

    return {
        "response": response,
        "sources": sources,
        "confidence": confidence,
        "confidence_label": label,
    }
