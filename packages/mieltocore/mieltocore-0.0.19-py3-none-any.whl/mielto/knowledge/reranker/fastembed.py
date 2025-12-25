from typing import Any, Dict, List, Optional

from mielto.knowledge.document import Document
from mielto.knowledge.reranker.base import Reranker
from mielto.utils.log import logger

try:
    from fastembed.rerank.cross_encoder import TextCrossEncoder
except ImportError:
    raise ImportError("fastembed not installed, please run `pip install fastembed`")


class FastEmbedReranker(Reranker):
    model: str = "jinaai/jina-reranker-v2-base-multilingual"
    model_kwargs: Optional[Dict[str, Any]] = None
    top_n: Optional[int] = None
    _reranker: Optional[TextCrossEncoder] = None

    @property
    def reranker(self) -> TextCrossEncoder:
        """Get or create the FastEmbed reranker instance"""
        if self._reranker is None:
            kwargs = self.model_kwargs or {}
            self._reranker = TextCrossEncoder(model_name=self.model, **kwargs)
        return self._reranker

    def _rerank(self, query: str, documents: List[Document]) -> List[Document]:
        if not documents:
            return []

        top_n = self.top_n
        if top_n and not (0 < top_n):
            logger.warning(f"top_n should be a positive integer, got {self.top_n}, setting top_n to None")
            top_n = None

        compressed_docs: list[Document] = []

        # Extract document contents for reranking
        doc_contents = [doc.content for doc in documents]

        # Perform reranking - FastEmbed returns scores in the same order as documents
        results = list(self.reranker.rerank(query=query, documents=doc_contents))

        # Process results - scores are returned in the same order as input documents
        # FastEmbed may return scores directly or RerankResult objects
        for index, result in enumerate(results):
            if index < len(documents):
                doc = documents[index]
                # Extract score from result (could be a number or an object with score attribute)
                if hasattr(result, 'score'):
                    score = result.score
                elif hasattr(result, 'relevance_score'):
                    score = result.relevance_score
                else:
                    score = result
                doc.reranking_score = float(score) if not isinstance(score, float) else score
                compressed_docs.append(doc)

        # Sort by relevance score (descending)
        compressed_docs.sort(
            key=lambda x: x.reranking_score if x.reranking_score is not None else float("-inf"),
            reverse=True,
        )

        # Limit to top_n if specified
        if top_n:
            compressed_docs = compressed_docs[:top_n]

        return compressed_docs

    def rerank(self, query: str, documents: List[Document]) -> List[Document]:
        try:
            return self._rerank(query=query, documents=documents)
        except Exception as e:
            logger.error(f"Error reranking documents: {e}. Returning original documents")
            return documents

