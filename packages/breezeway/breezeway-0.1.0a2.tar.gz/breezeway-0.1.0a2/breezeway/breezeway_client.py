import asyncio
from abc import ABC, abstractmethod
from os import getenv
from typing import Unpack, NoReturn, Any

import httpx

from .errors import *
from .models.auth import JWTAuth
from .models.base import Paginated
from .models.company import Company, Subdepartment, Template
from .models.reservation import Reservation
from .models.unit import Unit, UnitTag, UnitPhoto
from .models.user import User, UserStatus
from .resources.company import CompanyResource
from .resources.reservation import ReservationListDict, ReservationResource
from .resources.unit import UnitCreateDict, UnitResource, UnitListDict, UnitListAllDict
from .resources.user import UserResource


class BaseBreezewayClient(ABC):
    HEADERS = {'accept': 'application/json'}

    def __init__(self, client_id: str, client_secret: str, base_url: str = 'https://api.breezeway.io', company_id: int | None = None):
        self.base_url = base_url.rstrip('/')
        client_id = client_id or getenv('BREEZEWAY_CLIENT_ID')
        client_secret = client_secret or getenv('BREEZEWAY_CLIENT_SECRET')
        if not client_id or not client_secret:
            raise AuthenticationError('client_id and client_secret are required as parameters or environment variables'
                             'BREEZEWAY_CLIENT_ID and BREEZEWAY_CLIENT_SECRET')
        self._company_id: int | None = int(company_id) if company_id else company_id
        self.auth: JWTAuth = JWTAuth(self.base_url, client_id, client_secret)
        self._company_resource = CompanyResource(base_url)
        self._unit_resource = UnitResource(base_url)
        self._user_resource = UserResource(base_url)

    @abstractmethod
    def _process_request(self, request: httpx.Request) -> Any:
        pass

    @staticmethod
    def _handle_response_error(resp: httpx.Response) -> NoReturn:
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

    def _process_response(self, resp: httpx.Response) -> Any:
        data = resp.json()
        if isinstance(data, dict) and 'error' in data:
            self._handle_response_error(resp)
        return data

    @property
    def authenticated(self) -> bool:
        return self.auth.authenticated


class BreezewayClient(BaseBreezewayClient):
    def __init__(self, client_id=None, client_secret=None, base_url=None, company_id: int | None = None):
        super().__init__(client_id, client_secret, base_url, company_id)
        self.client = httpx.Client(auth=self.auth, base_url=self.base_url, headers=self.HEADERS)

    def _process_request(self, request: httpx.Request) -> Any:
        response = self.client.send(request)
        return self._process_response(response)

    def companies(self) -> list[Company]:
        """
        Get a list of all companies associated with the client.
        """
        request = self._company_resource.list_companies()
        data = self._process_request(request)
        return [Company.model_validate(company).attach_client(self) for company in data]

    def create_unit(self, **kwargs: Unpack[UnitCreateDict]) -> Unit:
        """
        Create a new unit.
        Company ID is required for clients with multi-company access.
        """
        request = self._unit_resource.create_unit(**kwargs)
        data = self._process_request(request)
        return Unit.model_validate(data).attach_client(self)

    def list_reservations(self, **kwargs: Unpack[ReservationListDict]) -> Paginated[Reservation]:
        """
        Get a paginated list of reservations.
        Company ID is required for clients with multi-company access.
        """
        request = ReservationResource.list_reservations(**kwargs)
        data = self._process_request(request)
        return Paginated[Reservation].model_validate(data).attach_client(self)

    def list_subdepartments(self, company_id: int | None = None, reference_company_id: str | None = None) -> list[Subdepartment]:
        """
        Get a list of all subdepartments associated with the company.
        Company ID is required for clients with multi-company access.
        """
        request = self._company_resource.list_subdepartments(company_id=company_id, reference_company_id=reference_company_id)
        data = self._process_request(request)
        return [Subdepartment.model_validate(subdepartment) for subdepartment in data]

    def list_templates(self, company_id: int | None = None) -> list[Template]:
        """
        Get a list of all active task templates associated with the company.
        Company ID is required for clients with multi-company access.
        """
        request = self._company_resource.list_templates(company_id=company_id)
        data = self._process_request(request)
        return [Template.model_validate(template) for template in data]

    def list_units(self, **kwargs: Unpack[UnitListDict]) -> Paginated[Unit]:
        """
        Get a paginated list of units.
        Company ID is required for clients with multi-company access.
        """
        request = self._unit_resource.list_units(**kwargs)
        data = self._process_request(request)
        return Paginated[Unit].model_validate(data).attach_client(self)

    def list_unit_tags(self, company_id: int | None = None) -> list[UnitTag]:
        """
        List unit tags configured for a Breezeway company
        Creation of company tags must be performed within the app.
        Company ID is required for clients with multi-company access.
        """
        request = self._unit_resource.list_unit_tags(company_id=company_id)
        data = self._process_request(request)
        return [UnitTag.model_validate(tag) for tag in data]

    def list_users(self, status: UserStatus = UserStatus.ACTIVE) -> list[User]:
        """
        Get a list of users associated with the client.
        """
        request = self._user_resource.list_users(status=status)
        data = self._process_request(request)
        return [User.model_validate(user).attach_client(self) for user in data]

    def retrieve_unit(self, unit_id: int) -> Unit:
        """
        Retrieve a unit by its Breezeway ID.
        """
        request = self._unit_resource.retrieve_unit(unit_id=unit_id)
        data = self._process_request(request)
        return Unit.model_validate(data).attach_client(self)

    def retrieve_user(self, user_id: int) -> User:
        """
        Retrieve a user by their ID.
        """
        request = self._user_resource.retrieve_user(user_id=user_id)
        data = self._process_request(request)
        return User.model_validate(data).attach_client(self)

    def set_default_photo_for_unit(self, unit: Unit, photo: UnitPhoto) -> UnitPhoto:
        """
        Set a default photo for a unit.
        """
        request = self._unit_resource.update_default_photo(unit_id=unit.id, photo_id=photo.id)
        data = self._process_request(request)
        return UnitPhoto.model_validate(data)

    def units(self, **kwargs: Unpack[UnitListAllDict]) -> list[Unit]:
        """
        Get a list of all units.
        Company ID is required for clients with multi-company access.
        """
        paginated_units = self.list_units(**kwargs)
        units = paginated_units.results
        for page in range(2, paginated_units.total_pages + 1):
            units += self.list_units(page=page, **kwargs).results
        return units


