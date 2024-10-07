import hashlib
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Column, DateTime, String, func
from sqlalchemy.orm import declarative_base

# Application models
class QueryBase(BaseModel):
    query: str
    k: int = 10
    simplify: bool = False

    # Using ConfigDict correctly
    model_config = ConfigDict(from_attributes=True)
    

class QueryRequest(QueryBase):
    pass
    
    
    