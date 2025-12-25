import json
import re
from typing import List, Union, Dict, Any, Optional

from mielto.knowledge.extract.base import ExtractStrategy, ExtractInstructions
from mielto.knowledge.document.base import Document
from mielto.models.base import Model
from mielto.models.message import Message
from mielto.utils.log import log_debug, log_error, log_warning, log_info


class AgenticExtractStrategy(ExtractStrategy):
    """
    LLM-based extraction strategy that uses natural language instructions or structured prompts
    to extract relevant content from documents.
    
    Supports:
    - Simple string prompts: "Extract all tables"
    - Structured ExtractInstructions with system_prompt and optional schema
    - Custom LLM provider and model configuration
    """

    # Approximate token limits (conservative estimates)
    # Most models have context windows, we'll use a safe chunk size
    MAX_TOKENS_PER_CHUNK = 100000  # ~75k characters for safety
    CHUNK_OVERLAP = 1000  # Small overlap for context

    def __init__(
        self,
        instructions: Union[str, ExtractInstructions],
        model: Optional[Model] = None,
    ):
        """
        Initialize AgenticExtractStrategy.
        
        Args:
            instructions: Either a string prompt or ExtractInstructions dict with:
                         - system_prompt: str
                         - schema: Optional[Dict[str, Any]]
                         - user_prompt: Optional[str] (if dict)
            model: Model instance to use for extraction. If None, a default model will be created.
        """
        self.instructions = instructions
        self.model = model
        if isinstance(instructions, ExtractInstructions) and model is None:
            self.model = instructions.model
        if self.model is not None and isinstance(self.model, str):
            raise ValueError("Model must be a Model object, not a string")
        
        # Set default model if none provided
        if self.model is None:
            self.get_model()
        
        # Parse instructions
        self.system_prompt = None
        self.user_prompt = None
        self.schema = None

        default_system_prompt = [
            "You are an expert at extracting relevant information, tables and structured data from documents from user query. ",
            "Extract the requested information accurately and preserve the original formatting when possible."
        ]
        
        if isinstance(instructions, str):
            # Simple string prompt - use as user prompt
            self.user_prompt = instructions
            self.system_prompt = default_system_prompt
        elif isinstance(instructions, ExtractInstructions):
            # Structured ExtractInstructions
            if instructions.system_prompt:
                self.system_prompt = [instructions.system_prompt]
            else:
                self.system_prompt = default_system_prompt
            self.schema = instructions.schema
            self.user_prompt = instructions.user_prompt
        else:
            raise ValueError(f"Invalid instructions type: {type(instructions)}")
        
        if not self.system_prompt:
            self.system_prompt = default_system_prompt
        
        if not self.schema:
            self.system_prompt.append("Wrap your response in <extracted_content> and </extracted_content> tags.")

        if not self.user_prompt:
            raise ValueError("No user prompt found in instructions")
        
        log_debug(
            f"AgenticExtractStrategy initialized with model={self.model.id if self.model else 'None'} "
            f"({self.model.provider if self.model else 'None'}), has_schema={self.schema is not None}"
        )

    def get_model(self) -> Model:
        """Get model instance, creating a default if none is provided."""
        if self.model is None:
            try:
                from mielto.models.openai import OpenAIChat
                self.model = OpenAIChat(id="gpt-4o-mini")
                log_debug("Created default OpenAI model: gpt-4o-mini")
            except ModuleNotFoundError as e:
                log_error(e)
                log_error(
                    "Mielto uses `openai` as the default model provider. Please provide a `model` or install `openai`."
                )
                raise RuntimeError(
                    "Model instance not provided and default model cannot be created. "
                    "Please provide a model instance or install `openai`."
                )
        return self.model

    def extract(self, documents: List[Document]) -> List[Document]:
        """
        Extract content from documents using LLM-based extraction.
        
        Args:
            documents: List of documents to extract from
            
        Returns:
            List of extracted documents
        """
        if not documents:
            return []
        
        extracted: List[Document] = []
        
        for doc in documents:
            try:
                extracted_doc = self._extract_from_document(doc)
                if extracted_doc:
                    extracted.append(extracted_doc)
            except Exception as e:
                log_error(f"Error extracting from document {doc.id or doc.name}: {e}")
                # On error, include original document as fallback
                extracted.append(doc)
        
        print(extracted, "EXTRACTED")
        return extracted if extracted else documents

    def _extract_from_document(self, document: Document) -> Optional[Document]:
        """
        Extract content from a single document using LLM.
        
        Args:
            document: Document to extract from
            
        Returns:
            Extracted document or None if extraction fails
        """
        if not document.content:
            log_warning(f"Document {document.id or document.name} has no content")
            return document
        
        content = document.content
        
        # Check if document needs chunking
        if len(content) > self.MAX_TOKENS_PER_CHUNK:
            log_debug(f"Document too large ({len(content)} chars), chunking for LLM")
            return self._extract_from_large_document(document)
        
        # Extract from single document
        try:
            extracted_content = self._call_llm(content)
            
            if not extracted_content:
                log_warning(f"No content extracted from document {document.id or document.name}")
                return document
            
            # Create extracted document
            meta_data = document.meta_data.copy() if document.meta_data else {}
            meta_data["extraction_strategy"] = "agentic"
            meta_data["extraction_instructions"] = self.user_prompt
            
            return Document(
                id=document.id,
                name=document.name,
                content=extracted_content,
                meta_data=meta_data,
                embedder=document.embedder,
                content_id=document.content_id,
                content_origin=document.content_origin,
                size=len(extracted_content),
            )
        except Exception as e:
            log_error(f"Error in LLM extraction: {e}")
            return document  # Fallback to original

    def _extract_from_large_document(self, document: Document) -> Document:
        """
        Extract from a large document by chunking and processing each chunk.
        
        Args:
            document: Large document to extract from
            
        Returns:
            Document with extracted content from all chunks
        """
        content = document.content
        chunks = self._chunk_content(content)
        
        extracted_chunks = []
        for i, chunk in enumerate(chunks):
            try:
                extracted_chunk = self._call_llm(chunk)
                if extracted_chunk:
                    extracted_chunks.append(extracted_chunk)
                    log_debug(f"Extracted chunk {i+1}/{len(chunks)}")
            except Exception as e:
                log_warning(f"Error extracting chunk {i+1}: {e}")
        
        if not extracted_chunks:
            log_warning("No chunks extracted from large document")
            return document
        
        # Combine extracted chunks
        combined_content = "\n\n".join(extracted_chunks)
        
        meta_data = document.meta_data.copy() if document.meta_data else {}
        meta_data["extraction_strategy"] = "agentic"
        meta_data["extraction_instructions"] = self.user_prompt
        meta_data["extraction_chunks_processed"] = len(chunks)
        
        return Document(
            id=document.id,
            name=document.name,
            content=combined_content,
            meta_data=meta_data,
            embedder=document.embedder,
            content_id=document.content_id,
            content_origin=document.content_origin,
            size=len(combined_content),
        )

    def _chunk_content(self, content: str) -> List[str]:
        """
        Split large content into chunks for LLM processing.
        
        Args:
            content: Content to chunk
            
        Returns:
            List of content chunks
        """
        chunks = []
        start = 0
        content_length = len(content)
        
        while start < content_length:
            end = min(start + self.MAX_TOKENS_PER_CHUNK, content_length)
            
            # Try to break at paragraph boundary
            if end < content_length:
                # Look for paragraph break (double newline)
                last_break = content.rfind("\n\n", start, end)
                if last_break > start:
                    end = last_break + 2
            
            chunk = content[start:end]
            chunks.append(chunk)
            start = end - self.CHUNK_OVERLAP if end < content_length else end
        
        return chunks

    def _extract_from_tags(self, content: str) -> str:
        """
        Extract content from <extracted_content> tags if present.
        
        Args:
            content: Content that may contain <extracted_content> tags
            
        Returns:
            Extracted content without the tags, or original content if tags not found
        """
        if not isinstance(content, str):
            return content
        
        # Pattern to match <extracted_content>...</extracted_content> tags
        pattern = r'<extracted_content>(.*?)</extracted_content>'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            extracted = match.group(1).strip()
            log_debug("Extracted content from <extracted_content> tags")
            return extracted
        
        # If no tags found, return content as-is
        return content

    def _call_llm(self, content: str) -> Optional[str]:
        """
        Call LLM to extract content based on instructions.
        
        Args:
            content: Document content to extract from
            
        Returns:
            Extracted content or None if extraction fails
        """
        model = self.get_model()
        
        # Join system_prompt list into a string if it's a list
        system_prompt_content = (
            "\n".join(self.system_prompt)
        )
        
        # Build messages
        messages = [
            Message(role="system", content=system_prompt_content),
            Message(
                role="user",
                content=f"User query: {self.user_prompt}\n\nDocument content:\n{content}",
            ),
        ]
        
        # Prepare response format if schema is provided
        response_format = None
        if self.schema:
            # Check if model supports native structured outputs
            if model.supports_native_structured_outputs:
                # For native structured outputs, pass the schema dict directly
                response_format = self.schema
            elif model.supports_json_schema_outputs:
                # For JSON schema outputs, wrap in json_schema format
                response_format = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "ExtractedContent",
                        "schema": self.schema,
                    },
                }
            else:
                # Fallback to json_object
                response_format = {"type": "json_object"}
        
        # Call LLM using model.response() (same pattern as MemoryManager)
        try:
            response = model.response(messages=messages, response_format=response_format)

            print(response, "RESPONSE")
            
            # Extract content from response
            if hasattr(response, "content") and response.content:
                extracted = response.content
                
                # If schema was provided and model supports native structured outputs,
                # check if we have parsed content
                if self.schema and model.supports_native_structured_outputs:
                    if hasattr(response, "parsed") and response.parsed is not None:
                        # Convert parsed object to JSON string
                        if isinstance(response.parsed, dict):
                            extracted = json.dumps(response.parsed, indent=2)
                        else:
                            # Try to convert to dict if it's a Pydantic model
                            try:
                                extracted = json.dumps(response.parsed.model_dump(), indent=2)
                            except AttributeError:
                                extracted = str(response.parsed)
                
                # If schema was provided and extracted is a string, try to parse JSON
                elif self.schema and isinstance(extracted, str):
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(extracted)
                        # Convert back to string for document content
                        extracted = json.dumps(parsed, indent=2)
                    except json.JSONDecodeError:
                        # Not JSON, use as-is
                        pass
                
                # If no schema was provided, extract content from <extracted_content> tags
                elif not self.schema and isinstance(extracted, str):
                    extracted = self._extract_from_tags(extracted)
                
                return extracted
            else:
                log_warning("LLM response has no content")
                return None
                
        except Exception as e:
            log_error(f"Error calling LLM: {e}")
            raise
