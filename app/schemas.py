from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    # role is intentionally excluded from creation schema to prevent privilege escalation

class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class AnalyticsSummary(BaseModel):
    total_requests: int
    avg_latency_ms: float
    error_count: int
