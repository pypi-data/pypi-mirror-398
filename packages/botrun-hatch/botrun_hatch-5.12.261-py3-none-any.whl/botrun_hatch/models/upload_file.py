from datetime import datetime, timedelta
from pydantic import BaseModel, Field


class UploadFile(BaseModel):
    id: str = Field(..., description="File ID")
    name: str = Field(..., description="File name")
    updated_at: str = Field(..., description="Last update time in ISO format")
    size: int = Field(..., description="File size in bytes")

    @property
    def formatted_size(self) -> str:
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        return f"{self.size / (1024 * 1024 * 1024):.1f} GB"

    @property
    def formatted_date(self) -> str:
        date = datetime.fromisoformat(self.updated_at)
        return date.strftime("%Y-%m-%d")
