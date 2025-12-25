import asyncio
from abc import ABC, abstractmethod
from os import getenv
from typing import Literal

import httpx

from .errors import *
from .models.auth import JWTAuth
from .models.company import Company, Subdepartment, Template
from .models.unit import PaginatedUnits, Unit, UnregisteredUnit, UnitTag, UnitPhoto
from .models.user import User, UserStatus, InvitedUser


class BaseBreezewayClient(ABC):
    HEADERS = {'accept': 'application/json'}

    def __init__(self, client_id: str, client_secret: str, base_url: str, company_id: int | None = None):
        base_url = base_url or 'https://api.breezeway.io'
        client_id = client_id or getenv('BREEZEWAY_CLIENT_ID')
        client_secret = client_secret or getenv('BREEZEWAY_CLIENT_SECRET')
        if not client_id or not client_secret:
            raise AuthenticationError('client_id and client_secret are required either as parameters or environment variables'
                             'BREEZEWAY_CLIENT_ID and BREEZEWAY_CLIENT_SECRET')
        self.base_url: str = base_url.rstrip('/')
        self._company_id: int | None = int(company_id) if company_id else company_id
        self.auth: JWTAuth = JWTAuth(self.base_url, client_id, client_secret)

    @abstractmethod
    def _request(self, method: str, endpoint: str, query_params: dict = None, payload: dict | list= None) -> dict:
        pass

    @staticmethod
    def _filter_query_params(query_params: dict | list | None) -> dict:
        if query_params is None:
            return {}
        return {key: value for key, value in query_params.items() if value is not None}

    def _get_user_data(self, status: UserStatus | None = None) -> dict:
        endpoint = '/public/inventory/v1/people'
        query_params = {'status': status.value if status else None}
        return self._request('GET', endpoint, query_params=query_params)

    @staticmethod
    def _handle_response(resp: httpx.Response) -> None:
        if 'error' not in resp.json():
            return None
        if resp.json()['error'] == 'inactive client':
            raise AuthenticationError('Inactive client. Check your credentials.')
        if resp.status_code == 403:
            raise UnauthorizedError(resp.json()['description'])
        if resp.status_code == 404:
            raise NotFoundError('Resource not found. Are you using the correct endpoint?')
        if resp.status_code == 429:
            raise RateLimitExceeded(resp.json())

        if resp.json() and 'description' in resp.json():
            raise APIClientError(f"API error: {resp.json()['description']}")
        raise APIClientError()

    @property
    def authenticated(self) -> bool:
        return self.auth.authenticated

    @property
    def company_id(self) -> int:
        if self._company_id:
            return self._company_id
        companies = self.companies()
        if not companies:
            raise NoCompaniesError()
        elif len(companies) > 1:
            raise MultipleCompaniesError()
        self._company_id = companies[0].id
        return self._company_id

    @company_id.setter
    def company_id(self, value: int):
        self._company_id = value

    def companies(self) -> list[Company]:
        """Get all companies associated with the client."""
        endpoint = '/public/inventory/v1/companies'
        return [Company.model_validate(company) for company in self._request('GET', endpoint)]

    def create_unit(self, unit: UnregisteredUnit) -> Unit:
        """Create a new unit."""
        endpoint = '/public/inventory/v1/property'
        payload = unit.model_dump()
        return Unit.model_validate(self._request('POST', endpoint, payload=payload)).attach_client(self)

    def inactive_users(self) -> list[User]:
        """Get a list of all inactive users."""
        return [User.model_validate(user) for user in self._get_user_data(status=UserStatus.INACTIVE)]

    def invited_users(self) -> list[InvitedUser]:
        """Get a list of all invited users."""
        return [InvitedUser.model_validate(user).attach_client(self) for user in self._get_user_data(status=UserStatus.INVITED)]

    def paginated_units(self, company_id: int | None = None, limit: int | None = None, page: int | None = None, sort_by: str | None = None, sort_order: Literal['desc', 'asc'] | None = None) -> PaginatedUnits:
        """
        Get a paginated list of units.
        Company ID is required for clients with multi-company access.
        """
        endpoint = 'public/inventory/v1/property'
        query_params = {
            'company_id': company_id,
            'limit': limit,
            'page': page,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        paginated_units = PaginatedUnits.model_validate(self._request('GET', endpoint, query_params=query_params))
        for unit in paginated_units.results:
            unit.attach_client(self)
        return paginated_units

    def set_default_photo_for_unit(self, unit: Unit, photo: UnitPhoto) -> Unit:
        """Set a default photo for a unit."""
        endpoint = f'public/inventory/v1/property/{unit.id}/default_photo'
        payload = {'photo_id': photo.id}
        return Unit.model_validate(self._request('PATCH', endpoint, payload=payload))

    def subdepartments(self, company_id: int | None = None, reference_company_id: str | None = None) -> list[Subdepartment]:
        """
        Get a list of all subdepartments associated with the company.
        Company ID is required for clients with multi-company access.
        """
        endpoint = 'public/inventory/v1/companies/subdepartments'
        query_params = {
            'company_id': company_id,
            'reference_company_id': reference_company_id
        }
        return [Subdepartment.model_validate(subdepartment) for subdepartment in self._request('GET', endpoint, query_params=query_params)]

    def templates(self, company_id: int | None = None) -> list[Template]:
        """
        Get a list of all templates associated with the company.
        Company ID is required for clients with multi-company access.
        """
        endpoint = 'public/inventory/v1/companies/templates'
        query_params = {'company_id': company_id}
        return [Template.model_validate(template) for template in self._request('GET', endpoint, query_params=query_params)]

    def unit(self, unit_id: int) -> Unit:
        """Get a unit by its ID."""
        endpoint = f'public/inventory/v1/property/{unit_id}'
        return Unit.model_validate(self._request('GET', endpoint)).attach_client(self)

    def units(self, company_id: int | None = None, sort_by: str | None = None, sort_order: Literal['desc', 'asc'] | None = None) -> list[Unit]:
        """
        Get a list of all units associated with the company.
        Company ID is required for clients with multi-company access.
        """
        paginated_units = self.paginated_units(company_id=company_id, sort_by=sort_by, sort_order=sort_order)
        units = paginated_units.results
        for page in range(2, paginated_units.total_pages + 1):
            units += self.paginated_units(company_id=company_id, page=page, sort_by=sort_by, sort_order=sort_order).results
        return [unit.attach_client(self) for unit in units]

    def unit_tags(self, company_id: int | None = None) -> list[UnitTag]:
        """
        List property tags configured for a Breezeway company; creation of company tags must be performed within the app.
        company_id is required for clients with multi-company access.
        """
        endpoint = f'public/inventory/v1/property/tags'
        query_params = {'company_id': company_id}
        return [UnitTag.model_validate(tag) for tag in self._request('GET', endpoint, query_params=query_params)]

    def user(self, user_id: int) -> User:
        """Get a user by their ID."""
        endpoint = f'public/inventory/v1/people/{user_id}'
        return User.model_validate(self._request('GET', endpoint)).attach_client(self)

    def users(self) -> list[User]:
        """
        Get a list of all users associated with the company.
        """
        return [User.model_validate(user).attach_client(self) for user in self._get_user_data()]


class BreezewayClient(BaseBreezewayClient):
    def __init__(self, client_id=None, client_secret=None, base_url=None, company_id: int | None = None):
        super().__init__(client_id, client_secret, base_url, company_id)
        self.client = httpx.Client(auth=self.auth, base_url=self.base_url, headers=self.HEADERS)

    def _request(self, method: str, endpoint: str, query_params: dict | None = None, payload: dict | list = None) -> dict:
        resp = self.client.request(method, endpoint, json=payload, params=self._filter_query_params(query_params))
        resp.read()
        self._handle_response(resp)
        return resp.json()


class AsyncBreezewayClient(BaseBreezewayClient):
    def __init__(self, client_id=None, client_secret=None, base_url=None, company_id: int | None = None):
        super().__init__(client_id, client_secret, base_url, company_id)
        self.client = httpx.AsyncClient(auth=self.auth, base_url=self.base_url, headers=self.HEADERS)

    async def _request(self, method: str, endpoint: str, query_params: dict | None = None, payload: dict | list = None) -> dict:
        resp = await self.client.request(method, endpoint, json=payload, params=self._filter_query_params(query_params))
        await resp.aread()
        self._handle_response(resp)
        return resp.json()


    async def units(self, company_id: int | None = None, sort_by: str | None = None, sort_order: Literal['desc', 'asc'] | None = None) -> list[Unit]:
        paginated_units = await self.paginated_units(company_id=company_id, sort_by=sort_by, sort_order=sort_order)
        units = paginated_units.results
        tasks = [
            self.paginated_units(company_id=company_id, page=page, sort_by=sort_by, sort_order=sort_order)
            for page in range(2, paginated_units.total_pages + 1)
        ]
        for result in await asyncio.gather(*tasks):
            units += result.results
        return units
