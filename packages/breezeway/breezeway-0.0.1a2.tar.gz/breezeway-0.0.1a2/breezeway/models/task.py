from datetime import datetime, timedelta, time, date
from decimal import Decimal
from enum import StrEnum
from typing import Dict

from pydantic import field_serializer, Field, ConfigDict

from .base import BaseBreezewayModel
from .company import Department, Subdepartment


class AssignmentStatus(StrEnum):
    PENDING = 'pending'
    ASSIGNED = 'assigned'
    ACCEPTED = 'accepted'

    @property
    def name(self) -> str:
        return {
            AssignmentStatus.PENDING: "Pending",
            AssignmentStatus.ASSIGNED: "Assigned",
            AssignmentStatus.ACCEPTED: "Accepted"
        }[self]


class MarkupType(StrEnum):
    FLAT_RATE = 'flat_rate'
    PERCENT = 'percent'


class Payor(StrEnum):
    DAMAGE = 'damage'
    GUEST = 'guest'
    INTERNAL = 'internal'
    OWNER = 'owner'
    INSURANCE = 'insurance'
    REVIEW = 'review'

    @property
    def name(self) -> str:
        return {
            Payor.DAMAGE: "Damage",
            Payor.GUEST: "Guest",
            Payor.INTERNAL: "No Charge/Internal",
            Payor.OWNER: "Owner",
            Payor.INSURANCE: "Insurance",
            Payor.REVIEW: "Review",

        }[self]


class Priority(StrEnum):
    URGENT = 'urgent'
    HIGH = 'high'
    NORMAL = 'normal'
    LOW = 'low'
    WATCH = 'watch'


class RateType(StrEnum):
    HOUR = 'hour'
    PIECE = 'piece'

    @property
    def name(self) -> str:
        return {
            RateType.HOUR: 'hourly',
            RateType.PIECE: 'piece'
        }[self]


class Requester(StrEnum):
    OWNER = 'owner'
    GUEST = 'guest'
    GUEST_SURVEY = 'guest_survey'
    INSPECTOR = 'inspector'
    HOUSEKEEPER = 'housekeeper'
    MAINTENANCE_TECH = 'maintenance_tech'
    PROPERTY_SERVICES = 'property_services'
    PROPERTY_MANAGER = 'property_manager'
    DISPATCHER = 'dispatcher'

    @property
    def name(self) -> str:
        return {
            Requester.OWNER: "Owner",
            Requester.GUEST: "Guest",
            Requester.GUEST_SURVEY: "Guest Survey",
            Requester.INSPECTOR: "Inspector",
            Requester.HOUSEKEEPER: "Housekeeper",
            Requester.MAINTENANCE_TECH: "Maintenance Tech",
            Requester.PROPERTY_SERVICES: "Property Services",
            Requester.PROPERTY_MANAGER: "Property Manager",
            Requester.DISPATCHER: "Dispatcher"
        }[self]


class TaskRequirementType(StrEnum):
    CONDITION = 'condition'
    CHECKLIST = 'checklist'
    PHOTO = 'photo'
    COUNT = 'count'
    TEXT = 'text'
    YES_NO = 'yes / no'
    RATING = 'rating'

    @property
    def name(self) -> str:
        return {
            TaskRequirementType.CONDITION: "Condition",
            TaskRequirementType.CHECKLIST: "Checklist",
            TaskRequirementType.PHOTO: "Photo",
            TaskRequirementType.COUNT: "Count",
            TaskRequirementType.TEXT: "Text",
            TaskRequirementType.YES_NO: "Yes/No",
            TaskRequirementType.RATING: "Rating"
        }[self]


class TaskStatus(StrEnum):
    DRAFTED = 'drafted'
    CREATED = 'created'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'
    CLOSED = 'closed'
    APPROVED = 'approved'
    DELETED = 'deleted'

    @property
    def name(self) -> str:
        return {
            TaskStatus.DRAFTED: "Drafted",
            TaskStatus.CREATED: "Created",
            TaskStatus.IN_PROGRESS: "In Progress",
            TaskStatus.FINISHED: "Finished",
            TaskStatus.CLOSED: "Closed",
            TaskStatus.APPROVED: "Approved",
            TaskStatus.DELETED: "Deleted"
        }[self]


