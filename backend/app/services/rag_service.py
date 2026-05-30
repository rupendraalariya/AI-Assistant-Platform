"""RAG Service - Document retrieval and context injection pipeline."""

import os
from typing import Dict, List, Optional

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RAGService:
    """Retrieval-Augmented Generation service with FAISS vector store."""

    def __init__(self):
        self._embeddings = None
        self._text_splitter = None
        self.vector_store = None
        self._initialized = False

    def _initialize(self):
        """Lazy initialization of heavy ML components."""
        if self._initialized:
            return
        try:
            # Newer langchain moved the splitter to langchain_text_splitters
            try:
                from langchain_text_splitters import RecursiveCharacterTextSplitter
            except ImportError:
                from langchain.text_splitter import RecursiveCharacterTextSplitter
            from langchain_huggingface import HuggingFaceEmbeddings

            self._embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
            self._load_existing_index()
            self._initialized = True
            logger.info("[RAG] Service initialized with embeddings + splitter")
        except ImportError as e:
            logger.warning(f"[RAG] dependencies not installed: {e}")
            self._initialized = True

    def _load_existing_index(self) -> None:
        """Load existing FAISS index if available."""
        if not self._embeddings:
            return
        index_path = settings.faiss_index_path
        if os.path.exists(index_path):
            try:
                from langchain_community.vectorstores import FAISS
                self.vector_store = FAISS.load_local(
                    index_path,
                    self._embeddings,
                    allow_dangerous_deserialization=True,
                )
                logger.info("Loaded existing FAISS index", path=index_path)
            except Exception as e:
                logger.warning(f"Failed to load FAISS index: {e}")

    async def ingest_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict]] = None,
    ) -> int:
        """Ingest documents into the vector store."""
        self._initialize()
        if not self._text_splitter or not self._embeddings:
            logger.warning("RAG not available - missing dependencies")
            return 0

        from langchain_community.vectorstores import FAISS

        documents = []
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            chunks = self._text_splitter.create_documents(
                texts=[text],
                metadatas=[metadata],
            )
            documents.extend(chunks)

        if not documents:
            return 0

        logger.info(f"[RAG] Chunks created: {len(documents)}")

        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(documents, self._embeddings)
        else:
            self.vector_store.add_documents(documents)

        logger.info(f"[RAG] Embeddings created & vectors stored: {len(documents)} chunks")
        self._save_index()
        logger.info(f"[RAG] FAISS index persisted ({len(documents)} new chunks)")
        return len(documents)

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict] = None,
    ) -> List:
        """Retrieve relevant documents for a query, optionally filtered by metadata."""
        self._initialize()
        if self.vector_store is None:
            logger.debug("[RAG] No vector store available")
            return []

        k = top_k or settings.top_k_results
        try:
            if filter_metadata:
                # Fetch a wider pool then filter by metadata (e.g. user_id/session_id)
                results = self.vector_store.similarity_search(
                    query, k=k, filter=filter_metadata, fetch_k=max(k * 4, 20)
                )
            else:
                results = self.vector_store.similarity_search(query, k=k)
            logger.info(f"[RAG] Retrieved {len(results)} chunks for query (filter={filter_metadata})")
            return results
        except Exception as e:
            logger.error(f"[RAG] Retrieval failed: {e}")
            return []

    async def retrieve_with_scores(self, query: str, top_k: Optional[int] = None) -> List[tuple]:
        """Retrieve documents with relevance scores."""
        self._initialize()
        if self.vector_store is None:
            return []

        k = top_k or settings.top_k_results
        try:
            return self.vector_store.similarity_search_with_score(query, k=k)
        except Exception as e:
            logger.error(f"Scored retrieval failed: {e}")
            return []

    async def get_context_string(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict] = None,
    ) -> str:
        """Get formatted context string for LLM injection."""
        documents = await self.retrieve(query, top_k, filter_metadata)
        if not documents:
            return ""

        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "Unknown")
            context_parts.append(f"[Source {i}: {source}]\n{doc.page_content}")

        context = "\n\n".join(context_parts)
        logger.info(f"[RAG] Injected context: {len(context)} chars from {len(documents)} chunks")
        return context

    def _save_index(self) -> None:
        """Persist FAISS index to disk."""
        if self.vector_store:
            os.makedirs(os.path.dirname(settings.faiss_index_path) or "data", exist_ok=True)
            self.vector_store.save_local(settings.faiss_index_path)

    @property
    def has_documents(self) -> bool:
        """Check if vector store has any documents."""
        self._initialize()
        return self.vector_store is not None


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
