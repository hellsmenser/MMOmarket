from pydantic import BaseModel, Field
from typing import Optional, List
from app.db.schemas.category import CategoryShort


class ItemBase(BaseModel):
    name: str = Field(..., example="Sword of Valor")
    modifications: Optional[List[int]] = Field(default=None, example=[3, 5, 10])
    image: Optional[str] = Field(default="PLACEHOLDER", example="http://example.com/img.png")

class ItemCreate(ItemBase):
    category_id: Optional[int] = Field(default=None, example=1)

class ItemShort(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    modifications: Optional[List[int]] = None
    image: Optional[str] = None
    category_id: Optional[int] = None

class ItemOut(BaseModel):
    id: int
    name: str
    modifications: list[int]
    image: str
    category: CategoryShort
    tolerance: Optional[float] = Field(default=0.1, example=0.05)

    class Config:
        from_attributes = True