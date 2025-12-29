import asyncio
from collections.abc import Callable
import math
import pandas as pd
from asyncdb import AsyncDB
from asyncdb.exceptions import (
    StatementError,
    DataError
)
from pathlib import Path
from .CopyTo import CopyTo
from ..interfaces.dataframes import PandasDataframe
from ..exceptions import (
    ComponentError,
    DataNotFound
)
from querysource.conf import (
    BIGQUERY_CREDENTIALS,
    BIGQUERY_PROJECT_ID
)


class CopyToBigQuery(CopyTo, PandasDataframe):
    """
    CopyToBigQuery.

    Overview

        This component allows copying data into a BigQuery table,
        using write functionality from AsyncDB BigQuery driver.

        :widths: auto

        | tablename    |   Yes    | Name of the table in                                   |
        |              |          | BigQuery                                               |
        | schema       |   Yes    | Name of the dataset                                    |
        |              |          | where the table is located                             |
        | truncate     |   Yes    | This option indicates if the component should empty    |
        |              |          | before copying the new data to the table. If set to    |
        |              |          | true, the table will be truncated before saving data.  |
        | use_buffer   |   No     | When activated, this option allows optimizing the      |
        |              |          | performance of the task when dealing with large        |
        |              |          | volumes of data.                                       |
        | credentials  |   No     | Path to BigQuery credentials JSON file                 |
        |              |          |                                                        |
        | project_id   |   No     | Google Cloud Project ID                                |
        |              |          |                                                        |


        Example:

    |---|---|---|
    | version | No | version of component |


        Example:

        | Name | Required | Summary |
    |---|---|---|
    | version | No | version of component |


        Example:

        ```yaml
          CopyToBigQuery:
          schema: hisense
          tablename: product_availability_all
        ```
    """
    _version = "1.0.0"
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ):
        self.pk = []
        self.truncate: bool = False
        self.data = None
        self._engine = None
        self.tablename: str = ""
        self.schema: str = ""  # dataset in BigQuery terminology
        self.use_chunks = False
        self._chunksize: int = kwargs.pop('chunksize', 10000)
        self._connection: Callable = None
        self._project_id: str = kwargs.pop('project_id', BIGQUERY_PROJECT_ID)
        self._credentials: str = kwargs.pop('credentials', BIGQUERY_CREDENTIALS)
        try:
            self.multi = bool(kwargs["multi"])
            del kwargs["multi"]
        except KeyError:
            self.multi = False
        super().__init__(
            loop=loop,
            job=job,
            stat=stat,
            **kwargs
        )
        self._driver: str = 'bigquery'

    def default_connection(self):
        """default_connection.

        Default Connection to BigQuery.
        """
        try:
            credentials = self._credentials
            if isinstance(credentials, Path):
                credentials = str(credentials)
            params: dict = {
                "credentials": credentials,
                "project_id": self._project_id
            }
            self._connection = AsyncDB(
                'bigquery',
                params=params,
                loop=self._loop
            )
            return self._connection
        except Exception as err:
            raise ComponentError(
                f"Error configuring BigQuery Connection: {err!s}"
            ) from err

    # Function to clean invalid float values
    def clean_floats(self, data):
        def sanitize_value(value):
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                return None
            return value

        if isinstance(data, dict):
            return {k: sanitize_value(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.clean_floats(item) for item in data]
        return data

    async def _create_table(self):
        """Create a Table in BigQuery if it doesn't exist."""
        try:
            async with await self._connection.connection() as conn:
                # First ensure dataset exists
                await conn.create_dataset(self.schema)

                # Infer schema from DataFrame
                bq_schema = []
                type_mapping = {
                    'object': 'STRING',
                    'string': 'STRING',
                    'int64': 'INTEGER',
                    'float64': 'FLOAT',
                    'bool': 'BOOLEAN',
                    'datetime64[ns]': 'TIMESTAMP',
                    'date': 'DATE'
                }

                for column, dtype in self.data.dtypes.items():
                    bq_type = type_mapping.get(str(dtype), 'STRING')
                    bq_schema.append({
                        "name": column,
                        "type": bq_type,
                        "mode": "NULLABLE"
                    })

                # If create_table has clustering fields, add them to the config
                table_config = {}
                if hasattr(self, 'create_table'):
                    if isinstance(self.create_table, dict) and 'pk' in self.create_table:
                        table_config['clustering_fields'] = self.create_table['pk']

                # Create the table with the inferred schema
                await conn.create_table(
                    table_id=self.tablename,
                    dataset_id=self.schema,
                    schema=bq_schema,
                    **table_config
                )

        except Exception as err:
            raise ComponentError(
                f"Error creating BigQuery table: {err}"
            ) from err

    async def _truncate_table(self):
        """Truncate the BigQuery table using the driver's built-in method."""
        async with await self._connection.connection() as conn:
            await self._connection.truncate_table(
                table_id=self.tablename,
                dataset_id=self.schema
            )

    async def _copy_dataframe(self):
        """Copy a pandas DataFrame to BigQuery."""
        try:
            # Clean NA/NaT values from string fields
            str_cols = self.data.select_dtypes(include=["string"])
            if not str_cols.empty:
                self.data[str_cols.columns] = str_cols.astype(object).where(
                    pd.notnull(str_cols), None
                )

            # Clean datetime fields - convert to ISO format strings
            datetime_types = ["datetime64", "datetime64[ns]"]
            datetime_cols = self.data.select_dtypes(include=datetime_types)
            if not datetime_cols.empty:
                for col in datetime_cols.columns:
                    # self.data[col] = self.data[col].apply(
                    #     lambda x: x.isoformat() if pd.notnull(x) else None
                    # )
                    self.data[col] = self.data[col].dt.tz_localize(None)
            async with await self._connection.connection() as conn:
                result = await conn.write(
                    data=self.data,
                    table_id=self.tablename,
                    dataset_id=self.schema,
                    use_pandas=True,
                    if_exists="append"
                )
                print('CopyTo: ', result)
        except StatementError as err:
            raise ComponentError(
                f"Statement error: {err}"
            ) from err
        except DataError as err:
            raise ComponentError(
                f"Data error: {err}"
            ) from err
        except Exception as err:
            raise ComponentError(
                f"{self.StepName} Error: {err!s}"
            ) from err

    async def _copy_iterable(self):
        """Copy an iterable to BigQuery."""
        try:
            async with await self._connection.connection() as conn:
                await conn.write(
                    data=self.data,
                    table_id=self.tablename,
                    dataset_id=self.schema,
                    use_pandas=False,
                    if_exists="append",
                    batch_size=self._chunksize
                )
        except Exception as err:
            raise ComponentError(
                f"Error copying iterable to BigQuery: {err}"
            ) from err
