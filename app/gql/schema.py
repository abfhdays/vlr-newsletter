import strawberry
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from strawberry.types import Info
from sqlalchemy.orm import Session
from app.db import get_db, SessionLocal
from app.data_models import Article, Match
from app.datasource.api_client import APIClient

@strawberry.type
class ArticleGQL:
    id: int
    url: str
    title: str
    published_at: Optional[datetime]
    tags: Optional[List[str]]

@strawberry.type
class MatchGQL:
    id: int
    event: Optional[str]
    stage: Optional[str]
    date_time: Optional[datetime]
    team_a: str
    team_b: str
    score_a: Optional[int]
    score_b: Optional[int]
    bo: Optional[int]
    url: Optional[str]

def _session(info: Info) -> Session:
    return SessionLocal()

@strawberry.type
class Query:
    @strawberry.field
    def last_week_articles(self, info: Info) -> List[ArticleGQL]:
        db = _session(info)
        from sqlalchemy import select, desc
        now = datetime.now(timezone.utc); since = now - timedelta(days=7)
        rows = db.execute(
            select(Article).where(Article.published_at >= since).order_by(desc(Article.published_at))
        ).scalars().all()
        return [ArticleGQL(**{
            "id": r.id, "url": r.url, "title": r.title,
            "published_at": r.published_at, "tags": r.tags
        }) for r in rows]

    @strawberry.field
    def last_week_matches(self, info: Info) -> List[MatchGQL]:
        db = _session(info)
        from sqlalchemy import select, desc
        now = datetime.now(timezone.utc); since = now - timedelta(days=7)
        rows = db.execute(
            select(Match).where(Match.date_time >= since).order_by(desc(Match.date_time))
        ).scalars().all()
        return [MatchGQL(**{
            "id": r.id, "event": r.event, "stage": r.stage, "date_time": r.date_time,
            "team_a": r.team_a, "team_b": r.team_b, "score_a": r.score_a, "score_b": r.score_b,
            "bo": r.bo, "url": r.url
        }) for r in rows]

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def fetch_last_week(self) -> bool:
        api = APIClient()
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=7)
        arts = await api.fetch_articles(since)
        mats = await api.fetch_matches(since)
        with SessionLocal() as db:
            for a in arts:
                exists = db.query(Article).filter_by(source_id=a.source_id).first()
                if not exists:
                    db.add(Article(
                        source_id=a.source_id, url=str(a.url), title=a.title,
                        published_at=a.published_at, author=a.author, tags=a.tags,
                        body_text=a.body_text
                    ))
            for m in mats:
                exists = db.query(Match).filter_by(url=m.url).first() if m.url else None
                if not exists:
                    db.add(Match(
                        event=m.event, stage=m.stage, date_time=m.date_time,
                        team_a=m.team_a, team_b=m.team_b, score_a=m.score_a,
                        score_b=m.score_b, bo=m.bo, url=m.url
                    ))
            db.commit()
        return True

schema = strawberry.Schema(query=Query, mutation=Mutation)
