"""
core/vectorstore.py — ChromaDB vector store manager.

Handles document ingestion (load → chunk → embed → store) and
similarity search with confidence scores.
"""
from pathlib import Path
from typing import List, Tuple

import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHROMA_DIR,
    COLLECTION_NAME,
    DOCS_DIR,
    TOP_K,
)
from core.embeddings import get_embeddings


def _load_documents() -> List[Document]:
    """Load all PDF files from the documents directory."""
    from langchain_community.document_loaders import PyPDFLoader

    docs = []
    pdf_files = list(Path(DOCS_DIR).glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in {DOCS_DIR}. "
            "Please convert your documents to PDF format and place them in data/documents/"
        )

    for pdf_file in pdf_files:
        loader = PyPDFLoader(str(pdf_file))
        pages = loader.load()  # returns one Document per page
        for page in pages:
            # PyPDFLoader already sets page_content and metadata.source
            # normalise source to just the filename
            page.metadata["source"] = pdf_file.name
        docs.extend(pages)
        print(f"  Loaded {len(pages)} pages from {pdf_file.name}")

    return docs


def _chunk_documents(docs: List[Document]) -> List[Document]:
    """Split documents into overlapping chunks, preserving section context."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        # split at double newlines first, then single newlines, then words
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for doc in docs:
        split_chunks = splitter.split_text(doc.page_content)
        for i, chunk in enumerate(split_chunks):
            # try to extract a heading from the chunk text (works for structured PDFs)
            heading = ""
            for line in chunk.split("\n")[:5]:  # check first 5 lines
                stripped = line.strip()
                if stripped and len(stripped) < 80 and not stripped.endswith("."):
                    heading = stripped
                    break
            chunks.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": doc.metadata.get("source", "unknown"),
                        "page": doc.metadata.get("page", 0),
                        "section": heading or f"chunk_{i}",
                        "chunk_index": i,
                    },
                )
            )
    return chunks


def get_vectorstore() -> Chroma:
    """Return (or create) the ChromaDB vector store."""
    embeddings = get_embeddings()
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    vectorstore = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )

    # ingest documents if collection is empty
    collection = client.get_or_create_collection(COLLECTION_NAME)
    if collection.count() == 0:
        print("Ingesting documents into ChromaDB...")
        raw_docs = _load_documents()
        chunks = _chunk_documents(raw_docs)
        vectorstore.add_documents(chunks)
        print(f"Ingested {len(chunks)} chunks from {len(raw_docs)} documents.")

    return vectorstore


def similarity_search_with_scores(
    query: str, k: int = TOP_K
) -> List[Tuple[Document, float]]:
    """
    Run similarity search and return (document, score) pairs.
    Score is cosine similarity in [0, 1] — higher is better.
    """
    vs = get_vectorstore()
    # returns list of (Document, distance) where distance is in [0, 2] for cosine
    results = vs.similarity_search_with_score(query, k=k)

    # convert cosine distance to similarity: similarity = 1 - distance/2
    scored = []
    for doc, distance in results:
        similarity = max(0.0, 1.0 - distance / 2.0)
        scored.append((doc, round(similarity, 4)))

    return scored
