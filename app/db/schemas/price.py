from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.db.schemas.item import ItemOut


class PriceBase(BaseModel):
    item: ItemOut = Field(..., description="Item associated with the price")
    price: int = Field(..., example=3600000)
    enchant_level: Optional[int] = Field(default=None, example=5)
    currency: str = Field(..., example="adena")  # 'adena' или 'coin'
    source: Optional[str] = Field(default=None, example="WorldTrade"),
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, example="2023-10-01T12:00:00Z")


class PriceCreate(PriceBase):
    pass


class PriceUpdate(BaseModel):
    price: Optional[int] = None
    enchant_level: Optional[int] = None
    currency: Optional[str] = None
    source: Optional[str] = None


class PriceOut(PriceBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
