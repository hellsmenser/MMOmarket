from sqlalchemy import String, ForeignKey, MetaData
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

metadata = MetaData()

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    modifications: Mapped[str | None] = mapped_column(String, nullable=True)
    image: Mapped[str] = mapped_column(String, default="PLACEHOLDER")
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    tolerance: Mapped[float | None] = mapped_column(default=0.1)

    prices: Mapped[list["PriceHistory"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    category: Mapped["Category"] = relationship(
        back_populates="items",
        lazy="joined"
    )

    _modifications: Mapped[str | None] = mapped_column("modifications", String, nullable=True)

    @hybrid_property
    def modifications(self) -> list[str] | None:
        if self._modifications:
            return self._modifications.split(",")
        return None

    @modifications.setter
    def modifications(self, value: list[str] | None):
        self._modifications = ",".join(value) if value else None
