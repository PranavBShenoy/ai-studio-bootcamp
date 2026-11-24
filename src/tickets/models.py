from datetime import date
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class TicketStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Ticket(BaseModel):
    ticket_id: int
    customer_name: str = Field(min_length=1)
    issue_summary: str = Field(min_length=3)
    priority: Priority
    status: TicketStatus
    created_date: date

    @field_validator("customer_name", "issue_summary", mode="before")
    @classmethod
    def strip_strings(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("created_date")
    @classmethod
    def reject_future_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("created_date cannot be in the future")
        return value
