from enum import Enum

from pydantic import Field, ConfigDict

from breezeway.models.base import BaseBreezewayModel


class UnitStatus(Enum):
    ACTIVE = 'active'
    ACTIVE_WITH_CONFLICT = 'pending_delete'
    INACTIVE = 'inactive'
    DELETED = 'deleted'

    @property
    def name(self) -> str:
        return {
            UnitStatus.ACTIVE: "Active",
            UnitStatus.ACTIVE_WITH_CONFLICT: "Active with Conflict",
            UnitStatus.INACTIVE: "Inactive",
            UnitStatus.DELETED: "Deleted",
        }[self]


class UnitGroup(BaseBreezewayModel):
    id: int
    name: str
    parent_group_id: int | None


class UnitNotes(BaseBreezewayModel):
    general: str | None = None
    about: str | None = None
    access: str | None = None
    directions: str | None = Field(None, validation_alias='direction', serialization_alias='direction')
    external: str | None = None
    guest_access: str | None = None
    housekeeping: str | None = None
    trash: str | None = Field(None, validation_alias='trash_info', serialization_alias='trash_info')
    wifi: str | None = Field(None, validation_alias='wifi_info', serialization_alias='wifi_info')


class UnitPhoto(BaseBreezewayModel):
    model_config = ConfigDict(frozen=True)
    caption: str | None
    default: bool
    id: int
    original_url: str | None
    url: str


class UnitTag(BaseBreezewayModel):
    id: int
    name: str
    company_id: int | None = None


class BaseUnit(BaseBreezewayModel):
    model_config = BaseBreezewayModel.model_config.copy().update({'frozen': False})
    name: str
    address1: str | None = None
    address2: str | None = None
    building: str | None = None
    city: str | None = None
    company_id: int | None = Field(None, frozen=True, exclude=True)
    country: str | None = None
    external_property_id: str | None = Field(None, validation_alias='internal_code', serialization_alias='internal_code', frozen=True)
    guest_access_code: str | None = Field(None, frozen=True, exclude=True)
    internal_access_code: str | None = Field(None, validation_alias='access_code', frozen=True, exclude=True)
    latitude: float | None = None
    longitude: float | None = None
    notes: UnitNotes | None = None
    num_bathrooms: int | None = Field(None, validation_alias='bathrooms', serialization_alias='bathrooms')
    num_bedrooms: int | None = Field(None, validation_alias='bedrooms', serialization_alias='bedrooms')
    status: UnitStatus | None = None
    state: str | None = None
    wifi_name: str | None = None
    wifi_password: str | None = None
    zipcode: str | None = None


class UnregisteredUnit(BaseUnit):
    external_property_id: str = Field(validation_alias='internal_code', serialization_alias='internal_code')
    photos: list[str] | None = None


class Unit(BaseUnit):
    id: int | None = Field(frozen=True, exclude=True)
    display: str = Field(frozen=True, exclude=True)
    groups: tuple[UnitGroup, ...] = Field(frozen=True, exclude=True)
    photos: tuple[UnitPhoto, ...] = Field(frozen=True, exclude=True)
    reference_company_id: str | None = Field(frozen=True, exclude=True)
    reference_external_property_id: str | None = Field(frozen=True, exclude=True)
    reference_property_id: str | None = Field(frozen=True, exclude=True)
    status: UnitStatus

    @property
    def tags(self) -> list[UnitTag]:
        return self.add_tags([])  # TODO: Test this breezeway API workaround

    @tags.setter
    def tags(self, tags: list[UnitTag]) -> None:
        endpoint = f'public/inventory/v1/property/{self.id}/tags'
        payload = [tag.id for tag in tags]
        self._request('PATCH', endpoint, payload=payload)

    def add_tag(self, tag: UnitTag) -> list[UnitTag]:
        return self.add_tags([tag])

    def add_tags(self, tags: list[UnitTag]) -> list[UnitTag]:
        endpoint = f'public/inventory/v1/property/{self.id}/tags'
        payload = [tag.id for tag in tags]
        return [UnitTag.model_validate(tag) for tag in self._request('POST', endpoint, payload=payload)]

    def delete_tag(self, tag: UnitTag) -> list[UnitTag]:
        return self.delete_tags([tag])

    def delete_tags(self, tags: list[UnitTag]) -> list[UnitTag]:
        """Delete tags from a property."""
        endpoint = f'public/inventory/v1/property/{self.id}/tags'
        payload = [tag.id for tag in tags]
        return [UnitTag.model_validate(tag) for tag in self._request('DELETE', endpoint, payload=payload)]

    def save(self):
        endpoint = f'public/inventory/v1/property/{self.id}'
        updated_unit = Unit.model_validate(self._request('PATCH', endpoint, payload=self.model_dump()))
        for attr, value in updated_unit.__dict__.items():
            if hasattr(self, attr) and value is not None:
                setattr(self, attr, value)




class PaginatedUnits(BaseBreezewayModel):
    limit: int
    page: int
    results: list[Unit]
    total_pages: int
    total_results: int
