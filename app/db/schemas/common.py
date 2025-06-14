from pydantic import BaseModel

class ItemShort(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CategoryShort(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True