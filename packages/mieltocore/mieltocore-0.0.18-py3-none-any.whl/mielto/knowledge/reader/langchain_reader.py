from mielto.knowledge.reader.base import Reader
from mielto.knowledge.document.base import Document
from mielto.utils.common import generate_prefix_ulid
from typing import Union, Optional, List, IO, Any
from pathlib import Path


from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    PDFPlumberLoader,
    PyPDFLoader,
    PyMuPDFLoader,
    PyPDFium2Loader,
    JSONLoader,
    Docx2txtLoader,
    UnstructuredFileLoader,
)
from mielto.knowledge.chunking.strategy import ChunkingStrategyType

from langchain_core.documents import Document as LangchainDocument


class LangchainFileReader(Reader):
    """Reader for Langchain files"""


    @classmethod
    def get_supported_chunking_strategies(self) -> List[ChunkingStrategyType]:
        """Get the list of supported chunking strategies for PDF readers."""
        return [
            ChunkingStrategyType.DOCUMENT_CHUNKER,
            ChunkingStrategyType.FIXED_SIZE_CHUNKER,
            ChunkingStrategyType.AGENTIC_CHUNKER,
            ChunkingStrategyType.SEMANTIC_CHUNKER,
            ChunkingStrategyType.RECURSIVE_CHUNKER
        ]

    def __init__(self, loader_type: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.loader_type = loader_type

    def get_loader(self, file: Union[Path, IO[Any], str], password: Optional[str] = None, config: Optional[dict] = None):
        if config is None:
            config = {}
        
        path = Path(file)
        
        if not path.exists():
                raise ValueError(f"File not found: {file}")
            
        extension = path.suffix.lower()
        
        if extension == ".txt":
            loader = TextLoader(str(path), **config)
        elif extension == ".pdf":
            if self.loader_type == "pdfplumber":
                loader = PDFPlumberLoader(str(path), **config)
            elif self.loader_type == "pypdf":
                loader = PyPDFLoader(str(path), **config)
            elif self.loader_type == "pymupdf":
                loader = PyMuPDFLoader(str(path), **config)
            elif self.loader_type == "pypdfium":
                loader = PyPDFium2Loader(str(path), **config)
            elif self.loader_type == "unstructured":
                loader = UnstructuredFileLoader(str(path), **config)
            else:
                raise ValueError(f"Unsupported PDF loader type: {self.loader_type}")
        elif extension == ".csv":
            loader = CSVLoader(str(path), **config)
        elif extension == ".json":
            loader = JSONLoader(str(path), **config)
        elif extension in [".docx", ".doc", ".docs"]:
            loader = Docx2txtLoader(str(path), **config)
        elif extension in [".md", ".html", ".pptx", ".xlsx", ".xls", ".xml", ".odt", ".epub", ".rtf"]:
            loader = UnstructuredFileLoader(str(path), **config)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
        
        return loader
    
    def _build_chunked_documents(self, documents: List[Document]) -> List[Document]:
        chunked_documents: List[Document] = []
        for document in documents:
            chunked_documents.extend(self.chunk_document(document))
        return chunked_documents

    def _create_documents(self, documents: List[LangchainDocument], name: Optional[str] = None) -> List[Document]:
        docs =  [Document(
            name=name,
            id=document.id or generate_prefix_ulid("chunk"),
            content=document.page_content,
            meta_data=document.metadata
        ) for document in documents]


        if self.extract:
            docs =  self.extract_content(docs)

        if self.chunk:
            return self._build_chunked_documents(docs)
        return docs

    def read(self, file: Union[Path, IO[Any], str], name: Optional[str] = None, password: Optional[str] = None) -> List[Document]:
        loader = self.get_loader(file, password)
        langchain_docs = loader.load()
        return self._create_documents(langchain_docs, name=name)

    async def async_read(self, file:  Union[Path, IO[Any], str], name: Optional[str] = None, password: Optional[str] = None) -> List[Document]:
        loader = self.get_loader(file)
        langchain_docs = await loader.aload()
        return self._create_documents(langchain_docs, name=name)