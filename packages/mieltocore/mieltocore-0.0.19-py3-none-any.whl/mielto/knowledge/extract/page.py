import re
from typing import List, Union, Set, Optional

from mielto.knowledge.extract.base import ExtractStrategy
from mielto.knowledge.document.base import Document
from mielto.utils.log import log_debug, log_warning


class PageExtractStrategy(ExtractStrategy):
    """
    Extraction strategy that extracts specific pages from documents.
    
    Supports:
    - Integer page numbers: [1, 3, 5]
    - String ranges: ["1-5", "10-15"]
    - Mixed: [1, "3-5", 10]
    """

    def __init__(self, pages: List[Union[int, str]]):
        """
        Initialize PageExtractStrategy.
        
        Args:
            pages: List of page numbers or ranges to extract.
                  Can be integers or strings like "5-10" for ranges.
        """
        if not pages:
            raise ValueError("pages list cannot be empty")
        
        self.pages = pages
        self.target_pages = self._parse_pages(pages)
        log_debug(f"PageExtractStrategy initialized with pages: {self.target_pages}")

    def _parse_pages(self, pages: List[Union[int, str]]) -> Set[int]:
        """
        Parse page numbers and ranges into a set of page numbers.
        
        Args:
            pages: List of page numbers or ranges
            
        Returns:
            Set of page numbers to extract
        """
        target_pages: Set[int] = set()
        
        for page_spec in pages:
            if isinstance(page_spec, int):
                target_pages.add(page_spec)
            elif isinstance(page_spec, str):
                # Try to parse as range (e.g., "5-10")
                range_match = re.match(r'^(\d+)-(\d+)$', page_spec.strip())
                if range_match:
                    start = int(range_match.group(1))
                    end = int(range_match.group(2))
                    if start > end:
                        log_warning(f"Invalid page range: {page_spec} (start > end), skipping")
                        continue
                    target_pages.update(range(start, end + 1))
                else:
                    # Try to parse as single page number
                    try:
                        page_num = int(page_spec.strip())
                        target_pages.add(page_num)
                    except ValueError:
                        log_warning(f"Invalid page specification: {page_spec}, skipping")
            else:
                log_warning(f"Invalid page type: {type(page_spec)}, skipping")
        
        return target_pages

    def extract(self, documents: List[Document]) -> List[Document]:
        """
        Extract documents that match the specified page numbers.
        
        Args:
            documents: List of documents to filter
            
        Returns:
            List of documents matching the page numbers
        """
        if not self.target_pages:
            log_warning("No valid pages to extract, returning empty list")
            return []
        
        extracted: List[Document] = []
        
        for doc in documents:
            # Get page number from metadata
            page_num = self._get_page_number(doc)
            
            if page_num is not None and page_num in self.target_pages:
                # Preserve original metadata and add extraction info
                meta_data = doc.meta_data.copy() if doc.meta_data else {}
                meta_data["extracted_page"] = page_num
                meta_data["extraction_strategy"] = "page"
                
                extracted.append(
                    Document(
                        id=doc.id,
                        name=doc.name,
                        content=doc.content,
                        meta_data=meta_data,
                        embedder=doc.embedder,
                        embedding=doc.embedding,
                        content_id=doc.content_id,
                        content_origin=doc.content_origin,
                        size=doc.size,
                    )
                )
                log_debug(f"Extracted page {page_num} from document: {doc.name or doc.id}")
        
        if not extracted:
            log_warning(
                f"No documents found matching pages {sorted(self.target_pages)}. "
                f"Available pages in metadata: {self._get_available_pages(documents)}"
            )
        
        return extracted

    def _get_page_number(self, document: Document) -> Optional[int]:
        """
        Extract page number from document metadata.
        
        Args:
            document: Document to extract page number from
            
        Returns:
            Page number if found, None otherwise
        """
        if not document.meta_data:
            return None
        
        # Try different metadata keys that might contain page number
        page_keys = ["page", "page_number", "page_num", "pagenumber"]
        
        for key in page_keys:
            if key in document.meta_data:
                page_value = document.meta_data[key]
                if isinstance(page_value, int):
                    return page_value
                elif isinstance(page_value, str):
                    try:
                        return int(page_value)
                    except ValueError:
                        continue
        
        return None

    def _get_available_pages(self, documents: List[Document]) -> List[int]:
        """Get list of available page numbers from documents."""
        pages = []
        for doc in documents:
            page_num = self._get_page_number(doc)
            if page_num is not None:
                pages.append(page_num)
        return sorted(set(pages))
