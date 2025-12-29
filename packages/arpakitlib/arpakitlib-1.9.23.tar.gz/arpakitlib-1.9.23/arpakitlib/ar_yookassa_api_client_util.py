from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import timedelta
from typing import Any

import aiohttp
import requests

from arpakitlib.ar_base_http_api_client_util import BaseHTTPAPIClient
from arpakitlib.ar_dict_util import combine_dicts
from arpakitlib.ar_enumeration_util import Enumeration
from arpakitlib.ar_http_request_util import sync_make_http_request, async_make_http_request
from arpakitlib.ar_type_util import raise_for_type

"""
https://yookassa.ru/developers/api
"""


class EasyYookassaAPIClient(BaseHTTPAPIClient):
    class PaymentStatuses(Enumeration):
        pending = "pending"
        waiting_for_capture = "waiting_for_capture"
        succeeded = "succeeded"
        canceled = "canceled"

    def __init__(self, *, secret_key: str, shop_id: int):
        super().__init__()
        self.secret_key = secret_key
        self.shop_id = shop_id
        self.headers = {"Content-Type": "application/json"}
        self._logger = logging.getLogger(f"{self.__class__.__name__}-{shop_id}")

    def _sync_make_http_request(
            self,
            *,
            method: str,
            url: str,
            headers: dict[str, Any] | None = None,
            not_raise_for_statuses_: list[int] | set[int] | None = None,
            **kwargs
    ) -> requests.Response:
        return sync_make_http_request(
            method=method,
            url=url,
            headers=combine_dicts(self.headers, (headers if headers is not None else {})),
            max_tries_=1,
            raise_for_status_=True,
            timeout_=timedelta(seconds=5),
            not_raise_for_statuses_=not_raise_for_statuses_,
            auth=(self.shop_id, self.secret_key),
            enable_logging_=False,
            **kwargs
        )

    async def _async_make_http_request(
            self,
            *,
            method: str = "GET",
            url: str,
            headers: dict[str, Any] | None = None,
            not_raise_for_statuses_: list[int] | set[int] | None = None,
            **kwargs
    ) -> aiohttp.ClientResponse:
        return await async_make_http_request(
            method=method,
            url=url,
            headers=combine_dicts(self.headers, (headers if headers is not None else {})),
            max_tries_=1,
            raise_for_status_=True,
            not_raise_for_statuses_=not_raise_for_statuses_,
            timeout_=timedelta(seconds=5),
            auth=aiohttp.BasicAuth(login=str(self.shop_id), password=self.secret_key),
            enable_logging_=False,
            **kwargs
        )

    def sync_create_payment(self, *, json_body: dict[str, Any]) -> dict[str, Any]:

        """
        json_body example
        json_body = {
            "amount": {
                "value": "2.0",
                "currency": "RUB"
            },
            "description": "description",
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/{get_tg_bot_username()}",
                "locale": "ru_RU"
            },
            "capture": True,
            "metadata": {},
            "merchant_customer_id": ""
        }
        """

        response = self._sync_make_http_request(
            method="POST",
            url="https://api.yookassa.ru/v3/payments",
            headers={"Idempotence-Key": str(uuid.uuid4())},
            json=json_body,
        )
        json_data = response.json()
        response.raise_for_status()
        return json_data

    def sync_get_payment(self, *, payment_id: str) -> dict[str, Any] | None:
        raise_for_type(payment_id, str)
        response = self._sync_make_http_request(
            method="GET",
            url=f"https://api.yookassa.ru/v3/payments/{payment_id}",
            not_raise_for_statuses_=[404]
        )
        json_data = response.json()
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return json_data

    async def async_create_payment(self, *, json_body: dict[str, Any]) -> dict[str, Any]:

        """
        json_body example
        json_body = {
            "amount": {
                "value": "2.0",
                "currency": "RUB"
            },
            "description": "description",
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/{get_tg_bot_username()}",
                "locale": "ru_RU"
            },
            "capture": True,
            "metadata": {},
            "merchant_customer_id": ""
        }
        """

        response = await self._async_make_http_request(
            method="POST",
            url="https://api.yookassa.ru/v3/payments",
            headers={"Idempotence-Key": str(uuid.uuid4())},
            json=json_body,
        )
        json_data = await response.json()
        response.raise_for_status()
        return json_data

    async def async_get_payment(self, *, payment_id: str) -> dict[str, Any] | None:
        raise_for_type(payment_id, str)
        response = await self._async_make_http_request(
            method="GET",
            url=f"https://api.yookassa.ru/v3/payments/{payment_id}",
            not_raise_for_statuses_=[404]
        )
        json_data = await response.json()
        if response.status == 404:
            return None
        response.raise_for_status()
        return json_data


YookassaAPIClient = EasyYookassaAPIClient


def __example():
    pass


async def __async_example():
    pass


if __name__ == '__main__':
    __example()
    asyncio.run(__async_example())
