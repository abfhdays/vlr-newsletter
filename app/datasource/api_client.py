from datetime import datetime, timedelta, timezone
from .types import ArticleDTO, MatchDTO

class APIClient:
    async def fetch_articles(self, since: datetime) -> list[ArticleDTO]:
        now = datetime.now(timezone.utc)
        return [ArticleDTO(
            source_id="mock-1",
            url="https://vlr.gg/news/mock",
            title="Mock: Epic upset",
            published_at=now - timedelta(days=1),
            tags=["upset","playoffs"],
            body_text="Story..."
        )]

    async def fetch_matches(self, since: datetime) -> list[MatchDTO]:
        now = datetime.now(timezone.utc)
        return [MatchDTO(
            event="Mock Masters", stage="Playoffs",
            date_time=now - timedelta(days=2),
            team_a="Team Alpha", team_b="Team Beta",
            score_a=2, score_b=0, bo=3, url="https://vlr.gg/match/123"
        )]
