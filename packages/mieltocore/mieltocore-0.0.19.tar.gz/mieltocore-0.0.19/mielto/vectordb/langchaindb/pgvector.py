from mielto.utils.common import generate_prefix_ulid
from mielto.vectordb.base import VectorDb
from mielto.knowledge.embedder.base import Embedder
from mielto.vectordb.search import SearchType
from mielto.vectordb.pgvector.pgvector import Ivfflat, HNSW, Distance
from mielto.vectordb.pgvector.pgvector import Reranker
from typing import Optional, Union
from mielto.utils.log import log_debug, log_info, logger
from mielto.knowledge.document import Document
from typing import Optional, Dict, List, Any
import asyncio
try:
    from pgvector.sqlalchemy import Vector
    
except ImportError:
    raise ImportError("`pgvector` not installed. Please install using `pip install pgvector`")

from sqlalchemy.dialects.postgresql import TSVECTOR
from langchain_core.documents import Document as LangChainDocument

try:
    from langchain_postgres import PGEngine, PGVectorStore
    from langchain_postgres.v2.indexes import DistanceStrategy
    from langchain_postgres.v2.hybrid_search_config import HybridSearchConfig, reciprocal_rank_fusion
except ImportError:
    raise ImportError("`langchain_postgres` not installed. Please install using `pip install langchain_postgres`")
try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    raise ImportError(
        "`langchain-openai` not installed. Please install using `pip install langchain-openai`"
    )

try:
    from sqlalchemy import update, JSON
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.engine import Engine, create_engine
    from sqlalchemy.inspection import inspect
    from sqlalchemy.orm import Session, scoped_session, sessionmaker
    from sqlalchemy.schema import Column, Index, MetaData, Table
    from sqlalchemy.sql.expression import bindparam, desc, func, select, text
    from sqlalchemy.types import DateTime, String

except ImportError:
    raise ImportError("`sqlalchemy` not installed. Please install using `pip install sqlalchemy psycopg`")


