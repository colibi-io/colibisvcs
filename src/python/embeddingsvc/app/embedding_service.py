import asyncio
from nats.aio.client import Client
import os


import logging
from ragatouille import RAGPretrainedModel
from embedding.v1.embedding_pb2_grpc import EmbeddingServiceServicer
from embedding.v1.embedding_pb2 import CreateProductResponse, Status, QueryResult, QueryProductResponse


from .schemas import EmbeddingIndexer


class EmbeddingService(EmbeddingServiceServicer):

    def __init__(self, broker: Client):
        # Initialize COLBERT model
        logging.info(
            f"Initializing COLBERT model with index path: {os.getenv('INDEX_PATH')}"
        )
        self.__indexer = RAGPretrainedModel.from_pretrained(
            pretrained_model_name_or_path="colbert-ir/colbertv2.0",
            index_root=os.getenv("INDEX_PATH"),
        )
        self.__broker = broker
        
    async def __indexing(self, hashed_store_id: str, products: str):
        index_path = self.__indexer.index(collection=[products], index_name=hashed_store_id)
        indexer = EmbeddingIndexer(hashed_store_id=hashed_store_id, path=index_path)
        await self.__broker.publish(os.getenv("EMBEDDING_CREATED"), indexer.model_dump_json().encode("utf-8"))
        

    async def CreateProduct(self, request, context):
        logging.info("Received CREATE request")
        
        # Run the heavy task in the background
        asyncio.get_event_loop().create_task(self.__indexing(request.product.hashed_store_id, request.product.text))
        
        return CreateProductResponse(
            hashed_store_id=request.product.hashed_store_id,
            status=Status.STATUS_RECEIVED,
        )

    async def QueryProduct(self, request, context):
        query = request.query
        hashed_store_id = request.hashed_store_id
        k = request.k

        """Queries products based on given query text."""
        # Extract query text and other relevant information from the request
        RETRIEVER = RAGPretrainedModel.from_index(
            f"{os.getenv('QUERY_PATH')}/{hashed_store_id}"
        )

        # Perform the search
        search_results = RETRIEVER.search(query=query, k=k)

        # Construct the query results
        results = [
            QueryResult(
                content=result["content"],
                score=result["score"],
                rank=result["rank"],
                document_id=result["document_id"],
                passage_id=result["passage_id"],
            )
            for result in search_results
        ]

        # Create the response object
        response = QueryProductResponse(
            hashed_store_id=request.hashed_store_id,
            query=query,
            results=results,
        )

        # Return the response
        return response
