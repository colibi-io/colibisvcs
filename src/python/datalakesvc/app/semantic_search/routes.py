


from http import HTTPStatus
import os
from fastapi import APIRouter
import grpc


from .models import QueryRequest


class SemanticSearchService:
    def __init__(self):
        self.__router = APIRouter()
        self.__setup()
        
    def __setup(self):
        self.__router.add_api_route("/query/{store_id}", self.__query, methods=["POST"], response_model=list[str], status_code=HTTPStatus.OK)
        
    async def __query(
        self,
        store_id: str,
        params: QueryRequest,
    ) -> list[str]: 
        async with grpc.aio.insecure_channel(os.getenv("EMBEDDING_GRPC")) as channel:
            stub = EmbeddingServiceStub(channel)
            request = messages.QueryProductRequest(
                hashed_store_id=store_id,
                query=params.query,
                k=params.k if params.k is not None else 10,
            )
            response = await stub.QueryProduct(request)
            return [result.content for result in response.results]

    def get_router(self):
        return self.__router
            