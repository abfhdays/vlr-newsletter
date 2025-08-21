from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.data_models import Article, Match

def last_week(db: Session):
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=7)
    arts = db.execute(
        select(Article).where(Article.published_at >= since).order_by(desc(Article.published_at))
    ).scalars().all()
    mats = db.execute(
        select(Match).where(Match.date_time >= since).order_by(desc(Match.date_time))
    ).scalars().all()
    return arts, mats
