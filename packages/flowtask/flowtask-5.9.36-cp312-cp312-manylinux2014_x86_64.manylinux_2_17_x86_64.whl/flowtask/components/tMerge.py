import asyncio
import pandas as pd
from typing import Any
from collections.abc import Callable
from querysource.exceptions import QueryException
from ..exceptions import ComponentError
from .flow import FlowComponent


class tMerge(FlowComponent):
    """
    tMerge

        Overview

            The tMerge class is a component for merging two DataFrames (or named Series objects) using a database-style join.
            It supports different join types such as 'inner', 'outer', 'left', 'right', and 'cross', allowing flexible merging
            configurations for complex data workflows.

        :widths: auto

            | df1              |   Yes    | The left DataFrame to join.                                               |
            | df2              |   Yes    | The right DataFrame to join.                                              |
            | type             |   No     | The type of join to perform (e.g., 'inner', 'outer'). Defaults to 'cross'.|
            | pd_args          |   No     | Additional arguments for the Pandas merge function, if any.               |

        Returns

            This component returns a DataFrame created by merging `df1` and `df2` based on the specified join type and arguments.
            It records metrics for the resulting DataFrame’s row and column counts. Any errors during merging are raised
            with detailed error messages, and additional debug information is available if debugging mode is enabled.


        Example:

    |---|---|---|
    | version | No | version of component |


        Example:

        | Name | Required | Summary |
    |---|---|---|
    | version | No | version of component |


        Example:

        ```yaml
          tMerge:
          depends:
          - QueryToPandas_1
          - QueryToPandas_2
          type: cross
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
        """Init Method."""
        self.df1: Any = None
        self.df2: Any = None
        self.type = kwargs.pop('type', 'cross')
        super(tMerge, self).__init__(loop=loop, job=job, stat=stat, **kwargs)

    async def start(self, **kwargs):
        if self.previous:
            self.data = self.input
        else:
            raise ComponentError("Data Not Found")
        try:
            self.df1 = self.previous[0].output()
        except IndexError as ex:
            name = self.depends[0]
            raise ComponentError(
                f"Missing LEFT Dataframe: {name}"
            ) from ex
        try:
            self.df2 = self.previous[1].output()
        except IndexError as ex:
            name = self.depends[1]
            raise ComponentError(
                "Missing RIGHT Dataframe"
            ) from ex
        return True

    async def close(self):
        pass

    async def run(self):
        try:
            if hasattr(self, "pd_args"):
                args = self.pd_args
            else:
                args = {}
            df = pd.merge(self.df1, self.df2, how=self.type, **args)
            self._result = df
            self.add_metric("NUM_ROWS", self._result.shape[0])
            self.add_metric("NUM_COLUMNS", self._result.shape[1])
            if self._debug:
                print("Debugging: tMerge ===")
                print(self._result)
                columns = list(self._result.columns)
                for column in columns:
                    t = self._result[column].dtype
                    print(
                        column, "->", t, "->", self._result[column].iloc[0]
                    )
            return self._result
        except (ValueError, KeyError) as err:
            raise ComponentError(f"tMerge Error: {err!s}") from err
        except Exception as err:
            raise ComponentError(f"tMerge error {err!s}") from err
