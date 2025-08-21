import strawberry
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, desc
from app.db import SessionLocal
from app.data_models import Article, Match
from app.scraper import Scraper

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

@strawberry.type
class Query:
    @strawberry.field
    def last_week_articles(self) -> List[ArticleGQL]:
        now = datetime.now(timezone.utc); since = now - timedelta(days=7)
        with SessionLocal() as db:
            rows = db.execute(
                select(Article).where(Article.published_at >= since).order_by(desc(Article.published_at))
            ).scalars().all()
        return [ArticleGQL(id=r.id, url=r.url, title=r.title, published_at=r.published_at, tags=r.tags) for r in rows]

    @strawberry.field
    def last_week_matches(self) -> List[MatchGQL]:
        now = datetime.now(timezone.utc); since = now - timedelta(days=7)
        with SessionLocal() as db:
            rows = db.execute(
                select(Match).where(Match.date_time >= since).order_by(desc(Match.date_time))
            ).scalars().all()
        return [
            MatchGQL(
                id=r.id, event=r.event, stage=r.stage, date_time=r.date_time,
                team_a=r.team_a, team_b=r.team_b, score_a=r.score_a, score_b=r.score_b,
                bo=r.bo, url=r.url
            )
            for r in rows
        ]

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def fetch_last_week(self) -> bool:
        now = datetime.now(timezone.utc); since = now - timedelta(days=7)
        try:
            scraper = Scraper()
            arts = await scraper.fetch_articles(since)
            mats = await scraper.fetch_matches(since)
            print(f"[scraper] fetched {len(arts)} articles, {len(mats)} matches")

            with SessionLocal() as db:
                # insert articles if new (by source_id)
                for a in arts:
                    if not db.query(Article).filter_by(source_id=a.source_id).first():
                        db.add(Article(
                            source_id=a.source_id, url=str(a.url), title=a.title,
                            published_at=a.published_at, author=a.author,
                            tags=a.tags, body_text=a.body_text
                        ))

                # insert matches if new (by url)
                for m in mats:
                    exists = db.query(Match).filter_by(url=m.url).first() if m.url else None
                    if not exists:
                        db.add(Match(
                            event=m.event, stage=m.stage, date_time=m.date_time,
                            team_a=m.team_a, team_b=m.team_b,
                            score_a=m.score_a, score_b=m.score_b, bo=m.bo,
                            url=m.url
                        ))
                db.commit()

            return True
        except Exception as e:
            print("[scraper] error:", repr(e))
            return False

schema = strawberry.Schema(query=Query, mutation=Mutation)
