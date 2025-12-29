from collections.abc import Callable
import asyncio
import random
import httpx
import pandas as pd
from tqdm.asyncio import tqdm
from bs4 import BeautifulSoup
from ...exceptions import ComponentError, ConfigError
from ...interfaces import HTTPService, SeleniumService
from ...interfaces.http import ua
from ..flow import FlowComponent
from .parsers import (
    CostcoScrapper,
)


class ServiceScrapper(FlowComponent, SeleniumService, HTTPService):
    """
    Service Scraper Component

    Overview:

    Pluggable component for scrapping several services and sites using different scrapers.

    :widths: auto

    | url_column (str)      |   Yes    | Name of the column containing URLs to scrape (default: 'search_url')                                |
    | wait_for (tuple)      |   No     | Element to wait for before scraping (default: ('class', 'company-overview'))                        |

    Return:
    - DataFrame with company information

    |---|---|---|
    | version | No | version of component |


        Example:

        | Name | Required | Summary |
    |---|---|---|
    | version | No | version of component |


        Example:

        ```yaml
          ServiceScrapper:
          # attributes here
        ```
    """
    _version = "1.0.0"

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ) -> None:
        self.info_column: str = kwargs.get('column_name', 'url')
        self.scrapper_name: str = kwargs.get('scrapper', ['costco'])
        self.scrapper_class: Callable = None
        self._scrapper_func: str = kwargs.get('function', 'special_events')
        self.wait_for: tuple = kwargs.get('wait_for', ('class', 'company-overview'))
        self._counter: int = 0
        self.use_proxy: bool = True
        self._free_proxy: bool = False
        self.paid_proxy: bool = True
        self.chunk_size: int = kwargs.get('chunk_size', 100)
        self.concurrently: bool = kwargs.get('concurrently', False)
        self.task_parts: int = kwargs.get('task_parts', 10)
        super().__init__(loop=loop, job=job, stat=stat, **kwargs)
        # Headers configuration
        self.headers: dict = {
            "Accept": self.accept,
            "TE": "trailers",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": random.choice(ua),
            **kwargs.get('headers', {})
        }
        self._free_proxy = False

    def split_parts(self, task_list, num_parts: int = 5) -> list:
        part_size, remainder = divmod(len(task_list), num_parts)
        parts = []
        start = 0
        for i in range(num_parts):
            # Distribute the remainder across the first `remainder` parts
            end = start + part_size + (1 if i < remainder else 0)
            parts.append(task_list[start:end])
            start = end
        return parts

    async def _processing_tasks(self, tasks: list) -> pd.DataFrame:
        """Process tasks concurrently."""
        results = []
        total_tasks = len(tasks)
        # Overall progress bar
        with tqdm(total=total_tasks, desc="Scraping Progress", unit="task") as pbar_total:
            if self.concurrently is False:
                # run every task in a sequential manner:
                for task in tasks:
                    try:
                        idx, row = await task
                        results.append((idx, row))  # Append as tuple (idx, row)
                        await asyncio.sleep(
                            random.uniform(0.25, 1.5)
                        )
                    except Exception as e:
                        self._logger.error(f"Task error: {str(e)}")
                        results.append((idx, row))  # Store the failure result
                    finally:
                        pbar_total.update(1)
            else:
                for chunk in self.split_parts(tasks, self.task_parts):
                    result = await asyncio.gather(*chunk, return_exceptions=False)
                    results.extend(result)
                # Convert results to DataFrame
        if not results:
            return pd.DataFrame()

        indices, data_dicts = zip(*results) if results else ([], [])
        df = pd.DataFrame(data_dicts, index=indices)
        return df

    async def start(self, **kwargs) -> bool:
        """Initialize the component and validate required parameters."""
        if self.previous:
            self.data = self.input

        if not isinstance(self.data, pd.DataFrame):
            raise ComponentError(
                "Input must be a DataFrame", status=404
            )

        if self.info_column not in self.data.columns:
            raise ConfigError(
                f"Column {self.info_column} not found in DataFrame"
            )

        return True

    async def _start_scrapping(self, idx, row):
        try:
            async with self._semaphore:
                url = row[self.info_column]
                self._logger.debug(
                    f"Scraping URL: {url}"
                )
                async with self.scrapper_class as scrapper:
                    response = await scrapper.get(url, headers=self.headers)
                    if response:
                        try:
                            fn = getattr(scrapper, self._scrapper_func, 'scrapping')
                            idx, row = await fn(response, idx, row)
                        except Exception as err:
                            print(' Exception caught > ', err)
                            return idx, row
            return idx, row
        except Exception as err:
            print(' Exception caught > ', err)
            raise ComponentError(
                f"Error while scrapping: {err}"
            )

    def _get_scrapper(self):
        """Get the scrapper class."""
        try:
            if self.scrapper_name == 'costco':
                return CostcoScrapper()
            else:
                return None
        except Exception as err:
            print(err)
            raise ConfigError(
                f"Error while getting scrapper: {err}"
            )

    async def run(self):
        """Execute scraping for requested URL in the DataFrame."""
        # function that import the specified scrapper
        try:
            self.scrapper_class = self._get_scrapper()
        except Exception as err:
            raise ConfigError(
                f"Error while getting scrapper: {err}"
            )
        httpx_cookies = self.get_httpx_cookies(
            domain=self.scrapper_class.domain, cookies=self.cookies
        )
        self.scrapper_class.cookies = httpx_cookies
        self.scrapper_class.set_columns(self.data)
        if not self.scrapper_class:
            raise ConfigError(
                "No valid scrapper were found or provided in configuration"
            )
        tasks = [
            self._start_scrapping(
                idx, row
            ) for idx, row in self.data.iterrows()
        ]
        df = await self._processing_tasks(tasks)
        self._result = df
        self._print_data_(self._result, 'Scrapper Results')
        return self._result

    async def close(self):
        """Clean up resources."""
        return True
