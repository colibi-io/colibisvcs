import hashlib
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Column, DateTime, String, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# Database models
class Store(Base):
    __tablename__ = "stores"
    id = Column(String(70), primary_key=True, nullable=False)
    id_hashed = Column(String(64), unique=True, nullable=False)
    kind = Column(String(50))
    products = Column(String)
    products_hashed = Column(String(64))
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    embedded = Column(Boolean, default=False)
    embbded_index_path = Column(String)
    

    def __init__(self, id, kind=None, products=None):
        if not id:
            raise ValueError("The 'id' field is required.")
        self.id = id
        self.id_hashed = hashlib.sha256(self.id.encode("utf-8")).hexdigest()
        self.kind = kind
        self.products = products
        self.products_hashed = hashlib.sha256(self.products.encode("utf-8")).hexdigest()


# Application models
class StoreBase(BaseModel):
    products: str

    # Using ConfigDict correctly
    model_config = ConfigDict(from_attributes=True)


class StoreOut(StoreBase):
    pass


class StorePatchIn(StoreBase):
    pass

class StoreCreateIn(StoreBase):
    pass
