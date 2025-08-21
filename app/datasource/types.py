from pydantic import BaseModel, HttpUrl
from datetime import datetime

class ArticleDTO(BaseModel):
    source_id: str
    url: HttpUrl
    title: str
    published_at: datetime | None = None
    author: str | None = None
    tags: list[str] | None = None
    body_text: str | None = None

class MatchDTO(BaseModel):
    event: str | None = None
    stage: str | None = None
    date_time: datetime | None = None
    team_a: str
    team_b: str
    score_a: int | None = None
    score_b: int | None = None
    bo: int | None = None
    url: str | None = None
