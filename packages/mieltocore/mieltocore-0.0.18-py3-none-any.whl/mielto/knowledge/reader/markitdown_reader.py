from mielto.knowledge.reader.base import Reader
from mielto.knowledge.document.base import Document
from mielto.utils.common import generate_prefix_ulid
from typing import Union, Optional, List, IO, Any
from pathlib import Path
from mielto.knowledge.chunking.strategy import ChunkingStrategyType

try:
    from markitdown import MarkItDown
except ImportError:
    raise ImportError(
        "MarkItDown not found. Please install using `pip install markitdown`"
    )


class MarkItDownReader(Reader):
    """Reader that uses MarkItDown to convert various file formats to markdown."""

    @classmethod
    def get_supported_chunking_strategies(cls) -> List[ChunkingStrategyType]:
        """Get the list of supported chunking strategies for MarkItDown readers."""
        return [
            ChunkingStrategyType.DOCUMENT_CHUNKER,
            ChunkingStrategyType.FIXED_SIZE_CHUNKER,
            ChunkingStrategyType.AGENTIC_CHUNKER,
            ChunkingStrategyType.SEMANTIC_CHUNKER,
            ChunkingStrategyType.RECURSIVE_CHUNKER
        ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.converter = MarkItDown()

    def get_supported_extensions(self) -> List[str]:
        """Get list of file extensions supported by MarkItDown."""
        return [
            ".pdf", ".docx", ".doc", ".pptx", ".ppt", 
            ".xlsx", ".xls", ".html", ".htm", ".txt",
            ".csv", ".json", ".xml", ".md", ".epub",
            ".odt", ".rtf", ".jpg", ".jpeg", ".png"
        ]

    def _validate_file(self, file: Union[Path, IO[Any], str]) -> Path:
        """Validate that the file exists and has a supported extension."""
        path = Path(file) if not isinstance(file, Path) else file
        
        if not path.exists():
            raise ValueError(f"File not found: {file}")
        
        extension = path.suffix.lower()
        supported_extensions = self.get_supported_extensions()
        
        if extension not in supported_extensions:
            raise ValueError(
                f"Unsupported file type: {extension}. "
                f"Supported types: {', '.join(supported_extensions)}"
            )
        
        return path

    def _convert_to_markdown(self, file_path: Path) -> str:
        """Convert file to markdown using MarkItDown."""
        try:
            result = self.converter.convert(str(file_path))
            return result.text_content if hasattr(result, 'text_content') else str(result)
        except Exception as e:
            raise ValueError(f"Failed to convert file to markdown: {e}")

    def _build_chunked_documents(self, documents: List[Document]) -> List[Document]:
        """Build chunked documents from a list of documents."""
        chunked_documents: List[Document] = []
        for document in documents:
            chunked_documents.extend(self.chunk_document(document))
        return chunked_documents

    def _create_document(
        self, 
        content: str, 
        name: Optional[str] = None, 
        metadata: Optional[dict] = None
    ) -> Document:
        """Create a Document object from markdown content."""
        return Document(
            name=name,
            id=generate_prefix_ulid("chunk"),
            content=content,
            meta_data=metadata or {}
        )

    def _create_documents(
        self, 
        markdown_content: str, 
        name: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> List[Document]:
        """Create documents from markdown content."""
        doc = self._create_document(markdown_content, name, metadata)

        if self.extract:
            doc = self.extract_content([doc])[0]
        
        if self.chunk:
            return self._build_chunked_documents([doc])
        return [doc]

    def read(
        self, 
        file: Union[Path, IO[Any], str], 
        name: Optional[str] = None, 
        password: Optional[str] = None
    ) -> List[Document]:
        """
        Read a file and convert it to Document objects.
        
        Args:
            file: Path to the file or file-like object
            name: Optional name for the document
            password: Optional password (not used by MarkItDown but kept for interface compatibility)
            
        Returns:
            List of Document objects
        """
        # Validate file
        file_path = self._validate_file(file)
        
        # Convert to markdown
        markdown_content = self._convert_to_markdown(file_path)
        
        # Prepare metadata
        metadata = {
            "source": str(file_path),
            "file_name": file_path.name,
            "file_type": file_path.suffix.lower()
        }
        
        # Create documents
        return self._create_documents(
            markdown_content, 
            name=name or file_path.name, 
            metadata=metadata
        )

    async def async_read(
        self, 
        file: Union[Path, IO[Any], str], 
        name: Optional[str] = None, 
        password: Optional[str] = None
    ) -> List[Document]:
        """
        Async version of read method.
        
        Note: MarkItDown doesn't have async support, so this calls the sync version.
        
        Args:
            file: Path to the file or file-like object
            name: Optional name for the document
            password: Optional password (not used by MarkItDown but kept for interface compatibility)
            
        Returns:
            List of Document objects
        """
        # MarkItDown doesn't have native async support, so we call the sync version
        # In the future, this could be wrapped with asyncio.to_thread for true async behavior
        return self.read(file, name, password)
