from pydantic import BaseModel


class UserSetting(BaseModel):
    user_id: str
    default_model: str = ""
    audio_reply: bool = False
    search_vendor: str = "Botrun"
    search_enabled: bool = False
    api_key: str = ""
