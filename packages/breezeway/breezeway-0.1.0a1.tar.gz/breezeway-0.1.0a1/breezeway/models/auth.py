import logging
import time
import typing

import httpx
from httpx import Request, Response

from breezeway.errors import AuthenticationError, RateLimitExceeded, APIClientError


class JWTAuth(httpx.Auth):
    HEADERS = {'accept': 'application/json'}

    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = 0

    @staticmethod
    def _handle_response(resp: httpx.Response) -> None:
        if resp.json() is None: # Breezeway returns 200 with empty body when client_secret is incorrect
            raise AuthenticationError()
        if 'error' not in resp.json():
            return None
        if resp.json()['error'] == 'inactive client':  # Cant check by code because breezeway returns 200
            raise AuthenticationError('Inactive client. Check your credentials.')
        if resp.status_code == 429:
            raise RateLimitExceeded(resp.json())
        raise APIClientError(resp.json()['error'])

    @property
    def authenticated(self) -> bool:
        return self._access_token is not None and self._refresh_token is not None

    def build_authentication_request(self) -> httpx.Request:
        url = self.base_url + '/public/auth/v1/'
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        return httpx.Request("POST", url, headers=self.HEADERS, json=payload)

    def build_refresh_token_request(self) -> httpx.Request:
        url = self.base_url + '/public/auth/v1/refresh'
        headers = self.HEADERS | {'authorization': f'JWT {self._refresh_token}'}
        return httpx.Request("POST", url, headers=headers)

    def _update_tokens(self, response: httpx.Response):
        response.raise_for_status()
        body = response.json()
        if not body or 'error' in body:
            logging.error(f"Authentication failed\n\t{body['error'] if 'error' in body else body}")
            raise RuntimeError('Authentication failed')
        self._token_expires_at = time.time() + 86400
        self._access_token = body['access_token']
        self._refresh_token = body['refresh_token']

    def sync_auth_flow(self, request: Request) -> typing.Generator[Request, Response, None]:
        if self._token_expires_at < time.time():  # if token is expired
            if self._refresh_token:
                response = yield self.build_refresh_token_request()
                response.read()
                self._handle_response(response)
                self._update_tokens(response)
            else:
                response = yield self.build_authentication_request()
                response.read()
                self._handle_response(response)
                self._update_tokens(response)
        request.headers['authorization'] = f'JWT {self._access_token}'
        yield request

    async def async_auth_flow(self, request: Request) -> typing.AsyncGenerator[Request, Response]:
        if self._token_expires_at < time.time():  # if token is expired
            if self._refresh_token:
                response = yield self.build_refresh_token_request()
                await response.aread()
                self._handle_response(response)
                self._update_tokens(response)
            else:
                response = yield self.build_authentication_request()
                await response.aread()
                self._handle_response(response)
                self._update_tokens(response)
        request.headers['authorization'] = f'JWT {self._access_token}'
        yield request
