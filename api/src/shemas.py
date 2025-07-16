from pydantic import BaseModel


class Report(BaseModel):
    id: int
    title: str
    content: str
    created_at: str
