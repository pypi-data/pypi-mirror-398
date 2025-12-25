from datetime import date
from typing import TypedDict, Literal, Unpack

from httpx import Request

from .base import BaseResource

class ReservationListDict(TypedDict):
    property_id: int | None
    checkin_date_lt: date | None
    checkin_date_le: date | None
    checkin_date_gt: date | None
    checkin_date_ge: date | None
    checkout_date_lt: date | None
    checkout_date_le: date | None
    checkout_date_gt: date | None
    checkout_date_ge: date | None
    created_at_lt: date | None
    created_at_le: date | None
    created_at_gt: date | None
    created_at_ge: date | None
    updated_at_lt: date | None
    updated_at_le: date | None
    updated_at_gt: date | None
    updated_at_ge: date | None
    limit: int | None
    page: int | None
    sort_by: str | None
    sort_order: Literal['desc', 'asc'] | None
    company_id: int | None  # required if using cross-company access

class ReservationResource(BaseResource):
    def list_reservations(self, **kwargs: Unpack[ReservationListDict]) -> Request:
        """Get a paginated list of reservations."""
        endpoint = 'public/reservation/v1/reservation'
        params = kwargs
        return self._build_request('GET', endpoint, params=params)