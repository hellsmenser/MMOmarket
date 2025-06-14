from pydantic import BaseModel
from typing import List, Optional

from app.db.schemas.common import ItemShort


class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryShort(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CategoryOut(BaseModel):
    id: int
    name: str
    items: list[ItemShort]

    class Config:
        from_attributes = True

class ItemInCategory(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CategoryRead(CategoryBase):
    id: int
    items: Optional[List[ItemInCategory]] = []

    class Config:
        from_attributes = True