"""Advanced RAG Service - Hybrid search, re-ranking, and multi-query retrieval."""

from typing import Dict, List, Optional, Tuple

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.config import get_settings
from app.services.rag_service import get_rag_service
from app.utils.logger import get_logger
from app.utils.token_counter import count_tokens

logger = get_logger(__name__)
settings = get_settings()


class AdvancedRAGService:
    """Enhanced RAG with hybrid search, re-ranking, and context compression."""

    def __init__(self):
        self.rag_service = get_rag_service()
        self.bm25_corpus: List[List[str]] = []
        self.bm25_documents: List[Document] = []
        self.bm25_index: Optional[BM25Okapi] = None

    def build_bm25_index(self, documents: List[Document]) -> None:
        """Build BM25 index from documents for keyword search."""
        self.bm25_documents = documents
        self.bm25_corpus = [doc.page_content.lower().split() for doc in documents]
        if self.bm25_corpus:
            self.bm25_index = BM25Okapi(self.bm25_corpus)
            logger.info(f"Built BM25 index with {len(documents)} documents")

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> List[Tuple[Document, float]]:
        """Perform hybrid search combining semantic and keyword retrieval.

        Args:
            query: Search query
            top_k: Number of results
            semantic_weight: Weight for semantic (FAISS) results
            keyword_weight: Weight for keyword (BM25) results

        Returns:
            List of (document, score) tuples
        """
        results: Dict[str, Tuple[Document, float]] = {}

        # Semantic search (FAISS)
        semantic_results = await self.rag_service.retrieve_with_scores(query, top_k=top_k)
        for doc, score in semantic_results:
            doc_id = doc.page_content[:100]  # Use content prefix as ID
            normalized_score = 1 / (1 + score)  # Convert distance to similarity
            results[doc_id] = (doc, normalized_score * semantic_weight)

        # Keyword search (BM25)
        if self.bm25_index and self.bm25_corpus:
            tokenized_query = query.lower().split()
            bm25_scores = self.bm25_index.get_scores(tokenized_query)

            # Normalize BM25 scores
            max_score = max(bm25_scores) if max(bm25_scores) > 0 else 1
            for i, score in enumerate(bm25_scores):
                if score > 0:
                    doc = self.bm25_documents[i]
                    doc_id = doc.page_content[:100]
                    normalized_score = score / max_score
                    if doc_id in results:
                        results[doc_id] = (
                            results[doc_id][0],
                            results[doc_id][1] + normalized_score * keyword_weight,
                        )
                    else:
                        results[doc_id] = (doc, normalized_score * keyword_weight)

        # Sort by combined score
        sorted_results = sorted(results.values(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

    async def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 5,
    ) -> List[Document]:
        """Re-rank documents using cross-encoder scoring.

        Uses a simple relevance scoring approach.
        For production, integrate sentence-transformers CrossEncoder.
        """
        if not documents:
            return []

        # Score each document based on query term overlap and position
        scored_docs = []
        query_terms = set(query.lower().split())

        for doc in documents:
            content_lower = doc.page_content.lower()
            content_terms = set(content_lower.split())

            # Term overlap score
            overlap = len(query_terms & content_terms)
            overlap_score = overlap / max(len(query_terms), 1)

            # Exact phrase match bonus
            phrase_bonus = 1.0 if query.lower() in content_lower else 0.0

            # Length penalty (prefer concise, relevant chunks)
            length_penalty = min(1.0, 500 / max(len(doc.page_content), 1))

            score = overlap_score * 0.5 + phrase_bonus * 0.3 + length_penalty * 0.2
            scored_docs.append((doc, score))

        # Sort by score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored_docs[:top_k]]

    async def multi_query_retrieve(
        self,
        query: str,
        num_queries: int = 3,
        top_k: int = 5,
    ) -> List[Document]:
        """Generate multiple query variations and retrieve for each.

        This improves recall by capturing different aspects of the query.
        """
        # Generate query variations
        variations = self._generate_query_variations(query, num_queries)

        # Retrieve for each variation
        all_docs: Dict[str, Document] = {}
        for variation in variations:
            docs = await self.rag_service.retrieve(variation, top_k=top_k)
            for doc in docs:
                doc_id = doc.page_content[:100]
                if doc_id not in all_docs:
                    all_docs[doc_id] = doc

        # Re-rank combined results
        return await self.rerank(query, list(all_docs.values()), top_k=top_k)

    def _generate_query_variations(self, query: str, num_variations: int) -> List[str]:
        """Generate simple query variations for multi-query retrieval."""
        variations = [query]

        # Add question form
        if not query.endswith("?"):
            variations.append(f"What is {query}?")

        # Add keyword extraction
        words = query.split()
        if len(words) > 3:
            # Use key terms
            variations.append(" ".join(words[:3]))

        return variations[:num_variations]

    async def compress_context(
        self,
        documents: List[Document],
        max_tokens: int = 3000,
    ) -> str:
        """Compress retrieved context to fit within token budget."""
        context_parts = []
        total_tokens = 0

        for i, doc in enumerate(documents):
            doc_tokens = count_tokens(doc.page_content)
            if total_tokens + doc_tokens > max_tokens:
                # Truncate this document to fit
                remaining_budget = max_tokens - total_tokens
                if remaining_budget > 50:  # Only include if meaningful
                    truncated = doc.page_content[:remaining_budget * 4]  # Approximate
                    context_parts.append(f"[Source {i+1}]\n{truncated}...")
                break

            source = doc.metadata.get("source", "Unknown")
            context_parts.append(f"[Source {i+1}: {source}]\n{doc.page_content}")
            total_tokens += doc_tokens

        return "\n\n".join(context_parts)

    async def retrieve_and_generate_context(
        self,
        query: str,
        use_hybrid: bool = True,
        use_reranking: bool = True,
        max_tokens: int = 3000,
    ) -> str:
        """Full advanced retrieval pipeline.

        1. Hybrid search (semantic + keyword)
        2. Re-ranking
        3. Context compression
        """
        if use_hybrid and self.bm25_index:
            results = await self.hybrid_search(query, top_k=10)
            documents = [doc for doc, _ in results]
        else:
            documents = await self.rag_service.retrieve(query, top_k=10)

        if use_reranking and documents:
            documents = await self.rerank(query, documents, top_k=5)

        return await self.compress_context(documents, max_tokens=max_tokens)


# Singleton
_advanced_rag_service: Optional[AdvancedRAGService] = None


def get_advanced_rag_service() -> AdvancedRAGService:
    """Get or create advanced RAG service singleton."""
    global _advanced_rag_service
    if _advanced_rag_service is None:
        _advanced_rag_service = AdvancedRAGService()
    return _advanced_rag_service
