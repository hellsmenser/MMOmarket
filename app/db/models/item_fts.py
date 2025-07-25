from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ItemFTS(Base):
    __tablename__ = "items_fts"
    __table_args__ = {"sqlite_with_rowid": False}

    rowid = Column(Integer, primary_key=True)
    name = Column(String)