class LangChainPgVector(VectorDb):

    def __init__(
        self,
        table_name: str,
        schema: str = "ai",
        db_url: Optional[str] = None,
        pg_engine: Optional[PGEngine] = None,
        db_engine: Optional[Engine] = None,
        embedder: Optional[Embedder] = None,
        search_type: SearchType = SearchType.vector,
        vector_index: Union[Ivfflat, HNSW] = HNSW(),
        distance: Distance = Distance.cosine,
        prefix_match: bool = False,
        vector_score_weight: float = 0.5,
        content_language: str = "english",
        schema_version: int = 1,
        auto_upgrade_schema: bool = False,
        reranker: Optional[Reranker] = None,
        use_batch: bool = False,
    ):
        """
        Initialize the PgVector instance.

        Args:
            table_name (str): Name of the table to store vector data.
            schema (str): Database schema name.
            db_url (Optional[str]): Database connection URL.
            db_engine (Optional[Engine]): SQLAlchemy database engine.
            pg_engine (Optional[PGEngine]): Langchain Postgres engine.
            embedder (Optional[Embedder]): Embedder instance for creating embeddings.
            search_type (SearchType): Type of search to perform.
            vector_index (Union[Ivfflat, HNSW]): Vector index configuration.
            distance (Distance): Distance metric for vector comparisons.
            prefix_match (bool): Enable prefix matching for full-text search.
            vector_score_weight (float): Weight for vector similarity in hybrid search.
            content_language (str): Language for full-text search.
            schema_version (int): Version of the database schema.
            auto_upgrade_schema (bool): Automatically upgrade schema if True.
        """

        if not table_name:
            raise ValueError("Table name must be provided.")

        if db_engine is None and db_url is None:
            raise ValueError("Either 'db_url' or 'db_engine' must be provided.")

        if db_engine is None:
            if db_url is None:
                raise ValueError("Must provide 'db_url' if 'db_engine' is None.")
            try:
                db_engine = create_engine(db_url)
            except Exception as e:
                logger.error(f"Failed to create engine from 'db_url': {e}")
                raise

        self.table_name: str = table_name
        self.schema: str = schema
        self.db_url: Optional[str] = db_url
        self.db_engine: Engine = db_engine
        self.pg_engine: PGEngine = pg_engine
        if self.pg_engine is None:
            self.pg_engine = PGEngine.from_connection_string(self.db_url.replace("+psycopg2", "+asyncpg"))
        self.metadata: MetaData = MetaData(schema=self.schema)
        self.use_batch: bool = use_batch

        # Embedder for embedding the document contents
        if embedder is None:
            from mielto.knowledge.embedder.openai import OpenAIEmbedder

            embedder = OpenAIEmbedder()
            log_info("Embedder not provided, using OpenAIEmbedder as default.")
        self.embedder: Embedder = embedder
        self.dimensions: Optional[int] = self.embedder.dimensions

        if self.dimensions is None:
            raise ValueError("Embedder.dimensions must be set.")
        
        # Search type
        self.search_type: SearchType = search_type
        # Distance metric
        self.distance: Distance = distance

        if self.table_exists():
            self.vector_store: PGVectorStore = self._get_vector_store()

        self.Session: scoped_session = scoped_session(sessionmaker(bind=self.db_engine))
        # Database table
        self.table: Table = self.get_table()
        log_debug(f"Initialized LangChainPgVector with table '{self.schema}.{self.table_name}'")

    def get_langchain_embedding(self) -> "OpenAIEmbeddings":
        """
        Transform Mielto OpenAIEmbedder to LangChain OpenAIEmbeddings.
        
        Returns:
            OpenAIEmbeddings: LangChain OpenAI embeddings instance
        """
       
        
        # Extract parameters from Mielto OpenAIEmbedder
        embedder_params = {}
        
        # Map Mielto embedder attributes to LangChain parameters
        if hasattr(self.embedder, 'api_key') and self.embedder.api_key:
            embedder_params['api_key'] = self.embedder.api_key
        
        if hasattr(self.embedder, 'base_url') and self.embedder.base_url:
            embedder_params['base_url'] = self.embedder.base_url
        
        if hasattr(self.embedder, 'organization') and self.embedder.organization:
            embedder_params['organization'] = self.embedder.organization
        
        if hasattr(self.embedder, 'id') and self.embedder.id:
            embedder_params['model'] = self.embedder.id
        
        # if hasattr(self.embedder, 'dimensions') and self.embedder.dimensions:
        #     embedder_params['dimensions'] = self.embedder.dimensions
        
        # if hasattr(self.embedder, 'encoding_format') and self.embedder.encoding_format:
        #     embedder_params['encoding_format'] = self.embedder.encoding_format
        
        if hasattr(self.embedder, 'user') and self.embedder.user:
            embedder_params['user'] = self.embedder.user
        
        # Add any additional client parameters
        if hasattr(self.embedder, 'client_params') and self.embedder.client_params:
            embedder_params.update(self.embedder.client_params)
        
        # Add any additional request parameters
        if hasattr(self.embedder, 'request_params') and self.embedder.request_params:
            embedder_params.update(self.embedder.request_params)
        
        log_debug(f"Creating LangChain OpenAIEmbeddings with params: {embedder_params}")

        return OpenAIEmbeddings(**embedder_params)
    
    def get_table(self) -> Table:
        """
        Get the SQLAlchemy Table object for schema version 1.

        Returns:
            Table: SQLAlchemy Table object representing the database table.
        """
        if self.dimensions is None:
            raise ValueError("Embedder dimensions are not set.")
        table = Table(
            self.table_name,
            self.metadata,
            Column("id", String, primary_key=True),
            Column("meta_data", JSON, server_default=text("'{}'::json")),
            Column("content", postgresql.TEXT),
            Column("embedding", Vector(self.dimensions)),
            Column("hybrid_tsv", TSVECTOR, nullable=True),
            Column("content_hash", String),
            Column("content_id", String),
            Column("collection_id", String, nullable=True),
            Column("workspace_id", String, nullable=True),
            extend_existing=True,
        )

        # Add indexes
        return table

    def _get_distance_strategy(self) -> str:
        """
        Map Mielto Distance enum to LangChain DistanceStrategy.
        
        Returns:
            str: LangChain DistanceStrategy string
        """
        distance_mapping = {
            Distance.cosine: DistanceStrategy.COSINE_DISTANCE,
            Distance.l2: DistanceStrategy.EUCLIDEAN, 
            Distance.max_inner_product: DistanceStrategy.INNER_PRODUCT,
        }
        return distance_mapping.get(self.distance, DistanceStrategy.COSINE_DISTANCE)

    def create(self):
        """
        Create the vector store table using LangChain Postgres.
        """
        if not self.table_exists():
            metadata_columns = [
                {"name": "collection_id", "data_type": "varchar", "nullable": True},
                {"name": "workspace_id", "data_type": "varchar", "nullable": True}, 
                {"name": "content_id", "data_type": "varchar", "nullable": True},
                {"name": "content_hash", "data_type": "text", "nullable": True},
                {"name": "hybrid_tsv", "data_type": "tsvector", "nullable": True}
            ]
            self.pg_engine.init_vectorstore_table(
                table_name=self.table_name,
                vector_size=self.dimensions,
                schema_name=self.schema,
                metadata_columns=metadata_columns,
                metadata_json_column="meta_data",
                id_column={"name": "id", "data_type": "varchar", "nullable": False}

            )


            try:
                log_debug(f"Creating indexes for table '{self.table_name}'")
                ## Create indexes - using raw sql via the Session
                with self.Session() as sess, sess.begin():
                    sess.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_collection_id ON {self.schema}.{self.table_name} (collection_id);"))
                    sess.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_workspace_id ON {self.schema}.{self.table_name} (workspace_id);"))
                    sess.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_content_id ON {self.schema}.{self.table_name} (content_id);"))
                    sess.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_content_hash ON {self.schema}.{self.table_name} (content_hash);"))
                    # sess.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_meta_data ON {self.schema}.{self.table_name} USING GIN (meta_data);"))
                    # sess.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_hybrid_tsv ON {self.schema}.{self.table_name} USING GIN (hybrid_tsv);"))
            except Exception as e:
                logger.error(f"Error creating indexes for table '{self.table_name}': {e}")
            
            
            # The table will be created automatically when the store is first used
            log_info(f"Vector store table '{self.table_name}' will be created on first use")

        self.vector_store: PGVectorStore = self._get_vector_store()


    async def async_create(self) -> None:
        """Create the table asynchronously by running in a thread."""
        await asyncio.to_thread(self.create)

    def _get_vector_store(self) -> PGVectorStore:
        """
        Create PGVectorStore with LangChain OpenAI embeddings using LangChain Postgres.
        
        Returns:
            PGVectorStore: LangChain PGVector store instance
        """
        # Get LangChain OpenAI embeddings
        embeddings = self.get_langchain_embedding()
        distance_strategy = self._get_distance_strategy()
        kwargs = {}

        if self.search_type == SearchType.hybrid:
            kwargs["hybrid_search_config"] = HybridSearchConfig(
                tsv_column="hybrid_tsv",
                fusion_function=reciprocal_rank_fusion,
            )
        store = PGVectorStore.create_sync(
            engine=self.pg_engine,
            table_name=self.table_name,
            embedding_service=embeddings,
            distance_strategy=distance_strategy,
            schema_name=self.schema,
            id_column="id",
            metadata_columns=["collection_id", "workspace_id", "content_id", "content_hash"],
            metadata_json_column="meta_data",
            **kwargs
        )

        # if self.search_type == SearchType.hybrid:
        #     store.apply_hybrid_search_index()

        return store

    def table_exists(self) -> bool:
        """
        Check if the table exists in the database.

        Returns:
            bool: True if the table exists, False otherwise.
        """
        log_debug(f"Checking if table '{self.table_name}' exists.")
        try:
            return inspect(self.db_engine).has_table(self.table_name, schema=self.schema)
        except Exception as e:
            logger.error(f"Error checking if table exists: {e} {self.table_name} {self.schema}")
            return False

    def _record_exists(self, column, value) -> bool:
        """
        Check if a record with the given column value exists in the table.

        Args:
            column: The column to check.
            value: The value to search for.

        Returns:
            bool: True if the record exists, False otherwise.
        """
        try:
            with self.Session() as sess, sess.begin():
                stmt = select(1).where(column == value).limit(1)
                result = sess.execute(stmt).first()
                return result is not None
        except Exception as e:
            log_debug(f"Error checking if record exists: {e}")
            logger.error(f"Error checking if record exists: {e}")
            return False

    def insert(self, 
        content_hash: str, 
        documents: List[Document], 
        filters: Optional[Dict[str, Any]] = None, 
        collection_id: Optional[str] = None, 
        workspace_id: Optional[str] = None
    ) -> None:
        """Insert documents into the vector store using LangChain Postgres."""
       
        # Convert Mielto documents to LangChain documents
        lc_documents = []
        for doc in documents:
            metadata = doc.meta_data or {}
            if collection_id:
                metadata["collection_id"] = collection_id
            if workspace_id:
                metadata["workspace_id"] = workspace_id
            if content_hash:
                metadata["content_hash"] = content_hash
            if doc.content_id:
                metadata["content_id"] = doc.content_id
                
            lc_doc = LangChainDocument(
                page_content=doc.content,
                metadata=metadata
            )
            lc_documents.append(lc_doc)
        
        # Add documents to vector store
        self.vector_store.add_documents(lc_documents)
        log_info(f"Inserted {len(documents)} documents into vector store")

    async def async_insert(
        self, content_hash: str, documents: List[Document], filters: Optional[Dict[str, Any]] = None, collection_id: Optional[str] = None, workspace_id: Optional[str] = None
    ) -> None:
        """Insert documents asynchronously into the vector store using LangChain Postgres."""
       
        # Convert Mielto documents to LangChain documents
        lc_documents = []
        for doc in documents:
            metadata = doc.meta_data or {}
            if collection_id:
                metadata["collection_id"] = collection_id
            if workspace_id:
                metadata["workspace_id"] = workspace_id
            if content_hash:
                metadata["content_hash"] = content_hash
            if doc.content_id:
                metadata["content_id"] = doc.content_id
                
            lc_doc = LangChainDocument(
                id=doc.id or generate_prefix_ulid("chunk"),
                page_content=doc.content,
                metadata=metadata
            )
            lc_documents.append(lc_doc)
        
        # Add documents to vector store asynchronously
        await self.vector_store.aadd_documents(lc_documents)
        log_info(f"Async inserted {len(documents)} documents into vector store")

    def upsert(self, content_hash: str, documents: List[Document], filters: Optional[Dict[str, Any]] = None) -> None:
        """Upsert documents into the vector store using LangChain Postgres."""
        # For now, treat upsert as insert since LangChain Postgres handles duplicates
        self.insert(content_hash, documents, filters)

    async def async_upsert(self, documents: List[Document], filters: Optional[Dict[str, Any]] = None) -> None:
        """Upsert documents asynchronously into the vector store using LangChain Postgres."""
        # For now, treat upsert as insert since LangChain Postgres handles duplicates
        await self.async_insert("", documents, filters)

    def search(
        self, query: str, limit: Optional[int] = None, filters: Optional[Dict[str, Any]] = None, collection_id: Optional[str] = None, workspace_id: Optional[str] = None
    ) -> List[Document]:
        """Returns relevant documents matching the query using LangChain Postgres similarity search."""


        # Use LangChain Postgres similarity search
        k = limit or 10
        filter_dict = filters or {}
        if collection_id:
            filter_dict["collection_id"] = collection_id
        if workspace_id:
            filter_dict["workspace_id"] = workspace_id
        log_debug(f"Getting {k} relevant documents for query: {query}")

        lc_documents: List[LangChainDocument] =[]

        if self.search_type == SearchType.keyword:

            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 1, 
                    "fetch_k": 2, 
                    "lambda_mult": 0.5
                }
            )
            lc_documents = retriever.invoke(query)
        else:
            lc_documents = self.vector_store.similarity_search(
            query=query,
            k=k,
            filter=filter_dict
        )
        
        # Convert LangChain documents back to Mielto documents
        documents = []
        for lc_doc in lc_documents:
            documents.append(
                Document(
                    id=lc_doc.id,
                    content=lc_doc.page_content,
                    meta_data=lc_doc.metadata,
                )
            )
        return documents

    async def async_search(
        self, query: str, limit: Optional[int] = None, filters: Optional[Dict[str, Any]] = None, collection_id: Optional[str] = None, workspace_id: Optional[str] = None
    ) -> List[Document]:
        """Returns relevant documents matching the query using LangChain Postgres async similarity search."""
       

        # Use LangChain Postgres async similarity search
        k = limit or 10
        filter_dict = filters or {}
        if collection_id:
            filter_dict["collection_id"] = collection_id
        if workspace_id:
            filter_dict["workspace_id"] = workspace_id
        
        log_debug(f"Getting {k} relevant documents for query: {query}")
        lc_documents: List[LangChainDocument] = []


        if self.search_type == SearchType.keyword:


            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": k, 
                    "score_threshold": 0.5,
                    "include_metadata": True,
                    "filter": filter_dict
                }
            )
            lc_documents = retriever.invoke(query)
        else:
            lc_documents = await self.vector_store.asimilarity_search(
                query=query,
                k=k,
                filter=filter_dict
            )
        
        
        # Convert LangChain documents back to Mielto documents
        documents = []
        for lc_doc in lc_documents:
            documents.append(
                Document(
                    content=lc_doc.page_content,
                    meta_data=lc_doc.metadata,
                )
            )
        return documents

    def name_exists(self, name: str) -> bool:
        raise NotImplementedError

    def async_name_exists(self, name: str) -> bool:
        raise NotImplementedError

    def id_exists(self, id: str) -> bool:
        raise NotImplementedError

    def content_hash_exists(self, content_hash: str) -> bool:
        """
        Check if a document with the given content hash exists in the table.
        """
        exists = self._record_exists(self.table.c.content_hash, content_hash)
        log_debug(f"Content hash {content_hash} exists: {exists}")
        return exists


    def delete_by_content_id(self, content_id: str) -> bool:
        """
        Delete all chunks/vectors by content ID.
        
        Args:
            content_id (str): The content ID to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            with self.Session() as sess, sess.begin():
                stmt = self.table.delete().where(self.table.c.content_id == content_id)
                result = sess.execute(stmt)
                sess.commit()
                rows_deleted = result.rowcount if hasattr(result, 'rowcount') else 0
                log_info(f"Deleted {rows_deleted} records with content ID '{content_id}' from table '{self.schema}.{self.table_name}'.")
                return True
        except Exception as e:
            logger.error(f"Error deleting rows from table '{self.schema}.{self.table_name}': {e}")
            sess.rollback()
            return False

    def drop(self) -> None:
        """
        Drop the table from the database.
        """
        try:
            log_info(f"Dropping table '{self.schema}.{self.table_name}'")
            self.table.drop(self.db_engine)
            log_info(f"Table '{self.schema}.{self.table_name}' dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping table '{self.schema}.{self.table_name}': {e}")
            raise

    async def async_drop(self) -> None:
        """Drop the table asynchronously by running in a thread."""
        await asyncio.to_thread(self.drop)

    async def async_exists(self) -> bool:
        """Check if table exists asynchronously by running in a thread."""
        return await asyncio.to_thread(self.exists)

    def delete(self) -> bool:
        """
        Delete all records from the table.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        from sqlalchemy import delete as sql_delete

        try:
            with self.Session() as sess:
                sess.execute(sql_delete(self.table))
                sess.commit()
                log_info(f"Deleted all records from table '{self.schema}.{self.table_name}'.")
                return True
        except Exception as e:
            logger.error(f"Error deleting rows from table '{self.schema}.{self.table_name}': {e}")
            sess.rollback()
            return False

    def delete_by_id(self, id: str) -> bool:
        """
        Delete content by vector/chunk ID.
        
        Args:
            id (str): The vector ID to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            with self.Session() as sess, sess.begin():
                stmt = self.table.delete().where(self.table.c.id == id)
                result = sess.execute(stmt)
                sess.commit()
                rows_deleted = result.rowcount if hasattr(result, 'rowcount') else 0
                log_info(f"Deleted {rows_deleted} records with id '{id}' from table '{self.schema}.{self.table_name}'.")
                return True
        except Exception as e:
            logger.error(f"Error deleting rows from table '{self.schema}.{self.table_name}': {e}")
            sess.rollback()
            return False

    def delete_by_name(self, name: str) -> bool:
        """
        Delete content by name.
        
        Note: LangChain PgVector does not have a 'name' column like standard PgVector.
        This method searches for the name in the meta_data JSON column.
        
        Args:
            name (str): The name to search for in metadata
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            with self.Session() as sess, sess.begin():
                # Search for name in meta_data JSON column
                stmt = self.table.delete().where(
                    self.table.c.meta_data['name'].astext == name
                )
                result = sess.execute(stmt)
                sess.commit()
                rows_deleted = result.rowcount if hasattr(result, 'rowcount') else 0
                log_info(f"Deleted {rows_deleted} records with name '{name}' in metadata from table '{self.schema}.{self.table_name}'.")
                return True
        except Exception as e:
            logger.error(f"Error deleting rows from table '{self.schema}.{self.table_name}': {e}")
            sess.rollback()
            return False

    def delete_by_collection_id(self, collection_id: str) -> bool:
        """
        Delete content by collection ID.
        """
        try:
            with self.Session() as sess, sess.begin():
                stmt = self.table.delete().where(self.table.c.collection_id == collection_id)
                result = sess.execute(stmt)
                sess.commit()
                rows_deleted = result.rowcount if hasattr(result, 'rowcount') else 0
                log_info(f"Deleted {rows_deleted} records with collection ID '{collection_id}' from table '{self.schema}.{self.table_name}'.")
                return True
        except Exception as e:
            logger.error(f"Error deleting rows from table '{self.schema}.{self.table_name}': {e}")
            sess.rollback()
            return False

    def delete_by_workspace_id(self, workspace_id: str) -> bool:
        """
        Delete content by workspace ID.
        """
        try:
            with self.Session() as sess, sess.begin():
                stmt = self.table.delete().where(self.table.c.workspace_id == workspace_id)
                result = sess.execute(stmt)
                sess.commit()
                rows_deleted = result.rowcount if hasattr(result, 'rowcount') else 0
                log_info(f"Deleted {rows_deleted} records with workspace ID '{workspace_id}' from table '{self.schema}.{self.table_name}'.")
                return True
        except Exception as e:
            logger.error(f"Error deleting rows from table '{self.schema}.{self.table_name}': {e}")
            sess.rollback()
            return False

    def delete_by_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Delete content by metadata.
        
        Note: LangChain PgVector uses JSON (not JSONB) for metadata, so the
        containment operator (@>) may not be available. This implementation
        checks for exact match on specific keys.
        
        Args:
            metadata (Dict[str, Any]): The metadata to match for deletion
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            with self.Session() as sess, sess.begin():
                # Build WHERE clause for each metadata key
                stmt = self.table.delete()
                
                # For JSON columns, we need to check each key individually
                for key, value in metadata.items():
                    if isinstance(value, str):
                        stmt = stmt.where(self.table.c.meta_data[key].astext == value)
                    else:
                        # For non-string values, convert to string for comparison
                        stmt = stmt.where(self.table.c.meta_data[key].astext == str(value))
                
                result = sess.execute(stmt)
                sess.commit()
                rows_deleted = result.rowcount if hasattr(result, 'rowcount') else 0
                log_info(f"Deleted {rows_deleted} records with metadata '{metadata}' from table '{self.schema}.{self.table_name}'.")
                return True
        except Exception as e:
            logger.error(f"Error deleting rows from table '{self.schema}.{self.table_name}': {e}")
            sess.rollback()
            return False

    def exists(self) -> bool:
        return self.table_exists()

    def update_metadata(self, content_id: str, metadata: Dict[str, Any]) -> None:
        """
        Update the metadata for documents with the given content_id.
        Not implemented for LangChain wrapper.

        Args:
            content_id (str): The content ID to update
            metadata (Dict[str, Any]): The metadata to update
        """
        # raise NotImplementedError("update_metadata not supported for LangChain vectorstores")
        pass

    def get_chunk(self, vector_id: str, include_embedding: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get the full chunk data (including embedding and metadata) for a given vector ID.
        
        Args:
            vector_id (str): The ID of the vector/chunk to retrieve.
            include_embedding (bool): Whether to include the embedding vector.
            
        Returns:
            Optional[Dict[str, Any]]: Standardized chunk dictionary, or None if not found.
                Contains: id, content_id, collection_id, workspace_id, name, content, 
                         embedding (optional), metadata, created_at
        """
        try:
            with self.Session() as sess, sess.begin():
                stmt = select(
                    self.table.c.id,
                    self.table.c.content_id,
                    self.table.c.content,
                    self.table.c.embedding,
                    self.table.c.meta_data,
                    self.table.c.collection_id,
                    self.table.c.workspace_id,
                ).where(self.table.c.id == vector_id)
                
                result = sess.execute(stmt).first()
                
                if result is None:
                    log_debug(f"No chunk found with vector ID '{vector_id}'")
                    return None
                
                # Handle embedding format
                embedding_list = None
                if include_embedding:
                    embedding = result.embedding
                    if embedding is not None:
                        if isinstance(embedding, list):
                            embedding_list = embedding
                        elif hasattr(embedding, '__iter__'):
                            embedding_list = list(embedding)
                
                # Return standardized format
                return {
                    "id": result.id,
                    "content_id": result.content_id,
                    "collection_id": result.collection_id,
                    "workspace_id": result.workspace_id,
                    "name": None,  # LangChain doesn't store name
                    "content": result.content,
                    "embedding": embedding_list,
                    "metadata": result.meta_data or {},
                    "created_at": None,  # LangChain doesn't store created_at
                }
                    
        except Exception as e:
            logger.error(f"Error getting chunk for vector ID '{vector_id}': {e}")
            return None

    def list_chunks(
        self, 
        content_id: str = None, 
        filters: Optional[Dict[str, Any]] = None, 
        include_embedding: bool = False,
        limit: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List embedding vectors with metadata using cursor-based pagination.
        
        Args:
            content_id (str, optional): Filter by content ID.
            filters (Dict[str, Any], optional): Additional metadata filters.
                Supports: workspace_id, collection_id, or custom metadata filters.
            include_embedding (bool): Whether to include embedding vectors.
            limit (int, optional): Maximum number of chunks to return (default: 50).
            cursor (str, optional): Pagination cursor (last chunk's ID from previous response).
            
        Returns:
            Dict[str, Any]: Dictionary containing chunks, next_cursor, and has_more flag
        """
        try:
            with self.Session() as sess, sess.begin():
                # Build the query
                stmt = select(
                    self.table.c.id,
                    self.table.c.content_id,
                    self.table.c.content,
                    self.table.c.embedding,
                    self.table.c.meta_data,
                    self.table.c.collection_id,
                    self.table.c.workspace_id,
                )
                
                # Apply content_id filter if provided
                if content_id is not None:
                    stmt = stmt.where(self.table.c.content_id == content_id)

                filters = filters or {}

                if filters.get("workspace_id") is not None:
                    stmt = stmt.where(self.table.c.workspace_id == filters.get("workspace_id"))
                    del filters["workspace_id"]

                if filters.get("collection_id") is not None:
                    stmt = stmt.where(self.table.c.collection_id == filters.get("collection_id"))
                    del filters["collection_id"]
                
                # Apply cursor-based pagination
                # Cursor is the last seen ID from the previous page
                if cursor is not None:
                    stmt = stmt.where(self.table.c.id > cursor)
                
                # Order by ID for consistent cursor-based pagination
                stmt = stmt.order_by(self.table.c.id)
                
                # Default limit to 50 if not specified
                fetch_limit = limit if limit is not None else 50
                
                # Fetch one extra to determine if there are more pages
                stmt = stmt.limit(fetch_limit + 1)
                
                # Execute query
                results = sess.execute(stmt).fetchall()
                
                # Convert results to standardized format
                chunks = []
                for i, result in enumerate(results):
                    # Only include up to 'limit' chunks
                    if i >= fetch_limit:
                        break
                    
                    # Handle different embedding formats
                    embedding_list = None
                    if include_embedding:
                        embedding = result.embedding
                        if embedding is not None:
                            if isinstance(embedding, list):
                                embedding_list = embedding
                            elif hasattr(embedding, '__iter__'):
                                embedding_list = list(embedding)
                    
                    # Return standardized format
                    chunks.append({
                        "id": result.id,
                        "content_id": result.content_id,
                        "collection_id": result.collection_id,
                        "workspace_id": result.workspace_id,
                        "name": None,  # LangChain doesn't store name
                        "content": result.content,
                        "embedding": embedding_list,
                        "metadata": result.meta_data or {},
                        "created_at": None,  # LangChain doesn't store created_at
                    })
                
                # Determine if there are more pages
                has_more = len(results) > fetch_limit
                
                # Set next_cursor for pagination (last chunk's ID)
                next_cursor = chunks[-1]["id"] if chunks and has_more else None
                
                log_info(f"Found {len(chunks)} chunks" + (f" for content_id '{content_id}'" if content_id else "") +
                        (f" (limit={limit}, cursor={cursor})" if limit or cursor else ""))
                
                return {
                    "chunks": chunks,
                    "next_cursor": next_cursor,
                    "has_more": has_more
                }
                
        except Exception as e:
            logger.error(f"Error listing chunks: {e}")
            return []
