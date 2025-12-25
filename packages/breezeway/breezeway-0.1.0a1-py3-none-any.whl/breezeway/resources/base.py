from typing import Any, Literal, Mapping
import httpx


class BaseResource:

    def __init__(self, base_url: str):
        self.base_url = base_url

    def _build_request(
            self,
            method: Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
            endpoint: str,
            params: Mapping[str, Any] | None = None,
            payload: Mapping[str, Any] | None = None
    ) -> httpx.Request:

        return httpx.Request(
            method=method,
            url=f'{self.base_url}{endpoint}',
            params=params,
            json=payload
        )