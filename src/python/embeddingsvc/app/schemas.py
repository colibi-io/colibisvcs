from pydantic import BaseModel


class EmbeddingIndexer(BaseModel):
    hashed_store_id: str
    path: str