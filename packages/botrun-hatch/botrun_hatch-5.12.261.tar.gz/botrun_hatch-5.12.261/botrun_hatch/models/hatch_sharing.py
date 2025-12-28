from datetime import datetime
from pydantic import BaseModel, Field


class HatchSharing(BaseModel):
    hatch_id: str
    owner_id: str
    shared_with_id: str
    created_at: datetime = Field(default_factory=datetime.now)
