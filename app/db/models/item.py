from sqlalchemy import String, ForeignKey, Index, Computed, text, Identity, BigInteger
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        Index("ix_items_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_items_name_trgm", text("name gin_trgm_ops"), postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    origin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True, unique=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)
    tolerance: Mapped[float | None] = mapped_column(default=0.1)

    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('russian', coalesce(name,''))", persisted=True),
        nullable=False
    )

    prices: Mapped[list["PriceHistory"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="noload"
    )
    category: Mapped["Category"] = relationship(
        back_populates="items",
        lazy="selectin"
    )

    _modifications: Mapped[str | None] = mapped_column("modifications", String, nullable=True)

    @hybrid_property
    def modifications(self) -> list[int]:
        if not self._modifications:
            return []
        return [int(v) for v in self._modifications.split(",") if v]

    @modifications.setter
    def modifications(self, value: list[int] | None):
        self._modifications = ",".join(str(v) for v in value) if value else None
