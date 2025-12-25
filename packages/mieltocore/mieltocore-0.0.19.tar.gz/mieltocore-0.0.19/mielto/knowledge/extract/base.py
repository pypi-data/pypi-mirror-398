from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Dict, Any, Union

from mielto.knowledge.document.base import Document
from mielto.utils.log import log_debug, log_error, log_warning
from pydantic import BaseModel
from mielto.models.base import Model


class ExtractInstructions(BaseModel):
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = None
    provider: Optional[str] = None
    model: Optional[Union[str, Model]] = None
    mode: Optional[str] = "text" # text, base64

class ExtractConfig(BaseModel):
    strategy: Optional[str] = "page"
    pages: Optional[List[Union[int, str]]] = None
    instructions: Optional[Union[str, ExtractInstructions]] = None


class ExtractStrategy(ABC):
    """Base class for extraction strategies"""

    @abstractmethod
    def extract(self, documents: List[Document]) -> List[Document]:
        """
        Extract relevant portions from documents.
        
        Args:
            documents: List of documents to extract from
            
        Returns:
            List of extracted documents
        """
        raise NotImplementedError


class ExtractStrategyType(str, Enum):
    """Enumeration of available extraction strategies."""

    NO_EXTRACT = "NoExtract"
    PAGE_EXTRACT = "PageExtract"
    AGENTIC_EXTRACT = "AgenticExtract"

    @classmethod
    def from_string(cls, strategy_name: str) -> "ExtractStrategyType":
        """Convert a string to an ExtractStrategyType."""
        strategy_name_clean = strategy_name.strip().lower()

        mapping = {
            "noextract": cls.NO_EXTRACT,
            "pageextract": cls.PAGE_EXTRACT,
            "page": cls.PAGE_EXTRACT,
            "agenticextract": cls.AGENTIC_EXTRACT,
            "agentic": cls.AGENTIC_EXTRACT,
            "prompt": cls.AGENTIC_EXTRACT,
            "instruction": cls.AGENTIC_EXTRACT,
        }

        if strategy_name_clean in mapping:
            return mapping[strategy_name_clean]

        # Try exact enum value match
        for enum_member in cls:
            if enum_member.value.lower() == strategy_name_clean:
                return enum_member

        raise ValueError(
            f"Unsupported extraction strategy: {strategy_name}. "
            f"Valid options: {[e.value for e in cls]}"
        )


class NoExtractStrategy(ExtractStrategy):
    """Passthrough strategy that returns documents unchanged."""

    def extract(self, documents: List[Document]) -> List[Document]:
        """Return documents unchanged."""
        return documents


class ExtractStrategyFactory:
    """Factory for creating extraction strategy instances."""

    @classmethod
    def create_strategy(
        cls,
        config: ExtractConfig,
        **kwargs
    ) -> ExtractStrategy:
        """
        Create an instance of the extraction strategy based on ExtractConfig or explicit parameters.
        
        Args:
            extract_config: ExtractConfig object (from backend schema)
            pages: List of page numbers/ranges to extract
            instructions: Instructions for agentic extraction (string or ExtractInstructions dict)
            model: Model instance for agentic extraction (required for AgenticExtractStrategy)
            **kwargs: Additional parameters
            
        Returns:
            ExtractStrategy instance
        """

        model = None

        if (config.strategy == "page" and config.pages) or (config.pages and not config.instructions):
            return cls._create_page_extract(pages=config.pages, **kwargs)
        elif (config.strategy == "agentic" and config.instructions) or config.instructions is not None:

            if isinstance(config.instructions, ExtractInstructions):
                if isinstance(config.instructions.model, str):
                    raise ValueError("Model must be a Model object, not a string")

                model = config.instructions.model

            if config.strategy != "agentic":
                print("WARNING: Strategy is not agentic, but instructions are provided. Defaulting to agentic strategy.")
                config.strategy = "agentic"
            return cls._create_agentic_extract(
                instructions=config.instructions,
                model=model,
                **kwargs
            )
        else:
            return NoExtractStrategy()
        

    @classmethod
    def _create_page_extract(cls, pages: List[Union[int, str]], **kwargs) -> ExtractStrategy:
        """Create PageExtractStrategy instance."""
        from mielto.knowledge.extract.page import PageExtractStrategy
        return PageExtractStrategy(pages=pages, **kwargs)

    @classmethod
    def _create_agentic_extract(
        cls,
        instructions: Union[str, ExtractInstructions],
        model: Optional[Any] = None,
        **kwargs
    ) -> ExtractStrategy:
        """Create AgenticExtractStrategy instance."""
        from mielto.knowledge.extract.agentic import AgenticExtractStrategy
        return AgenticExtractStrategy(
            instructions=instructions,
            model=model,
            **kwargs
        )
