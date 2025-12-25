import asyncio
from pathlib import Path
from typing import IO, Any, List, Optional, Union

from mielto.knowledge.chunking.strategy import ChunkingStrategyType
from mielto.knowledge.document.base import Document
from mielto.knowledge.reader.base import Reader
from mielto.knowledge.types import ContentType
from mielto.utils.common import generate_prefix_ulid
from mielto.utils.log import log_error, log_info, logger
from langchain_core.documents import Document as LangchainDocument

try:
    from langchain_docling import DoclingLoader
    from langchain_docling.loader import ExportType
except ImportError:
    raise ImportError(
        "`langchain-docling` not installed. Please install it via `pip install langchain-docling`."
    )


class DoclingReader(Reader):
    """Reader for documents using Docling via langchain-docling"""

    def __init__(
        self,
        export_type: Optional[ExportType] = None,
        convert_kwargs: Optional[dict] = None,
        md_export_kwargs: Optional[dict] = None,
        **kwargs,
    ):
        """
        Initialize DoclingReader.

        Args:
            export_type: Export type for Docling (ExportType.DOC_CHUNKS or ExportType.MARKDOWN).
                           Defaults to ExportType.DOC_CHUNKS.
            convert_kwargs: Keyword arguments for Docling conversion process.
            md_export_kwargs: Keyword arguments for Markdown export (used when export_type is MARKDOWN).
            **kwargs: Additional arguments passed to base Reader class.
        """
        super().__init__(**kwargs)
        self.export_type = export_type or ExportType.DOC_CHUNKS
        self.convert_kwargs = convert_kwargs or {}
        self.md_export_kwargs = md_export_kwargs or {}

    @classmethod
    def get_supported_chunking_strategies(cls) -> List[ChunkingStrategyType]:
        """Get the list of supported chunking strategies for Docling readers."""
        return [
            ChunkingStrategyType.DOCUMENT_CHUNKER,
            ChunkingStrategyType.FIXED_SIZE_CHUNKER,
            ChunkingStrategyType.AGENTIC_CHUNKER,
            ChunkingStrategyType.SEMANTIC_CHUNKER,
            ChunkingStrategyType.RECURSIVE_CHUNKER,
            ChunkingStrategyType.HYBRID_CHUNKER,
        ]

    @classmethod
    def get_supported_content_types(cls) -> List[ContentType]:
        """Get the list of supported content types for Docling readers."""
        return [
            ContentType.PDF,
            ContentType.DOCX,
            ContentType.DOC,
            ContentType.FILE,  # Docling supports many file types
        ]

    def _validate_file(self, file: Union[Path, IO[Any], str]) -> Union[str, Path]:
        """Validate and return the file path."""
        if isinstance(file, str):
            # Could be a URL or file path
            if file.startswith(("http://", "https://")):
                return file
            path = Path(file)
        elif isinstance(file, Path):
            path = file
        else:
            # File-like object
            if hasattr(file, "name"):
                path = Path(file.name)
            else:
                raise ValueError(f"Cannot determine path for file object: {file}")

        if not path.exists() and not str(path).startswith(("http://", "https://")):
            raise ValueError(f"File not found: {file}")

        return path if isinstance(file, (Path, str)) and not str(file).startswith(("http://", "https://")) else str(file)

    def _build_chunked_documents(self, documents: List[Document]) -> List[Document]:
        """Build chunked documents from a list of documents."""
        chunked_documents: List[Document] = []
        for document in documents:
            chunked_documents.extend(self.chunk_document(document))
        return chunked_documents

    def _create_documents(
        self, langchain_docs: List[LangchainDocument], name: Optional[str] = None
    ) -> List[Document]:
        """Convert LangChain documents to Mielto Document objects."""
        docs = [
            Document(
                name=name or doc.metadata.get("source") or "docling_document",
                id=generate_prefix_ulid("chunk"),
                content=doc.page_content,
                meta_data=doc.metadata,
            )
            for doc in langchain_docs
        ]

        if self.extract:
            docs =  self.extract_content(docs)

        if self.chunk:
            return self._build_chunked_documents(docs)
        return docs

    def read(
        self, file: Union[Path, IO[Any], str], name: Optional[str] = None, password: Optional[str] = None
    ) -> List[Document]:
        """
        Read a file using Docling and convert it to Document objects.

        Args:
            file: Path to the file, file-like object, or URL string
            name: Optional name for the document
            password: Optional password (not used by Docling but kept for interface compatibility)

        Returns:
            List of Document objects
        """
        print(f"Reading with Docling: {file}")
        try:
            # Validate and get file path
            file_path = self._validate_file(file)

            # Determine document name
            if name:
                doc_name = name
            elif isinstance(file_path, Path):
                doc_name = file_path.stem
            elif isinstance(file_path, str) and not file_path.startswith(("http://", "https://")):
                doc_name = Path(file_path).stem
            else:
                doc_name = "docling_document"

            log_info(f"Reading with Docling: {doc_name}")

            # Create DoclingLoader
            loader = DoclingLoader(
                file_path=[file_path] if not isinstance(file_path, list) else file_path,
                export_type=self.export_type,
                convert_kwargs=self.convert_kwargs,
                md_export_kwargs=self.md_export_kwargs,
            )

            # Load documents
            langchain_docs = loader.load()

            if not langchain_docs:
                log_error(f"No documents extracted from: {file_path}")
                return []

            # Convert to Mielto documents
            return self._create_documents(langchain_docs, name=doc_name)

        except Exception as e:
            logger.error(f"Error reading file with Docling: {e}")
            log_error(f"Error reading file with Docling: {e}")
            return []

    async def async_read(
        self, file: Union[Path, IO[Any], str], name: Optional[str] = None, password: Optional[str] = None
    ) -> List[Document]:
        """
        Async version of read method.

        Args:
            file: Path to the file, file-like object, or URL string
            name: Optional name for the document
            password: Optional password (not used by Docling but kept for interface compatibility)

        Returns:
            List of Document objects
        """
        # DoclingLoader doesn't have native async support, so we wrap the sync call
        return await asyncio.to_thread(self.read, file, name, password)
