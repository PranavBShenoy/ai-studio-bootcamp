from typing import Literal, Optional
from pydantic import BaseModel, Field


class TicketTriage(BaseModel):
    equipment: str = Field(..., min_length=2, description="Normalized medical/IT device name")
    urgency: Literal["low", "medium", "high", "critical"]
    hospital: Optional[str] = Field(
        default=None, description="Hospital/clinic name if mentioned, otherwise null"
    )
    next_action: Literal[
        "remote_troubleshoot",
        "dispatch_field_engineer",
        "escalate_vendor_rma",
        "schedule_preventive_maintenance",
    ]
