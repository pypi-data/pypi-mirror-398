import os
from typing import Any, Callable, Dict, List, Optional

from mielto.knowledge.reader.base import Reader
from mielto.knowledge.reader.langchain_reader import LangchainFileReader

class ReaderFactory:
    """Factory for creating and managing document readers with lazy loading."""

    # Cache for instantiated readers
    _reader_cache: Dict[str, Reader] = {}

    @classmethod
    def _get_pdf_reader(cls, **kwargs) -> Reader:
        """Get PDF reader instance."""
        from mielto.knowledge.reader.pdf_reader import PDFReader

        provider = kwargs.get("provider", "native")

        print(f"Getting PDF reader: {kwargs}")

        config: Dict[str, Any] = {
            "chunk": kwargs.get("chunk", True),
            "chunk_size": kwargs.get("chunk_size", 512),
            "chunking_strategy": kwargs.get("chunking_strategy", None),
            "extract": kwargs.get("extract", None),
            "loader_type": kwargs.get("loader_type", None),
            "description": "Processes PDF documents with OCR support for images and text extraction",
        }
        if kwargs.get("chunking_strategy"):
            config["chunking_strategy"] = kwargs.get("chunking_strategy")
            
        if provider == "langchain":
            return LangchainFileReader(**config)
        elif provider == "docling":
            from mielto.knowledge.reader.docling_reader import DoclingReader
            return DoclingReader(**config)
        return PDFReader(**config)

    @classmethod
    def _get_csv_reader(cls, **kwargs) -> Reader:
        """Get CSV reader instance."""
        from mielto.knowledge.reader.csv_reader import CSVReader


        config: Dict[str, Any] = {
            "name": "CSV Reader",
            "chunk": kwargs.get("chunk", True),
            "chunk_size": kwargs.get("chunk_size", 512),
            "extract": kwargs.get("extract", None),
            "description": "Parses CSV, XLSX, and XLS files with custom delimiter support",
        }
        if kwargs.get("chunking_strategy"):
            config["chunking_strategy"] = kwargs.get("chunking_strategy")
       
        # config.update(kwargs)
        return CSVReader(**config)

    @classmethod
    def _get_docx_reader(cls, **kwargs) -> Reader:
        """Get Docx reader instance."""
        from mielto.knowledge.reader.docx_reader import DocxReader

        provider = kwargs.get("provider", "native")


        config: Dict[str, Any] = {
            "name": "Docx Reader",
            "chunk": kwargs.get("chunk", True),
            "chunk_size": kwargs.get("chunk_size", 512),
            "extract": kwargs.get("extract", None),
            "description": "Extracts text content from Microsoft Word documents (.docx and .doc formats)",
        }
        if provider == "langchain":
            return LangchainFileReader(**config)
        elif provider == "docling":
            from mielto.knowledge.reader.docling_reader import DoclingReader
            return DoclingReader(**config)

        # config.update(kwargs)
        return DocxReader(**config)

    @classmethod
    def _get_json_reader(cls, **kwargs) -> Reader:
        """Get JSON reader instance."""
        from mielto.knowledge.reader.json_reader import JSONReader
        provider = kwargs.get("provider", "native")

        if kwargs.get("provider"):
            del kwargs["provider"]

        config: Dict[str, Any] = {
            "name": "JSON Reader",
            "chunk": kwargs.get("chunk", True),
            "chunk_size": kwargs.get("chunk_size", 512),
            "extract": kwargs.get("extract", None),
            "description": "Processes JSON data structures and API responses with nested object handling",
        }
        if kwargs.get("chunking_strategy"):
            config["chunking_strategy"] = kwargs.get("chunking_strategy")
        # config.update(kwargs)
        return JSONReader(**config)

    @classmethod
    def _get_markdown_reader(cls, **kwargs) -> Reader:
        """Get Markdown reader instance."""
        from mielto.knowledge.reader.markdown_reader import MarkdownReader

        config: Dict[str, Any] = {
            "name": "Markdown Reader",
            "chunk": kwargs.get("chunk", True),
            "chunk_size": kwargs.get("chunk_size", 512),
            "extract": kwargs.get("extract", None),
            "description": "Processes Markdown documentation with header-aware chunking and formatting preservation",
        }
        if kwargs.get("chunking_strategy"):
            config["chunking_strategy"] = kwargs.get("chunking_strategy")
        # config.update(kwargs)
        return MarkdownReader(**config)

    @classmethod
    def _get_text_reader(cls, **kwargs) -> Reader:
        """Get Text reader instance."""
        from mielto.knowledge.reader.text_reader import TextReader

        config: Dict[str, Any] = {
            "name": "Text Reader",
            "chunk": kwargs.get("chunk", True),
            "chunk_size": kwargs.get("chunk_size", 512),
            "extract": kwargs.get("extract", None),
            "description": "Handles plain text files with customizable chunking strategies and encoding detection",
        }
        # config.update(kwargs)
        return TextReader(**config)

    @classmethod
    def _get_website_reader(cls, **kwargs) -> Reader:
        """Get Website reader instance."""
        from mielto.knowledge.reader.website_reader import WebsiteReader

        config: Dict[str, Any] = {
            "name": "Website Reader",
            "chunk": kwargs.get("chunk", True),
            "chunk_size": kwargs.get("chunk_size", 512),
            "extract": kwargs.get("extract", None),
            "description": "Scrapes and extracts content from web pages with HTML parsing and text cleaning",
        }
        config.update(kwargs)
        return WebsiteReader(**config)

    @classmethod
    def _get_firecrawl_reader(cls, **kwargs) -> Reader:
        """Get Firecrawl reader instance."""
        from mielto.knowledge.reader.firecrawl_reader import FirecrawlReader

        config: Dict[str, Any] = {
            "api_key": kwargs.get("api_key") or os.getenv("FIRECRAWL_API_KEY"),
            "mode": "crawl",
            "name": "Firecrawl Reader",
            "chunk": kwargs.get("chunk", True),
            "chunk_size": kwargs.get("chunk_size", 512),
            "extract": kwargs.get("extract", None),
            "description": "Advanced web scraping and crawling with JavaScript rendering and structured data extraction",
        }
        # config.update(kwargs)
        return FirecrawlReader(**config)

    @classmethod
    def _get_youtube_reader(cls, **kwargs) -> Reader:
        """Get YouTube reader instance."""
        from mielto.knowledge.reader.youtube_reader import YouTubeReader

        config: Dict[str, Any] = {
            "name": "YouTube Reader",
            "description": "Extracts transcripts and metadata from YouTube videos and playlists",
        }
        config.update(kwargs)
        return YouTubeReader(**config)

    @classmethod
    def _get_arxiv_reader(cls, **kwargs) -> Reader:
        """Get Arxiv reader instance."""
        from mielto.knowledge.reader.arxiv_reader import ArxivReader

        config: Dict[str, Any] = {
            "name": "Arxiv Reader",
            "description": "Downloads and processes academic papers from ArXiv with PDF parsing and metadata extraction",
        }
        config.update(kwargs)
        return ArxivReader(**config)

    @classmethod
    def _get_wikipedia_reader(cls, **kwargs) -> Reader:
        """Get Wikipedia reader instance."""
        from mielto.knowledge.reader.wikipedia_reader import WikipediaReader

        config: Dict[str, Any] = {
            "name": "Wikipedia Reader",
            "description": "Fetches and processes Wikipedia articles with section-aware chunking and link resolution",
        }
        config.update(kwargs)
        return WikipediaReader(**config)

    @classmethod
    def _get_web_search_reader(cls, **kwargs) -> Reader:
        """Get Web Search reader instance."""
        from mielto.knowledge.reader.web_search_reader import WebSearchReader

        config: Dict[str, Any] = {
            "name": "Web Search Reader",
            "description": "Executes web searches and processes results with relevance ranking and content extraction",
        }
        config.update(kwargs)
        return WebSearchReader(**config)

    @classmethod
    def _get_markitdown_reader(cls, **kwargs) -> Reader:
        """Get MarkItDown reader instance."""
        from mielto.knowledge.reader.markitdown_reader import MarkItDownReader

        config: Dict[str, Any] = {
            "name": "MarkItDown Reader",
            "description": "Converts various file formats to markdown using MarkItDown library",
            "chunk": kwargs.get("chunk", True),
            "chunk_size": kwargs.get("chunk_size", 512),
        }
        config.update(kwargs)
        return MarkItDownReader(**config)

    @classmethod
    def _get_docling_reader(cls, **kwargs) -> Reader:
        """Get Docling reader instance."""
        from mielto.knowledge.reader.docling_reader import DoclingReader

        config: Dict[str, Any] = {
            "name": "Docling Reader",
            "description": "Processes documents using Docling with support for PDF, DOCX, and other formats",
            "chunk": kwargs.get("chunk", True),
            "chunk_size": kwargs.get("chunk_size", 512),
        }
        config.update(kwargs)
        return DoclingReader(**config)

    @classmethod
    def _get_langchain_reader(cls, **kwargs) -> Reader:
        """Get Langchain reader instance."""
        from mielto.knowledge.reader.langchain_reader import LangchainFileReader

        config: Dict[str, Any] = {
            "name": "Langchain Reader",
            "loader_type": kwargs.get("loader_type", None),
            "chunk": kwargs.get("chunk", True),
            "chunk_size": kwargs.get("chunk_size", 512),
            "extract": kwargs.get("extract", None),
            "description": "Processes documents using Langchain with support for PDF, DOCX, and other formats",
        }
        config.update(kwargs)
        return LangchainFileReader(**config)

    @classmethod
    def _get_reader_method(cls, reader_key: str) -> Callable[[], Reader]:
        """Get the appropriate reader method for the given key."""
        method_name = f"_get_{reader_key}_reader"
        print(f"Getting reader method: {method_name}")
        if not hasattr(cls, method_name):
            raise ValueError(f"Unknown reader: {reader_key}")
        return getattr(cls, method_name)

    @classmethod
    def create_reader(cls, reader_key: str, **kwargs) -> Reader:
        """Create a reader instance with the given key and optional overrides."""

        if kwargs.get("provider") and kwargs.get("provider") != "native":
            reader_key = f"{kwargs.get('provider')}"
            print(f"Using provider reader key: {reader_key}")

        if reader_key in cls._reader_cache:
            return cls._reader_cache[reader_key]

        # Get the reader method and create the instance
        reader_method = cls._get_reader_method(reader_key)
        reader = reader_method(**kwargs)

        # Cache the reader
        cls._reader_cache[reader_key] = reader

        return reader

    @classmethod
    def get_reader_for_extension(cls, extension: str, provider: Optional[str] = "native") -> Reader:
        """Get the appropriate reader for a file extension."""
        extension = extension.lower()

        if extension in [".pdf", "application/pdf"]:
            return cls.create_reader("pdf", provider=provider)
        elif extension in [".csv", "text/csv"]:
            return cls.create_reader("csv", provider=provider)
        elif extension in [".docx", ".doc"]:
            return cls.create_reader("docx", provider=provider)
        elif extension == ".json":
            return cls.create_reader("json", provider=provider)
        elif extension in [".md", ".markdown"]:
            return cls.create_reader("markdown", provider=provider)
        elif extension in [".txt", ".text"]:
            return cls.create_reader("text", provider=provider)
        elif extension in [".pptx", ".ppt"]:
            return cls.create_reader("pptx", provider=provider)
        else:
            # Default to text reader for unknown extensions
            return cls.create_reader("text")

    @classmethod
    def get_reader_for_url(cls, url: str) -> Reader:
        """Get the appropriate reader for a URL."""
        url_lower = url.lower()

        # Check for YouTube URLs
        if any(domain in url_lower for domain in ["youtube.com", "youtu.be"]):
            return cls.create_reader("youtube")

        # Default to URL reader
        return cls.create_reader("url")

    @classmethod
    def get_all_reader_keys(cls) -> List[str]:
        """Get all available reader keys in priority order."""
        # Extract reader keys from method names

        PREFIX = "_get_"
        SUFFIX = "_reader"

        reader_keys = []
        for attr_name in dir(cls):
            if attr_name.startswith(PREFIX) and attr_name.endswith(SUFFIX):
                reader_key = attr_name[len(PREFIX) : -len(SUFFIX)]  # Remove "_get_" prefix and "_reader" suffix
                reader_keys.append(reader_key)

        # Define priority order for URL readers
        url_reader_priority = ["url", "website", "firecrawl", "pdf_url", "csv_url", "youtube", "web_search"]

        # Sort with URL readers in priority order, others alphabetically
        def sort_key(reader_key):
            if reader_key in url_reader_priority:
                return (0, url_reader_priority.index(reader_key))
            else:
                return (1, reader_key)

        reader_keys.sort(key=sort_key)
        return reader_keys

    @classmethod
    def create_all_readers(cls) -> Dict[str, Reader]:
        """Create all readers and return them as a dictionary."""
        readers = {}
        for reader_key in cls.get_all_reader_keys():
            readers[reader_key] = cls.create_reader(reader_key)
        return readers

    @classmethod
    def clear_cache(cls):
        """Clear the reader cache."""
        cls._reader_cache.clear()

    @classmethod
    def register_reader(
        cls,
        key: str,
        reader_method,
        name: str,
        description: str,
        extensions: Optional[List[str]] = None,
    ):
        """Register a new reader type."""
        # Add the reader method to the class
        method_name = f"_get_{key}_reader"
        setattr(cls, method_name, classmethod(reader_method))
