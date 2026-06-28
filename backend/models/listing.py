from sqlalchemy import Column, Integer, String, BigInteger, Numeric, SmallInteger, Boolean, ARRAY, Text, TIMESTAMP
from sqlalchemy.sql import func
from backend.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id           = Column(Integer, primary_key=True)
    source       = Column(String(20), nullable=False)
    source_id    = Column(String(100), nullable=False)
    url          = Column(Text, nullable=False)
    title        = Column(Text)
    price        = Column(BigInteger)
    unit_price   = Column(Integer)
    area_ping    = Column(Numeric(8, 2))
    rooms        = Column(SmallInteger)
    floor        = Column(SmallInteger)
    total_floors = Column(SmallInteger)
    building_age = Column(SmallInteger)
    district     = Column(String(20))
    address      = Column(Text)
    lat          = Column(Numeric(10, 7))
    lng          = Column(Numeric(10, 7))
    photos       = Column(ARRAY(Text), default=[])
    is_active    = Column(Boolean, default=True)
    scraped_at   = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at   = Column(TIMESTAMP(timezone=True), server_default=func.now())
