from typing import Union
from collections.abc import Callable
from pathlib import PurePath
import asyncio
import aiofiles
from navconfig.logging import logging
from ..interfaces import TemplateSupport
from ..interfaces.databases.documentdb import DocumentDBSupport
from .flow import FlowComponent
from ..utils.functions import is_empty
from ..exceptions import FileError, ComponentError, DataNotFound
from ..utils.json import json_decoder, json_encoder


# Disable Mongo Logging
logging.getLogger("pymongo").setLevel(logging.INFO)


class DocumentDBQuery(DocumentDBSupport, TemplateSupport, FlowComponent):
    """
    DocumentDBQuery.

    DocumentDBQuery is a component that interacts with a DocumentDB database using pymongo.

    Returns json-object representation of the query result.


        Example:

    |---|---|---|
    | version | No | version of component |


        Example:

        | Name | Required | Summary |
    |---|---|---|
    | version | No | version of component |


        Example:

        ```yaml
          DocumentDBQuery:
          schema: networkninja
          tablename: batches
          query:
          data.metadata.type: form_data
          data.metadata.timestamp:
          $gte: 1743670800.0
          $lte: 1743681600.999999
        ```
    """
    _version = "1.0.0"
    driver: str = 'mongo'

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ):
        self._query: dict = {}
        # Collection:
        self._collection: str = kwargs.pop("collection_name", None)
        if not self._collection:
            self._collection = kwargs.pop("tablename", None)
        if not self._collection:
            raise ValueError(
                f"{__name__}: Missing Collection Name or Table Name"
            )
        self._database: str = kwargs.pop("database", None)
        if not self._database:
            self._database = kwargs.pop("schema", kwargs.get('program', None))
        if not self._database:
            raise ValueError(
                f"{__name__}: Missing Database Name or Schema Name"
            )
        self.query: Union[str, dict] = kwargs.get('query', None)
        super().__init__(
            loop=loop,
            job=job,
            stat=stat,
            **kwargs
        )
        if self.as_string is True:
            self.infer_types = True

    async def open_queryfile(self, file: PurePath, **kwargs) -> str:
        if file.exists() and file.is_file():
            content = None
            # open SQL File:
            async with aiofiles.open(file, "r+") as afp:
                content = await afp.read()
                # check if we need to replace masks
            if hasattr(self, "masks"):
                content = self.mask_replacement(content)
            if self.use_template is True:
                content = self._templateparser.from_string(content, kwargs)
            return content
        else:
            raise FileError(
                f"{__name__}: Missing Query File: {file}"
            )

    async def start(self, **kwargs) -> bool:
        """start.

        Start the DocumentDBQuery component.
        """
        await super(DocumentDBQuery, self).start(**kwargs)
        if hasattr(self, "conditions"):
            self.set_conditions("conditions")
        if hasattr(self, "query_file") or hasattr(self, "query_file"):
            query = self.query_file
            qry = await self.open_queryfile(query)
        elif isinstance(self.query, PurePath):
            qry = await self.open_queryfile(self.query)
        else:
            if isinstance(self.query, str):
                if hasattr(self, "masks"):
                    qry = self.mask_replacement(self.query)
                if "{" in self.query and hasattr(self, "conditions"):
                    qry = self.query.format(**self.conditions)
                else:
                    qry = self.query
            elif isinstance(self.query, dict):
                # Doing condition replacement for every element in the query
                qry = {}
                for key, value in self.query.items():
                    if isinstance(value, str):
                        if hasattr(self, "masks"):
                            value = self.mask_replacement(value)
                        if "{" in value and hasattr(self, "conditions"):
                            value = value.format(**self.conditions)
                    qry[key] = value
            else:
                raise ValueError(
                    f"{__name__}: Missing or Invalid Query or Query File"
                )
        try:
            if isinstance(qry, str):
                self._query = json_decoder(qry)
            else:
                self._query = qry
        except Exception as err:
            raise ComponentError(
                f"{__name__}: Error decoding Query: {err}"
            )
        return True

    async def close(self):
        pass

    async def run(self):
        try:
            db = self.default_connection(
                driver=self.driver, credentials=self.credentials
            )
        except Exception as e:
            self._logger.error(
                f"Error getting Default DocumentDB Connection: {e!s}"
            )
            raise
        try:
            async with await db.connection() as conn:
                if conn.is_connected() is not True:
                    raise ComponentError(
                        f"DB Error: driver {self.driver} is not connected."
                    )
                await conn.use(self._database)
                # print(
                #     ':: Count > ',
                #     await conn.count_documents(collection_name=self._collection)
                # )
                result, error = await conn.query(
                    collection_name=self._collection,
                    query=self._query,
                )
                if error:
                    raise ComponentError(
                        f"Error executing Query: {error}"
                    )
                if is_empty(result):
                    raise DataNotFound(
                        f"Data not found for Query: {self._query}"
                    )

                if self.as_dataframe is True:
                    self._result = await self.get_dataframe(result)
                else:
                    self._result = result
            # self.add_metric(
            #     "Query", json_encoder(self._query)
            # )
            self.add_metric(
                "Database", str(self._database)
            )
            self.add_metric(
                "Collection", str(self._collection)
            )
            self.add_metric(
                "NUM_RESULTS", len(self._result)
            )
            return self._result
        except DataNotFound:
            raise
        except ComponentError:
            raise
        except Exception as e:
            raise ComponentError(
                f"Error connecting to DocumentDB: {e}"
            )
