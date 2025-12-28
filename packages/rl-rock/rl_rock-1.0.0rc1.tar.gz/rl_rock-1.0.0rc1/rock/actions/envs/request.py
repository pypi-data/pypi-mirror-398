from pydantic import BaseModel


class EnvMakeRequest(BaseModel):
    env_id: str
    sandbox_id: str


class EnvResetRequest(BaseModel):
    sandbox_id: str
    seed: int | None = None


class EnvStepRequest(BaseModel):
    sandbox_id: str
    action: str


class EnvCloseRequest(BaseModel):
    sandbox_id: str
