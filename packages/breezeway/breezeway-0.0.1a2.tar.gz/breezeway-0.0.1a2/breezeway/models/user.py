from enum import Enum

from pydantic import Field

from .base import BaseBreezewayModel
from .company import Department
from .unit import UnitGroup


class UserRole(Enum):
    ADMIN = 'administrator'
    OFFICE = 'office'
    REPRESENTATIVE = 'representative'
    SERVICE_PARTNER = 'service_partner'
    SUPERVISOR = 'supervisor'

    @property
    def name(self) -> str:
        return {
            UserRole.ADMIN: "Administrator",
            UserRole.OFFICE: "Office",
            UserRole.REPRESENTATIVE: "Representative",
            UserRole.SERVICE_PARTNER: "Service Partner",
            UserRole.SUPERVISOR: "Supervisor",
        }[self]


class UserStatus(Enum):
    ACTIVE = 'active'
    INVITED = 'invited'
    INACTIVE = 'inactive'

    @property
    def name(self) -> str:
        return {
            UserStatus.ACTIVE: "Active",
            UserStatus.INVITED: "Invited",
            UserStatus.INACTIVE: "Inactive",
        }[self]


class User(BaseBreezewayModel):
    id: int
    first_name: str
    last_name: str
    accept_decline_tasks: bool
    active: bool
    emails: list[str]
    code: str | None = Field(alias='employee_code')
    groups: list[UnitGroup]
    shifts: dict
    departments: list[Department] = Field(alias='type_departments')
    role: UserRole = Field(alias='type_role')

    @property
    def name(self):
        return self.first_name + ' ' + self.last_name

    @property
    def email(self):
        return self.emails[0] if self.emails else None


class InvitedUser(User):
    def invite(self):
        """Send an invitation email to the user."""
        endpoint = f'public/inventory/v1/people/{self.id}/invite'
        self._request('POST', endpoint)
