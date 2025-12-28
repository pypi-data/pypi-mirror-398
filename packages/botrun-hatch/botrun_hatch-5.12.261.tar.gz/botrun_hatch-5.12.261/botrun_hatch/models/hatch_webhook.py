from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class HatchWebhook(BaseModel):
    """
    Hatch Webhook 資訊模型，用於追蹤 Google Drive webhook 註冊。

    Args:
        hatch_id (str): 關聯的 Hatch ID
        channel_id (str): Google Drive 通知頻道 ID
        resource_id (str): Google Drive 資源 ID
        created_at (datetime, optional): 建立時間
    """

    hatch_id: str
    channel_id: str
    resource_id: str
    created_at: Optional[datetime] = None
