from typing import List, Optional
from pydantic import BaseModel, Field

from botrun_hatch.models.upload_file import UploadFile


class Hatch(BaseModel):
    """
    Hatch 設定模型。

    Args:
        user_id (str):
        id (str):
        model_name (str, optional): 使用的模型名稱，預設為空字串。
        agent_model_name (str, optional): Agent 使用的模型名稱，預設為空字串。
        prompt_template (str, optional): 這個就是 system prompt，預設為空字串。
        google_doc_link (str, optional): 如果 google_doc_link 啟動，會將 google doc 的內容放在 prompt_template 裡面，預設為空字串。
        enable_google_doc_link (bool, optional): 是否啟用 Google Doc 搜尋，預設為 False。
        last_sync_gdoc_time (Optional[str], optional): 上一次同步 Google Doc 的 UTC 時間，預設為 None。
        last_sync_gdoc_success (bool, optional): 上一次同步 Google Doc 是否成功，預設為 False。
        user_prompt_prefix (str, optional): User prompt 前綴。
        name (str, optional):
        is_default (bool, optional):
        enable_search (bool, optional):
        related_question_prompt (str, optional):
        search_vendor (str, optional):
        search_domain_filter (List[str], optional):
        files (List[UploadFile], optional):
        enable_agent (bool, optional):
        enable_api (bool, optional):
        updated_at (str, optional): 最後更新時間 (UTC ISO format)，預設為空字串。
    """

    user_id: str
    id: str
    model_name: str = ""
    agent_model_name: str = ""
    prompt_template: str = ""
    google_doc_link: str = ""
    enable_google_doc_link: bool = False
    last_sync_gdoc_time: str = ""
    last_sync_gdoc_success: bool = False
    user_prompt_prefix: str = ""
    name: str = ""  # 将 name 设为可选字段，默认为空字符串
    is_default: bool = False
    enable_search: bool = False
    related_question_prompt: str = ""
    search_vendor: str = "perplexity"
    search_domain_filter: List[str] = []
    files: List[UploadFile] = []
    enable_agent: bool = False
    enable_api: bool = False
    mcp_config: str = """{
}"""
    updated_at: str = ""
