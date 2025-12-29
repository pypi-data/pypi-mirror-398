import logging
from typing import Any

import aiohttp
import requests

from arpakitlib.ar_dict_util import combine_dicts
from arpakitlib.ar_http_request_util import async_make_http_request, sync_make_http_request


class BaseHTTPAPIClient:
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}
        self._logger = logging.getLogger(f"{self.__class__.__name__}")

    def _sync_make_http_request(
            self,
            *,
            method: str,
            url: str,
            headers: dict[str, Any] | None = None,
            **kwargs
    ) -> requests.Response:
        return sync_make_http_request(
            method=method,
            url=url,
            headers=combine_dicts(self.headers, (headers if headers is not None else {})),
            **kwargs
        )

    async def _async_make_http_request(
            self,
            *,
            method: str = "GET",
            url: str,
            headers: dict[str, Any] | None = None,
            **kwargs
    ) -> aiohttp.ClientResponse:
        return await async_make_http_request(
            method=method,
            url=url,
            headers=combine_dicts(self.headers, (headers if headers is not None else {})),
            **kwargs
        )

    def healthcheck(self) -> bool:
        raise NotImplemented()

    async def async_healthcheck(self) -> bool:
        raise NotImplemented()