class TypeCost(StrEnum):
    LABOR = 'labor'
    MATERIAL = 'material'
    EXPENSE = 'expense'
    TAX = 'tax'
    SKILLED_LABOR = 'skilled_labor'
    NON_SKILLED_LABOR = 'non_skilled_labor'
    MILAGE = 'mileage'
    MARK_UP = 'mark_up'

    @property
    def name(self) -> str:
        return {
            TypeCost.LABOR: 'Labor',
            TypeCost.MATERIAL: 'Materials',
            TypeCost.EXPENSE: 'Expense',
            TypeCost.TAX: 'Tax',
            TypeCost.SKILLED_LABOR: 'Skilled Labor',
            TypeCost.NON_SKILLED_LABOR: 'Non-skilled Labor',
            TypeCost.MILAGE: 'Mileage',
            TypeCost.MARK_UP: 'Mark-up'
        }[self]

    @property
    def _id(self):
        return {
            TypeCost.LABOR: 1,
            TypeCost.MATERIAL: 2,
            TypeCost.EXPENSE: 3,
            TypeCost.TAX: 4,
            TypeCost.SKILLED_LABOR: 5,
            TypeCost.NON_SKILLED_LABOR: 6,
            TypeCost.MILAGE: 7,
            TypeCost.MARK_UP: 8
        }

    def serialize(self) -> dict:
        return {
            'code': self.value,
            'id': self._id,
            'name': self.name
        }


class Assignment(BaseBreezewayModel):
    id: int
    name: str
    user_id: int = Field(validation_alias='assignee_id', serialization_alias='assignee_id')
    employee_code: str | None
    expires_at: datetime | None
    status: AssignmentStatus = Field(validation_alias='type_task_user_status', serialization_alias='type_task_user_status')


class Comment(BaseBreezewayModel):
    id: int
    content: str = Field(validation_alias='comment', serialization_alias='comment')
    created_at: datetime


class Cost(BaseBreezewayModel):
    id: int
    amount: Decimal = Field(validation_alias='cost', serialization_alias='cost')
    created_at: datetime
    description: str
    category: TypeCost = Field(validation_alias='type_cost', serialization_alias='type_cost')
    updated_at: datetime | None


class TaskPhoto(BaseBreezewayModel):
    id: int
    url: str


class TaskRequirement(BaseBreezewayModel):
    # Some of these fields can be None with edge cases
    action: str | list[str]  # Always a list for checklists, even when there is only one line
    element_name: str | None  = Field(validation_alias='home_element_name', serialization_alias='home_element_name')  # Only populates when requirement is under a first level element
    note: str | None
    photo_required: bool  # is False for photo requirements
    photos: list[str]  # List of urls
    response: str | None  # condition('good', 'dirty', 'damaged', 'not_working') yes/no('yes', 'no') checklist('check', None), rating('1', '2', '3', '4', '5')
    section_name: str | None
    type: TaskRequirementType = Field(validation_alias='type_requirement', serialization_alias='type_requirement')


class TaskSupply(BaseBreezewayModel):
    id: int
    name: str
    billable: bool
    description: str
    markup_pricing_type: MarkupType
    markup_rate: Decimal
    quantity: int
    size: str
    supply_id: int
    total_price: Decimal
    unit_cost: Decimal  # pre-markup cost


class TaskTag(BaseBreezewayModel):
    id: int
    name: str


class Task(BaseBreezewayModel):
    model_config = super().model_config.copy()
    model_config.update(frozen=False)
    id: int = Field(frozen=True)
    name: str  # Title
    assignments: list[Assignment]
    bill_to: Payor | None
    costs: list[Cost]
    created_at: datetime
    created_by: Dict['id': int, 'name': str] | None  # id is a user id. None when created with API
    department: Department = Field(validation_alias='type_department', serialization_alias='type_department')
    description: str | None
    finished_at: datetime | None
    finished_by: dict  # TODO use a model from people?
    home_id: int
    paused: bool
    photos: list[TaskPhoto]
    priority: Priority = Field(validation_alias='type_priority', serialization_alias='type_priority')
    rate_paid: str  # example: '0.05 USD'
    rate_type: RateType
    reference_property_id: str | None
    report_url: str
    requested_by: Requester | None
    scheduled_date: date | None
    scheduled_time: time | None
    started_at: datetime | None
    status: TaskStatus = Field(validation_alias='type_task_status', serialization_alias='type_task_status')
    subdepartments: list[Subdepartment]
    supplies: list[TaskSupply]
    task_tags: list[TaskTag] # TODO: tags and task_tags are essentially the same thing
    template_id: int | None
    total_time: timedelta | None
    updated_at: datetime
