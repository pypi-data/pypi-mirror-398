from pydantic import BaseModel


class TokenOutput(BaseModel):
    access_token: str
    token_type: str | None = "bearer"


class User(BaseModel):
    id: str
    username: str
    permissions: dict[str, list[str]]


class AgentMatch(BaseModel):
    agent_id: str
    agent_name: str
    agent_description: str | None = None
    user: User


class MeOutput(BaseModel):
    success : bool
    agents: list[AgentMatch]
    auto_selected: bool
