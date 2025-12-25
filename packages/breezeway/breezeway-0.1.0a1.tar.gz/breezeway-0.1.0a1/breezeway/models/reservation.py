from datetime import time, date
from enum import StrEnum

from pydantic import Field

from .base import BaseBreezewayModel


class GuestType(StrEnum):
    GUEST = 'guest'
    OWNER = 'owner'

    @property
    def name(self) -> str:
        return {
            GuestType.GUEST: 'Guest',
            GuestType.OWNER: 'Owner'
        }[self]


class ReservationType(StrEnum):
    BOOKING = 'booking'
    HOLD = 'hold'

    @property
    def name(self) -> str:
        return {
            ReservationType.BOOKING: 'Booking',
            ReservationType.HOLD: 'Hold'
        }[self]


class StayType(StrEnum):
    GUEST = 'guest'
    OWNER = 'owner'

    @property
    def name(self) -> str:
        return {
            StayType.GUEST: 'Guest',
            StayType.OWNER: 'Owner'
        }[self]


class Guest(BaseBreezewayModel):
    first_name: str
    last_name: str
    emails: list[str]
    phone_numbers: list[dict]

class Tag(BaseBreezewayModel):
    id: int
    name: str
    company_id: int | None = None


class Reservation(BaseBreezewayModel):
    id: int
    access_code: str
    checkin_date: date
    checkin_time: time
    checkin_early: bool | None
    checkout_date: date
    checkout_time: time
    checkout_late: bool | None
    flags: list
    guests: list[Guest]
    guide_url: str | None
    note: str | None
    property_id: int
    reference_property_id: str | None
    reference_reservation_id: str | None
    status: str
    tags: list[Tag]
    type_guest: GuestType | None = Field(validation_alias='type_guest:code')
    type_reservation: ReservationType = Field(validation_alias='type_reservation:code')
    type_stay: StayType | None = Field(validation_alias='type_stay:code')