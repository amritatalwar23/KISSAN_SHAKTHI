"""Agricultural Knowledge Base and Retrieval-Augmented Generation (RAG) Service.

Ingests verified institutional publications (ICAR, IIHR, CPRI, SAUs),
indexes document chunks using dense/TF-IDF vector representations,
retrieves relevant context with confidence thresholding, and attributes exact sources.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.core.config import settings
from backend.app.core.logging import logger


class RAGService:
    def __init__(self):
        self.doc_file = Path(settings.KNOWLEDGE_BASE_DIR) / "icar_advisories.json"
        self.documents: List[Dict[str, Any]] = []
        self.chunks: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.doc_vectors = None
        self.similarity_threshold = 0.18

        self._load_and_index_documents()

    def _load_and_index_documents(self):
        """Loads documented institutional publications and builds the vector search index."""
        if not self.doc_file.exists():
            logger.warning(f"RAG document store not found at {self.doc_file}")
            return

        try:
            with open(self.doc_file, "r", encoding="utf-8") as f:
                self.documents = json.load(f)

            # Chunk documents (each paragraph or segmented advisory)
            self.chunks = []
            for doc in self.documents:
                content = doc.get("content", "")
                # Clean and split into coherent chunks
                sentences = content.split(". ")
                chunk_size = 3
                for i in range(0, len(sentences), chunk_size):
                    chunk_text = ". ".join(sentences[i:i + chunk_size]).strip()
                    if not chunk_text.endswith("."):
                        chunk_text += "."
                    if len(chunk_text) > 40:
                        self.chunks.append({
                            "title": doc.get("title", ""),
                            "content": chunk_text,
                            "source": doc.get("source", ""),
                            "publication": doc.get("publication_year", "Recent"),
                            "category": doc.get("category", "General")
                        })

            if self.chunks:
                corpus = [f"{c['title']} {c['content']}" for c in self.chunks]
                self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
                self.doc_vectors = self.vectorizer.fit_transform(corpus)
                logger.info(f"RAG index initialized with {len(self.chunks)} chunks from {len(self.documents)} publications.")
        except Exception as e:
            logger.error(f"Failed to build RAG index: {e}")

    def query(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """Retrieves most relevant knowledge chunks and constructs a source-attributed response."""
        if not question or not self.chunks or self.vectorizer is None or self.doc_vectors is None:
            return {
                "question": question,
                "retrieved_chunks": [],
                "grounded_answer": "Knowledge base index is currently unpopulated or question was empty.",
                "sufficient_evidence": False,
                "sources": []
            }

        try:
            q_vec = self.vectorizer.transform([question])
            scores = cosine_similarity(q_vec, self.doc_vectors)[0]
            top_indices = np.argsort(scores)[::-1][:top_k]

            retrieved = []
            sources = []
            for idx in top_indices:
                score = float(scores[idx])
                if score >= self.similarity_threshold:
                    chunk = self.chunks[idx].copy()
                    chunk["retrieval_score"] = round(score, 3)
                    retrieved.append(chunk)
                    src = f"{chunk['source']} ({chunk['publication']})"
                    if src not in sources:
                        sources.append(src)

            if not retrieved:
                return {
                    "question": question,
                    "retrieved_chunks": [],
                    "grounded_answer": (
                        "I could not verify official recommendations for this specific query within the current "
                        "ICAR/KVK advisory repository. Please consult your local Krishi Vigyan Kendra specialist "
                        "or call the national Kisan Call Centre at 1800-180-1551 for certified advice."
                    ),
                    "sufficient_evidence": False,
                    "sources": []
                }

            # Synthesize grounded answer
            best_chunk = retrieved[0]
            answer_parts = [
                f"**Based on verified guidance from {best_chunk['source']}:**\n",
                best_chunk['content']
            ]

            if len(retrieved) > 1:
                answer_parts.append(f"\n\n**Additional Protocol ({retrieved[1]['title']}):**\n{retrieved[1]['content']}")

            grounded_answer = "\n".join(answer_parts)

            return {
                "question": question,
                "retrieved_chunks": retrieved,
                "grounded_answer": grounded_answer,
                "sufficient_evidence": True,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"RAG query execution failed: {e}")
            return {
                "question": question,
                "retrieved_chunks": [],
                "grounded_answer": f"Error retrieving agricultural knowledge: {str(e)}",
                "sufficient_evidence": False,
                "sources": []
            }


rag_service = RAGService()
