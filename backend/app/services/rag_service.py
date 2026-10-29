"""Agricultural Knowledge Base and Retrieval-Augmented Generation (RAG) Service.

Ingests verified institutional publications (ICAR, IIHR, CPRI, SAUs),
indexes document chunks using dense/TF-IDF vector representations,
retrieves relevant context with confidence thresholding, and attributes exact sources.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.core.config import settings
from backend.app.core.logging import logger


class RAGService:
    QUERY_SYNONYMS = {
        "yellow": "chlorosis nutrient deficiency", "yellowing": "chlorosis nutrient deficiency",
        "spots": "lesions blight leaf spot", "spot": "lesions blight leaf spot",
        "worms": "armyworm caterpillar pest", "worm": "armyworm caterpillar pest",
        "pest": "insect armyworm", "insects": "insect armyworm",
        "water": "irrigation drip", "watering": "irrigation drip",
        "fertilizer": "nutrient soil organic carbon", "manure": "organic carbon FYM",
        "claim": "loss report 72 hours crop insurance", "compensation": "loss claim insurance",
        "tomatoes": "tomato", "potatoes": "potato", "maize": "corn maize",
    }

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

    @staticmethod
    def _chat_summary(chunk: Dict[str, Any]) -> str:
        """Turn a retrieved advisory into a short first reply; keep the excerpt for More Info."""
        title = chunk.get("title", "")
        title_lower = title.lower()
        content = chunk.get("content", "")
        if "tomato" in title_lower and "blight" in title_lower:
            return (
                "For tomato blight, early blight often shows ring-shaped brown spots on older leaves; late blight can "
                "spread quickly in cool, wet weather and may show water-soaked dark lesions. Improve airflow and avoid "
                "wetting foliage where practical. Confirm the disease before choosing a treatment; ask your KVK which "
                "product is currently recommended for your crop and area."
            )
        if "potato" in title_lower and "blight" in title_lower:
            return (
                "Potato late blight risk rises in cool, cloudy, wet conditions. Check plants frequently and get local "
                "advice as soon as blighted spots appear; the advisory recommends thorough leaf coverage with a locally "
                "approved treatment and keeping infected tubers out of healthy seed lots."
            )
        if "armyworm" in title_lower:
            return (
                "For fall armyworm in maize, inspect leaf whorls for fresh damage and frass early. The guidance prioritizes "
                "monitoring and early-stage measures; for severe damage, confirm the pest and use only a locally recommended "
                "product at its label rate."
            )
        if "soil health" in title_lower or "micronutrient" in title_lower:
            return (
                "Use your Soil Health Card or a recent soil test to confirm which nutrient is deficient before applying "
                "micronutrients. Yellowing can have several causes, so share the crop, leaf age affected, and soil-test "
                "results for a more specific next step."
            )
        if "drip irrigation" in title_lower or "fertigation" in title_lower:
            return (
                "With drip irrigation, keep emitters clear and adjust water and fertigation to the crop’s growth stage, "
                "soil moisture, and water quality. The retrieved guidance describes stage-based fertigation; ask your KVK "
                "for a crop-specific schedule before changing fertilizer rates."
            )
        if "pmfby" in title_lower or "claim filing" in title_lower:
            return (
                "If your insured crop has suffered a covered loss, report it promptly. The PMFBY guidance says localized "
                "calamity or post-harvest losses should be reported within 72 hours; keep your policy details, photos, and "
                "land information ready and confirm the current process with the insurer or agriculture office."
            )
        # For other material, use a short excerpt rather than presenting a whole
        # source document as if it were a conversational answer.
        sentences = re.split(r"(?<=[.!?])\s+", content.strip())
        excerpt = " ".join(sentences[:2])
        return excerpt if len(excerpt) <= 420 else excerpt[:417].rsplit(" ", 1)[0] + "..."

    def query(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """Retrieves most relevant knowledge chunks and constructs a source-attributed response."""
        if not question or not self.chunks or self.vectorizer is None or self.doc_vectors is None:
            return {
                "question": question,
                "retrieved_chunks": [],
                "grounded_answer": (
                    "I can't answer that reliably because the agricultural knowledge base is unavailable right now. "
                    "Please try again later or contact your local KVK or the Kisan Call Centre at 1800-180-1551."
                ),
                "sufficient_evidence": False,
                "sources": []
            }

        try:
            terms = re.findall(r"[a-z0-9]+", question.lower())
            expanded_question = question + " " + " ".join(
                self.QUERY_SYNONYMS[term] for term in terms if term in self.QUERY_SYNONYMS
            )
            q_vec = self.vectorizer.transform([expanded_question])
            analyzer = self.vectorizer.build_analyzer()
            query_terms = set(analyzer(expanded_question))
            scores = cosine_similarity(q_vec, self.doc_vectors)[0]
            top_indices = np.argsort(scores)[::-1][:top_k]

            retrieved = []
            sources = []
            for idx in top_indices:
                score = float(scores[idx])
                chunk = self.chunks[idx]
                chunk_terms = set(analyzer(f"{chunk['title']} {chunk['content']}"))
                matched_terms = query_terms & chunk_terms
                # One shared word such as a crop name is not enough to treat a
                # generic question as answered by an unrelated disease bulletin.
                enough_topic_overlap = len(query_terms) <= 1 or len(matched_terms) >= 2
                if score >= self.similarity_threshold and enough_topic_overlap:
                    chunk = chunk.copy()
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
                        "I couldn't find a relevant recommendation in the local agricultural guides, so I don't want "
                        "to guess. Share the crop, district, growth stage, and the specific issue (or a clear photo) "
                        "and I can check the available guidance. For field-specific advice, contact your local KVK "
                        "or the Kisan Call Centre at 1800-180-1551."
                    ),
                    "sufficient_evidence": False,
                    "sources": []
                }

            # Synthesize grounded answer
            best_chunk = retrieved[0]
            answer_parts = [
                f"**Relevant guidance: {best_chunk['title']}**\n",
                best_chunk['content'],
                f"\nSource: {best_chunk['source']} ({best_chunk['publication']})."
            ]

            if len(retrieved) > 1:
                answer_parts.append(f"\n\n**Related guidance ({retrieved[1]['title']}):**\n{retrieved[1]['content']}")

            grounded_answer = "\n".join(answer_parts)

            return {
                "question": question,
                "retrieved_chunks": retrieved,
                "grounded_answer": grounded_answer,
                "chat_answer": self._chat_summary(best_chunk),
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
