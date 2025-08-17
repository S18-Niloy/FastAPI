from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any

TaskType = Literal["qa","latest","image","platform_content"]

class AiTaskRequest(BaseModel):
    task: TaskType
    prompt: Optional[str] = None
    platform: Optional[Literal["facebook","linkedin","twitter","x","instagram","tiktok","reddit","medium"]] = None
    extras: Optional[Dict[str, Any]] = None

class AiTaskResponse(BaseModel):
    ok: bool = True
    task: TaskType
    data: Dict[str, Any]

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    username: str = Field(..., examples=["demo"])
    password: str = Field(..., examples=["demo123"])
