from datetime import datetime
from sqlalchemy import ForeignKey, BigInteger, Integer, Text, DateTime, func, MetaData
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

metadata = MetaData()

class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)

    price: Mapped[int] = mapped_column(BigInteger)
    enchant_level: Mapped[int | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(Text, default="adena")
    source: Mapped[str | None] = mapped_column(Text, nullable=True, default="auction_house")

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    item: Mapped["Item"] = relationship(
        back_populates="prices",
        lazy="joined"
    )
