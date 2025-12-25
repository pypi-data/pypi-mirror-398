import tempfile
from pathlib import Path
from typing import List, Optional

from mielto.knowledge.chunking.strategy import ChunkingStrategy
from mielto.knowledge.document.base import Document
from mielto.utils.log import log_debug, log_error, log_warning

try:
    from docling.chunking import HybridChunker
    from docling.document_converter import DocumentConverter
except ImportError:
    raise ImportError(
        "`docling` is required for hybrid chunking. "
        "Please install it using `pip install docling` to use HybridChunking."
    )

try:
    from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
    from transformers import AutoTokenizer
except ImportError:
    HuggingFaceTokenizer = None
    AutoTokenizer = None


class HybridChunking(ChunkingStrategy):
    """Chunking strategy that uses docling's HybridChunker for tokenization-aware hierarchical chunking."""

    def __init__(
        self,
        chunk_size: int = 5000,
        tokenizer_model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        merge_peers: bool = True,
    ):
        """
        Initialize HybridChunking.

        Args:
            chunk_size: Target chunk size in characters (used as fallback if tokenizer not provided)
            tokenizer_model: HuggingFace model ID for tokenization (e.g., "sentence-transformers/all-MiniLM-L6-v2").
                           If None, uses default tokenizer.
            max_tokens: Maximum tokens per chunk. If None and tokenizer_model is provided, derived from tokenizer.
            merge_peers: Whether to merge undersized peer chunks. Defaults to True.
        """
        self.chunk_size = chunk_size
        self.tokenizer_model = tokenizer_model
        self.max_tokens = max_tokens
        self.merge_peers = merge_peers
        self.chunker = None
        self._initialize_chunker()

    def _initialize_chunker(self):
        """Lazily initialize the HybridChunker with optional tokenizer."""
        if self.chunker is None:
            tokenizer = None

            # If tokenizer_model is provided, create a HuggingFace tokenizer
            if self.tokenizer_model and HuggingFaceTokenizer and AutoTokenizer:
                try:
                    hf_tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_model)
                    tokenizer = HuggingFaceTokenizer(
                        tokenizer=hf_tokenizer,
                        max_tokens=self.max_tokens,  # Will be derived from tokenizer if None
                    )
                    log_debug(f"Initialized HuggingFace tokenizer: {self.tokenizer_model}")
                except Exception as e:
                    log_warning(f"Failed to initialize tokenizer {self.tokenizer_model}: {e}. Using default.")
            elif self.tokenizer_model:
                log_warning(
                    "Tokenizer model specified but transformers/docling-core not available. "
                    "Install with: pip install transformers docling-core"
                )

            # Initialize HybridChunker
            chunker_kwargs = {"merge_peers": self.merge_peers}
            if tokenizer:
                chunker_kwargs["tokenizer"] = tokenizer

            self.chunker = HybridChunker(**chunker_kwargs)
            log_debug("Initialized HybridChunker")

    def _get_docling_document(self, document: Document):
        """
        Get or create a DoclingDocument from the input Document.

        Args:
            document: Mielto Document object

        Returns:
            DoclingDocument object
        """
        # Check if docling document is stored in metadata
        if document.meta_data and "docling_document" in document.meta_data:
            return document.meta_data["docling_document"]

        # Try to create DoclingDocument from text content
        # DocumentConverter needs a file source, so we'll create a temporary file
        log_debug("Creating DoclingDocument from text content")
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp_file:
                tmp_file.write(document.content)
                tmp_path = tmp_file.name

            try:
                converter = DocumentConverter()
                result = converter.convert(source=tmp_path)
                docling_doc = result.document
                log_debug("Successfully created DoclingDocument from text")
                return docling_doc
            finally:
                # Clean up temporary file
                Path(tmp_path).unlink(missing_ok=True)
        except Exception as e:
            log_error(f"Failed to create DoclingDocument from text: {e}")
            raise ValueError(
                f"Could not create DoclingDocument for hybrid chunking. "
                f"Ensure the document content is valid text. Error: {e}"
            )

    def chunk(self, document: Document) -> List[Document]:
        """
        Split document into chunks using docling's HybridChunker.

        Args:
            document: Document to chunk

        Returns:
            List of chunked Document objects
        """
        if not document.content or len(document.content.strip()) == 0:
            return [document]

        try:
            # Get or create DoclingDocument
            docling_doc = self._get_docling_document(document)

            # Chunk using HybridChunker
            chunk_iter = self.chunker.chunk(dl_doc=docling_doc)

            # Convert chunks to Mielto Documents
            chunks: List[Document] = []
            chunk_meta_data = document.meta_data.copy() if document.meta_data else {}
            chunk_number = 1

            for chunk in chunk_iter:
                # Get the contextualized text (metadata-enriched)
                chunk_text = self.chunker.contextualize(chunk=chunk)

                # Create chunk ID
                chunk_id = None
                if document.id:
                    chunk_id = f"{document.id}_{chunk_number}"
                elif document.name:
                    chunk_id = f"{document.name}_{chunk_number}"

                # Create metadata for chunk
                meta_data = chunk_meta_data.copy()
                meta_data["chunk"] = chunk_number
                meta_data["chunk_size"] = len(chunk_text)

                # Create Document for chunk
                chunks.append(
                    Document(
                        id=chunk_id,
                        name=document.name,
                        meta_data=meta_data,
                        content=chunk_text,
                        embedder=document.embedder,
                        content_id=document.content_id,
                        content_origin=document.content_origin,
                    )
                )
                chunk_number += 1

            log_debug(f"Hybrid chunking created {len(chunks)} chunks from document")
            return chunks if chunks else [document]

        except Exception as e:
            log_error(f"Error during hybrid chunking: {e}")
            # Fallback: return original document if chunking fails
            log_warning("Falling back to returning original document due to chunking error")
            return [document]