class AsyncBreezewayClient(BaseBreezewayClient):
    def __init__(self, client_id=None, client_secret=None, base_url=None, company_id: int | None = None):
        super().__init__(client_id, client_secret, base_url, company_id)
        self.client = httpx.AsyncClient(auth=self.auth, base_url=self.base_url, headers=self.HEADERS)

    async def _process_request(self, request: httpx.Request) -> Any:
        response = await self.client.send(request)
        return self._process_response(response)

    async def companies(self) -> list[Company]:
        """
        Get a list of all companies associated with the client.
        """
        request = self._company_resource.list_companies()
        data = await self._process_request(request)
        return [Company.model_validate(company).attach_client(self) for company in data]

    async def create_unit(self, **kwargs: Unpack[UnitCreateDict]) -> Unit:
        """
        Create a new unit.
        Company ID is required for clients with multi-company access.
        """
        request = self._unit_resource.create_unit(**kwargs)
        data = await self._process_request(request)
        return Unit.model_validate(data).attach_client(self)

    async def list_reservations(self, **kwargs: Unpack[ReservationListDict]) -> Paginated[Reservation]:
        """
        Get a paginated list of reservations.
        Company ID is required for clients with multi-company access.
        """
        request = ReservationResource.list_reservations(**kwargs)
        data = await self._process_request(request)
        return Paginated[Reservation].model_validate(data).attach_client(self)

    async def list_subdepartments(self, company_id: int | None = None, reference_company_id: str | None = None) -> list[Subdepartment]:
        """
        Get a list of all subdepartments associated with the company.
        Company ID is required for clients with multi-company access.
        """
        request = self._company_resource.list_subdepartments(company_id=company_id, reference_company_id=reference_company_id)
        data = await self._process_request(request)
        return [Subdepartment.model_validate(subdepartment) for subdepartment in data]

    async def list_templates(self, company_id: int | None = None) -> list[Template]:
        """
        Get a list of all active task templates associated with the company.
        Company ID is required for clients with multi-company access.
        """
        request = self._company_resource.list_templates(company_id=company_id)
        data = await self._process_request(request)
        return [Template.model_validate(template) for template in data]

    async def list_units(self, **kwargs: Unpack[UnitListDict]) -> Paginated[Unit]:
        """
        Get a paginated list of units.
        Company ID is required for clients with multi-company access.
        """
        request = self._unit_resource.list_units(**kwargs)
        data = await self._process_request(request)
        return Paginated[Unit].model_validate(data).attach_client(self)

    async def list_unit_tags(self, company_id: int | None = None) -> list[UnitTag]:
        """
        List unit tags configured for a Breezeway company
        Creation of company tags must be performed within the app.
        Company ID is required for clients with multi-company access.
        """
        request = self._unit_resource.list_unit_tags(company_id=company_id)
        data = await self._process_request(request)
        return [UnitTag.model_validate(tag) for tag in data]

    async def list_users(self, status: UserStatus = UserStatus.ACTIVE) -> list[User]:
        """
        Get a list of users associated with the client.
        """
        request = self._user_resource.list_users(status=status)
        data = await self._process_request(request)
        return [User.model_validate(user).attach_client(self) for user in data]

    async def retrieve_unit(self, unit_id: int) -> Unit:
        """
        Retrieve a unit by its Breezeway ID.
        """
        request = self._unit_resource.retrieve_unit(unit_id=unit_id)
        data = await self._process_request(request)
        return Unit.model_validate(data).attach_client(self)

    async def retrieve_user(self, user_id: int) -> User:
        """
        Retrieve a user by their ID.
        """
        request = self._user_resource.retrieve_user(user_id=user_id)
        data = await self._process_request(request)
        return User.model_validate(data).attach_client(self)

    async def set_default_photo_for_unit(self, unit: Unit, photo: UnitPhoto) -> UnitPhoto:
        """
        Set a default photo for a unit.
        """
        request = self._unit_resource.update_default_photo(unit_id=unit.id, photo_id=photo.id)
        data = await self._process_request(request)
        return UnitPhoto.model_validate(data)

    async def units(self, **kwargs: Unpack[UnitListAllDict]) -> list[Unit]:
        """
        Get a list of all units.
        Company ID is required for clients with multi-company access.
        """
        paginated_units = await self.list_units(**kwargs)
        units = paginated_units.results
        if paginated_units.total_pages == 1:
            return units
        tasks = [self.list_units(page=page, **kwargs) for page in range(2, paginated_units.total_pages + 1)]
        remaining_pages = await asyncio.gather(*tasks)
        for page in remaining_pages:
            units += page.results
        return units