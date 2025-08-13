from sqlalchemy import create_engine, DeclarativeBase
from sqlalcemy.orm import declarative_base, sessionmaker

engine = create_engine("sqlite:///./vlr.db", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()