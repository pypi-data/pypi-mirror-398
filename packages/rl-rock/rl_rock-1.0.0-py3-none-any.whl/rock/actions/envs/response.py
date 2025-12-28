from typing import Any

from pydantic import BaseModel, Field


class EnvMakeResponse(BaseModel):
    sandbox_id: str


class EnvResetResponse(BaseModel):
    observation: Any
    info: dict = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class EnvStepResponse(BaseModel):
    observation: Any
    reward: float
    terminated: bool
    truncated: bool
    info: dict = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class EnvCloseResponse(BaseModel):
    sandbox_id: str


class EnvListResponse(BaseModel):
    env_id: list[str]
