from pydantic import BaseModel

class Settings(BaseModel):
    timezone: str = "America/Toronto"
    # add API keys later if you need

settings = Settings()