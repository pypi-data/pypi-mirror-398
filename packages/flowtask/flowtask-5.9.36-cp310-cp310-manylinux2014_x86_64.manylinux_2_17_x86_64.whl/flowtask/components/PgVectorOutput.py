from collections.abc import Callable
import asyncio
from typing import List
from parrot.stores.postgres import PgVectorStore
from parrot.stores.models import Document
from .flow import FlowComponent
from ..exceptions import DataNotFound, ComponentError, ConfigError
from ..conf import default_sqlalchemy_pg
from ..interfaces.credentials import CredentialsInterface


class PgVectorOutput(CredentialsInterface, FlowComponent):
    """
    Saving Parrot Documents on a Postgres Database using PgVector.

    This component is designed to save documents into a PostgreSQL database using PgVector extension
    with Parrot's vector store implementation (no Langchain dependency).

    Example:

    |---|---|---|
    | version | No | version of component |


        Example:

        | Name | Required | Summary |
    |---|---|---|
    | version | No | version of component |


        Example:

        ```yaml
          PgVectorOutput:
          credentials:
          dsn:
          table: lg_products
          schema: lg
          embedding_model:
          model: thenlper/gte-base
          model_type: transformers
          id_column: "id"
          embedding_column: 'embedding'
          pk: source_type
          create_table: true
          upsert: true
        ```
    """
    _version = "1.0.0"
    _credentials: dict = {
        "dsn": str,
    }

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ):
        self.upsert: bool = kwargs.pop('upsert', True)
        self.pk: str = kwargs.pop('pk', 'source_type')
        self._embedding_model: dict = kwargs.get('embedding_model', None)
        self.embedding_column: str = kwargs.pop('embedding_column', kwargs.pop('vector_column', 'embedding'))
        self.table: str = kwargs.pop('table', 'documents')
        self.schema: str = kwargs.pop('schema', 'public')
        self.id_column: str = kwargs.pop('id_column', 'id')
        self.dimension: int = kwargs.pop('dimension', 768)
        self.create_table: dict = kwargs.pop('create_table', {})
        self.prepare_columns: bool = kwargs.pop('prepare_columns', True)
        self.document_column: str = kwargs.pop('document_column', 'document')
        self.metadata_column: str = kwargs.pop('metadata_column', 'cmetadata')
        self.text_column: str = kwargs.pop('text_column', 'text')
        super().__init__(loop=loop, job=job, stat=stat, **kwargs)

    async def start(self, **kwargs):
        if self.previous:
            self.data = self.input
        await super().start(**kwargs)
        self.processing_credentials()
        # DSN
        if not self.credentials:
            self._dsn = default_sqlalchemy_pg
        else:
            self._dsn = self.credentials.get('dsn', default_sqlalchemy_pg)
        if not self.data:
            raise DataNotFound(
                "List of Documents is Empty."
            )
        if not isinstance(self.data, list):
            raise ComponentError(
                f"Incompatible kind of data received, expected a *list* of documents, receives {type(self.data)}"
            )
        return True

    async def close(self):
        pass

    async def _create_collection(self, store: PgVectorStore):
        """
        Create the collection (table) in the PostgreSQL database using Parrot's method.
        """
        creation = self.create_table.get('create', True)
        if not creation:
            return
            
        if not await store.collection_exists(table=self.table, schema=self.schema):
            print(f"Creating collection {self.schema}.{self.table}...")
            
            # Use Parrot's create_collection method
            await store.create_collection(
                table=self.table,
                schema=self.schema,
                dimension=self.dimension,
                id_column=self.id_column,
                embedding_column=self.embedding_column,
                document_column=self.document_column,
                metadata_column=self.metadata_column
            )
            print(f"✅ Collection {self.schema}.{self.table} created successfully")

    async def _prepare_embedding_table(self, store: PgVectorStore):
        """
        Prepare the embedding table using Parrot's prepare_embedding_table method.
        """
        if not self.prepare_columns:
            return
            
        print(f"Preparing embedding table {self.schema}.{self.table}...")
        
        # Use Parrot's connection to prepare the table
        async with store.session() as session:
            await store.prepare_embedding_table(
                table=self.table,
                schema=self.schema,
                conn=session,
                embedding_column=self.embedding_column,
                document_column=self.document_column,
                metadata_column=self.metadata_column,
                text_column=self.text_column,
                id_column=self.id_column,
                dimension=self.dimension,
                create_all_indexes=True
            )
        print(f"✅ Embedding table {self.schema}.{self.table} prepared successfully")

    async def run(self):
        """
        Saving Parrot Documents on a Postgres Database using PgVector.
        """
        # Connecting to PostgreSQL using Parrot's PgVectorStore:
        _store = PgVectorStore(
            table=self.table,
            schema=self.schema,
            id_column=self.id_column,
            embedding_column=self.embedding_column,
            document_column=self.document_column,
            text_column=self.text_column,
            embedding_model=self._embedding_model,
            dsn=self._dsn,
            dimension=self.dimension,
            auto_initialize=True
        )
        
        self._result = None
        async with _store as store:
            print(f'Connecting to PostgreSQL... {store.is_connected()}')
            print(f"Processing table {self.schema}.{self.table}...")
            
            # Create collection if needed
            if self.create_table:
                await self._create_collection(store)
            
            # Prepare embedding columns if needed
            if self.prepare_columns:
                await self._prepare_embedding_table(store)
            
            # Verify collection exists
            if await store.collection_exists(table=self.table, schema=self.schema):
                # If upsert: delete existing documents with the same pk
                if hasattr(self, 'upsert') and self.upsert and self.pk:
                    print(f"Upserting: deleting existing documents with {self.pk}")
                    deleted_count = await store.delete_documents(
                        pk=self.pk,
                        values=[doc.metadata.get(self.pk) for doc in self.data if doc.metadata and self.pk in doc.metadata],
                        table=self.table,
                        schema=self.schema,
                        metadata_column=self.metadata_column
                    )
                    print(f"Deleted {deleted_count} existing documents")
                
                # Add documents to the store
                print(f"Adding {len(self.data)} documents to vector store...")
                await store.add_documents(
                    documents=self.data,
                    table=self.table,
                    schema=self.schema,
                    embedding_column=self.embedding_column,
                    content_column=self.document_column,
                    metadata_column=self.metadata_column
                )
                
                result = {
                    "vectorstore": f"{store!r}",
                    "table": f"{self.schema}.{self.table}",
                    "documents_added": len(self.data),
                    "embedding_column": self.embedding_column,
                    "schema": self.schema
                }
                print(f"✅ Successfully added {len(self.data)} documents to {self.schema}.{self.table}")
            else:
                raise DataNotFound(
                    f"Collection {self.schema}.{self.table} does not exist and could not be created."
                )
            
            self._result = result
        
        self.add_metric('DOCUMENTS_LOADED', len(self.data))
        return result
