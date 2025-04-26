from pydantic import BaseModel
from typing import Optional

class DependabotAlertModel(BaseModel):
    number: int
    state: str
    dependency: Optional[str]
    severity: Optional[str]
    security_advisory_summary: Optional[str]
    security_advisory_description: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    dismissed_at: Optional[str]
    dismissed_by: Optional[str]
    dismissed_reason: Optional[str]
    html_url: Optional[str]
