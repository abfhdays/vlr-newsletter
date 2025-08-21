from sqlalchemy import Integer, String, DateTime, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Article(Base):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str] = mapped_column(String(128), index=True)
    url: Mapped[str] = mapped_column(String(1024))
    title: Mapped[str] = mapped_column(String(512))
    published_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    author: Mapped[str | None] = mapped_column(String(128))
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    body_text: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Match(Base):
    __tablename__ = "matches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event: Mapped[str | None] = mapped_column(String(256))
    stage: Mapped[str | None] = mapped_column(String(128))
    date_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    team_a: Mapped[str] = mapped_column(String(128), index=True)
    team_b: Mapped[str] = mapped_column(String(128), index=True)
    score_a: Mapped[int | None] = mapped_column(Integer)
    score_b: Mapped[int | None] = mapped_column(Integer)
    bo: Mapped[int | None] = mapped_column(Integer)
    url: Mapped[str | None] = mapped_column(String(1024))
