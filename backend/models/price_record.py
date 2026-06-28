from sqlalchemy import Column, Integer, String, BigInteger, Numeric, Date, Text, TIMESTAMP
from sqlalchemy.sql import func
from backend.database import Base


class PriceRecord(Base):
    __tablename__ = "price_records"

    id               = Column(Integer, primary_key=True)
    address          = Column(Text)
    district         = Column(String(20))
    price            = Column(BigInteger)
    unit_price       = Column(Integer)
    area_ping        = Column(Numeric(8, 2))
    building_type    = Column(String(20))
    transaction_date = Column(Date, nullable=False)
    lat              = Column(Numeric(10, 7))
    lng              = Column(Numeric(10, 7))
    imported_at      = Column(TIMESTAMP(timezone=True), server_default=func.now())
