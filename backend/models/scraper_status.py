from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from backend.database import Base


class ScraperStatus(Base):
    __tablename__ = "scraper_status"

    id              = Column(Integer, primary_key=True)
    platform        = Column(String(20), unique=True, nullable=False)
    status          = Column(String(20), default="ok")
    last_success    = Column(TIMESTAMP(timezone=True))
    last_failure    = Column(TIMESTAMP(timezone=True))
    failure_count   = Column(Integer, default=0)
    error_log       = Column(Text)
    screenshot_path = Column(Text)
