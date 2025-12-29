import asyncio
import json
import random
from collections.abc import Callable
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd
from navconfig import config
from navconfig.logging import logging

from ..exceptions import ComponentError, ConfigError
from ..interfaces import HTTPService, SeleniumService
from ..interfaces.http import ua
from .flow import FlowComponent

try:  # pragma: no cover - optional dependency provided by ai-parrot package
    from parrot.tools.scraping import WebScrapingTool
except ModuleNotFoundError as exc:  # pragma: no cover - handled at runtime
    WebScrapingTool = None
    _IMPORT_ERROR: Optional[ModuleNotFoundError] = exc
else:  # pragma: no cover - only executed when dependency is available
    _IMPORT_ERROR = None


class DispatchMe(FlowComponent, SeleniumService, HTTPService):
    """
    Automation component for Dispatch (dispatch.me) recruiting data.

    |---|---|---|
    | version | No | version of component |


        Example:

        | Name | Required | Summary |
    |---|---|---|
    | version | No | version of component |


        Example:

        ```yaml
          DispatchMe:
          # attributes here
        ```
    """
    _version = "1.0.0"

    search_path: dict = {
        'recruit': "/v3/search/recruit",
        'account_organizations': '/v4/search/account_organizations'
    }

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs: Any,
    ) -> None:
        self.headless: bool = kwargs.get("headless", True)
        self.browser: str = kwargs.get("browser", "chrome")
        self.driver_type: str = kwargs.get("driver_type", "selenium")
        self.limit: int = int(kwargs.get("limit", 100))
        self.sort: str = kwargs.get("sort", "distance")
        self.last_job_activity: str = kwargs.get("last_job_activity", "anytime")
        self._base_api: str = kwargs.get("api_base", "https://wfm-api.dispatch.me")
        self._timeout: float = kwargs.get("timeout", 30)
        self.zipcode_column: str = kwargs.pop("zipcode_column", "zipcode")
        self.search_by: str = kwargs.get('search_by', 'recruit')
        default_filters: Dict[str, Any] = {
            "job_zip": kwargs.get("zipcode", ""),
            "radius": kwargs.get("radius", ""),
            "last_job_activity": kwargs.get("last_job_activity", self.last_job_activity),
        }
        statuses = kwargs.get("statuses")
        if statuses is not None:
            default_filters["status[]"] = statuses
        else:
            default_filters["status[]"] = ["Prospect", "On Hold"]
        provided_filters: Dict[str, Any] = kwargs.get("filters", {})
        self.filters: Dict[str, Any] = {**default_filters, **provided_filters}
        # Allow overrides for credentials
        self._username: Optional[str] = kwargs.get("username")
        self._password: Optional[str] = kwargs.get("password")
        self._flow_steps: Optional[List[Dict[str, Any]]] = kwargs.get("flow_steps")
        self._scraping_tool: Optional[Any] = None
        self._driver = None
        super().__init__(loop=loop, job=job, stat=stat, **kwargs)

    def _resolve_credentials(self) -> tuple[str, str]:
        username = self._username or config.get("DISPATCHME_USERNAME")
        password = self._password or config.get("DISPATCHME_PASSWORD")
        if not username:
            raise ConfigError("DispatchMe: Missing DISPATCHME_USERNAME credential")
        if not password:
            raise ConfigError("DispatchMe: Missing DISPATCHME_PASSWORD credential")
        return username, password

    def _default_flow(self) -> List[Dict[str, Any]]:
        username, password = self._resolve_credentials()
        return [
            {
                "action": "navigate",
                "url": "https://manage.dispatch.me/login",
                "description": "Dispatch login page",
            },
            {
                "action": "authenticate",
                "method": "form",
                "username_selector": "input[name='email']",
                "username": username,
                "enter_on_username": True,
                "password_selector": "input[name='password']",
                "password": password,
                "submit_selector": "button[type='submit']",
            },
            {
                "action": "wait",
                "timeout": 2,
                "condition_type": "url_is",
                "condition": "https://manage.dispatch.me/providers/list",
                "description": "Wait until redirected to providers list",
            },
        ]

    async def start(self, **kwargs: Any) -> bool:
        if self.previous:
            self.data = self.input
        if WebScrapingTool is None:
            raise ComponentError(
                "DispatchMe requires ai-parrot's WebScrapingTool."
                f" Install ai-parrot package: {_IMPORT_ERROR}"
            )

        # Ensure flow definition exists
        if not self._flow_steps:
            self._flow_steps = self._default_flow()
        # Prepare headers for HTTP requests later
        self.headers = {
            "Accept": "application/json",
            "User-Agent": random.choice(ua),
        }
        return True

    async def _execute_flow(self) -> Dict[str, Any]:
        if self._scraping_tool is None:
            tool_args = {
                "headless": self.headless,
                "browser": self.browser,
                "driver_type": self.driver_type,
            }
            try:
                self._scraping_tool = WebScrapingTool(**tool_args)
            except Exception as exc:  # pragma: no cover
                raise ComponentError(
                    f"DispatchMe: Unable to initialize WebScrapingTool: {exc}"
                ) from exc
        try:
            result = await self._scraping_tool._execute(steps=self._flow_steps)
        except Exception as exc:  # pragma: no cover
            raise ComponentError(
                f"DispatchMe: WebScrapingTool flow failed: {exc}"
            ) from exc
        try:
            # Try to capture driver reference
            self._driver = getattr(self._scraping_tool, "driver", None)
        except Exception as e:
            raise ComponentError(
                f"DispatchMe: Unable to access Selenium driver: {e}"
            ) from e
        return result

    def _build_query_params(self, page: int) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "job_zip": self.filters.get("job_zip", ""),
            "last_job_activity": self.filters.get(
                "last_job_activity", self.last_job_activity
            ),
            "limit": self.limit,
            "page": page,
            "radius": self.filters.get("radius", ""),
            "sort": self.filters.get("sort", self.sort),
        }

        for key, value in self.filters.items():
            if key in params:
                continue
            params[key] = value
        return params

    async def _fetch_page(
        self, client: httpx.AsyncClient, page: int
    ) -> Dict[str, Any]:
        params = self._build_query_params(page)
        search_path = self.search_path.get(self.search_by, self.search_path.get('recruit'))
        response = await client.get(search_path, params=params)
        response.raise_for_status()
        return response.json()

    async def _fetch_all_pages(
        self, cookies: Dict[str, str], authorization: str
    ) -> List[Dict[str, Any]]:
        headers = {
            "Authorization": str(authorization),
            **self.headers,
        }
        # create the Cookies from dict cookies:
        cookie_jar = httpx.Cookies()
        for key, value in cookies.items():
            if value is not None:
                cookie_jar.set(key, str(value))
        async with httpx.AsyncClient(
            base_url=self._base_api,
            headers=headers,
            cookies=cookie_jar,
            timeout=self._timeout,
        ) as client:
            all_records: List[Dict[str, Any]] = []
            page = 0
            total_pages: Optional[int] = None

            while True:
                payload = await self._fetch_page(client, page)
                records = payload.get("account_organizations", [])
                if records:
                    all_records.extend(records)
                meta = payload.get("meta", {})
                total_pages = meta.get("pages", total_pages)

                if total_pages is None:
                    if not records:
                        break
                else:
                    if page >= total_pages - 1:
                        break
                page += 1

            return all_records

    async def run(self) -> pd.DataFrame:
        try:
            await self._execute_flow()
        except Exception as exc:  # pragma: no cover
            raise ComponentError(
                f"DispatchMe: Failed to execute flow: {exc}"
            ) from exc
        try:
            cookies = self._scraping_tool.extracted_cookies[0]
            authorization = self._scraping_tool.extracted_authorization
        except Exception as exc:  # pragma: no cover
            raise ComponentError(
                f"DispatchMe: Failed to prepare API access: {exc}"
            ) from exc
        if not authorization:
            raise ComponentError(
                "DispatchMe: Unable to capture authorization token from browser session"
            )
        if isinstance(self.data, pd.DataFrame):
            # iterate over all zipcodes in the dataframe:
            zipcodes = self.data[self.zipcode_column].dropna().unique().tolist()
            all_records: List[Dict[str, Any]] = []
            for zipcode in zipcodes:
                self.filters["job_zip"] = str(zipcode)
                try:
                    records = await self._fetch_all_pages(cookies, authorization)
                    all_records.extend(records)
                except httpx.HTTPError as exc:  # pragma: no cover
                    logging.getLogger(__name__).error(
                        f"DispatchMe: API request failed for zipcode {zipcode}: {exc}"
                    )
                except Exception as exc:  # pragma: no cover
                    logging.getLogger(__name__).error(
                        f"DispatchMe: Failed to process API response for zipcode {zipcode}: {exc}"
                    )
            self._result = pd.DataFrame(all_records)
            return self._result
        else:
            try:
                records = await self._fetch_all_pages(cookies, authorization)
            except httpx.HTTPError as exc:  # pragma: no cover
                raise ComponentError(
                    f"DispatchMe: API request failed: {exc}"
                ) from exc
            except Exception as exc:  # pragma: no cover
                print('RESPONSE > ', exc)
                raise ComponentError(
                    f"DispatchMe: Failed to process API response: {exc}"
                ) from exc

            self._result = pd.DataFrame(records)
        return self._result

    async def close(self) -> None:
        if self._scraping_tool:
            close_method = getattr(self._scraping_tool, "close", None)
            if close_method:
                try:
                    if asyncio.iscoroutinefunction(close_method):
                        await close_method()
                    else:
                        close_method()
                except Exception:
                    pass
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
        self._scraping_tool = None
        self._driver = None
