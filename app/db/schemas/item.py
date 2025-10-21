from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from app.db.schemas.category import CategoryShort


class ItemBase(BaseModel):
    name: str = Field(..., example="Sword of Valor")
    modifications: Optional[List[int]] = Field(default=None, example=[3, 5, 10])


class ItemCreate(ItemBase):
    category_id: Optional[int] = Field(default=None, example=1)


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    modifications: Optional[List[int]] = None
    category_id: Optional[int] = None


class ItemOut(BaseModel):
    id: int
    name: str
    modifications: list[int] = Field(default_factory=list)
    category: CategoryShort
    tolerance: Optional[float] = Field(default=0.1, example=0.05)

    @field_validator("modifications", mode="before")
    def ensure_list(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return [int(m) for m in v]
        if isinstance(v, str):
            return [int(m) for m in v.split(",") if m]
        return []

    class Config:
        from_attributes = True

class ItemSearchOut(BaseModel):
    Items: List[ItemOut]
    Total: int

    class Config:
        from_attributes = True

class ItemActivity(BaseModel):
    id: int
    name: str
    category: CategoryShort
    price: int = Field(default=None, example=3600000)
    currency: str = Field(default="adena", example="adena")
    activity: int

    class Config:
        from_attributes = True
        validate_by_name = True
