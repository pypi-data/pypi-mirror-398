from enum import StrEnum

from pydantic import Field

from breezeway.models.base import BaseBreezewayModel


class Department(StrEnum):
    HOUSEKEEPING = 'housekeeping'
    INSPECTION = 'inspection'
    MAINTENANCE = 'maintenance'

    @property
    def name(self) -> str:
        return {
            Department.HOUSEKEEPING: "Cleaning",
            Department.INSPECTION: "Inspection",
            Department.MAINTENANCE: "Maintenance",
        }[self]


class Company(BaseBreezewayModel):
    id: int
    name: str
    reference_company_id: str | None = None


class Subdepartment(BaseBreezewayModel):
    id: int
    name: str


class Template(BaseBreezewayModel):
    id: int
    name: str = Field(validation_alias='template_name', serialization_alias='template_name')
    department: Department = Field(validation_alias='department_code', serialization_alias='department_code')
