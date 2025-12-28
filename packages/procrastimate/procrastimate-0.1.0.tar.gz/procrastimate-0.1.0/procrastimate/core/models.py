from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaskInput(BaseModel):
    task: str
    deadline: Optional[datetime] = None
    audience: str = "manager"
    severity: str = "medium"


class ProcrastinationResult(BaseModel):
    original_task: str
    rescheduled_to: datetime
    excuse: str
    affirmation: str


