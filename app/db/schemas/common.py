from pydantic import BaseModel

class ItemShort(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True