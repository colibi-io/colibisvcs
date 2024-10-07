import asyncio
import hashlib
import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from sqlalchemy.future import select
from http import HTTPStatus
from urllib.parse import unquote
import os
import grpc
from app.auth.token_verifier import TokenVerifier
from embedding.v1.embedding_pb2_grpc import EmbeddingServiceStub
from embedding.v1.embedding_pb2 import CreateProductRequest, Product, Status
from nats.aio.client import Client
from sqlalchemy.exc import MultipleResultsFound
from .models import Store, StorePatchIn, StoreOut, StoreCreateIn
from .database import get_session
from sqlalchemy.ext.asyncio import AsyncSession


async def get_store_identity(security_scopes: SecurityScopes, token: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> str:
    token = await TokenVerifier().verify(security_scopes, token)
    return token['sub']

class StoreService:
    def __init__(self, broker: Client):
        self.__router = APIRouter()
        self.__setup()
        self.__broker = broker
        asyncio.create_task(self.__broker.subscribe(os.getenv("EMBEDDING_CREATED"), cb=self.__handle_broker_message))

    def __setup(self):
        self.__router.add_api_route("/store/exists", self.__check_store_exists, methods=["GET"], response_model=dict)
        self.__router.add_api_route("/store", self.__read_store, methods=["GET"], response_model=StoreOut)
        self.__router.add_api_route("/store", self.__create_store, methods=["POST"], response_model=StoreOut, status_code=HTTPStatus.CREATED)
        self.__router.add_api_route("/store", self.__update_store, methods=["PATCH"], response_model=StoreOut)
        self.__router.add_api_route("/store", self.__delete_store, methods=["DELETE"], response_model=StoreOut)

    # Calculate the hash from the content of the products field
    def __calculate_hash(self, products: str):
        return hashlib.sha256(products.encode("utf-8")).hexdigest()
    

    async def __create_embedding(self, hash_store_id: str, text: str):
        async with grpc.aio.insecure_channel(os.getenv("EMBEDDING_GRPC")) as channel:
            stub = EmbeddingServiceStub(channel)
            create_product_request = CreateProductRequest(
                product=Product(
                    hashed_store_id=hash_store_id,
                    text=text
                )
            )
            response = await stub.CreateProduct(create_product_request)
            print(f"gRPC response: {response}")
            if response.status == Status.STATUS_FAILED:
                raise HTTPException(status_code=500, detail="Failed to create embedding")

    async def __check_store_exists(
        self,
        db: AsyncSession = Depends(get_session),
        store_id: str = Depends(get_store_identity)
    ):
        statement = select(Store).where(Store.id == store_id)
        result = await db.execute(statement)
        existing_store = result.scalar_one_or_none()
        if existing_store:
            return {"exists": True}
        else:
            return {"exists": False}

    async def __read_store(
        self,
        db: AsyncSession = Depends(get_session),
        store_id: str = Depends(get_store_identity)
    ):
        statement = select(Store).where(Store.id == store_id)
        result = await db.execute(statement)
        store = result.scalar_one_or_none()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        return StoreOut.model_validate(store)

    async def __create_store(
        self,
        create_in: StoreCreateIn,
        db: AsyncSession = Depends(get_session),
        store_id: str = Depends(get_store_identity)
        
    ):
        logging.info(f"User ID: {store_id}")
        statement = select(Store).where(Store.id == store_id)
        result = await db.execute(statement)
        existing_store = result.scalar_one_or_none()
        if existing_store:
            raise HTTPException(status_code=400, detail="Store with this id already exists")

        new_store = Store(
            id=store_id,
            products=create_in.products
        )

        db.add(new_store)
        await db.commit()
        await db.refresh(new_store)

        # Create gRPC client and call CreateProduct
        await self.__create_embedding(new_store.id_hashed, new_store.products)
        return StoreOut.model_validate(new_store)

    async def __update_store(
        self,
        update: StorePatchIn,
        db: AsyncSession = Depends(get_session),
        store_id: str = Depends(get_store_identity)
    ):
        statement = select(Store).where(Store.id == store_id )
        result = await db.execute(statement)
        existing_store = result.scalar_one_or_none()
        if not existing_store:
            raise HTTPException(status_code=404, detail=f"Store with the id {id} not found")

        if self.__calculate_hash(update.products) == existing_store.products_hashed:
            raise HTTPException(
                status_code=304, detail=f"The products haven't changed, no update needed"
            )
        existing_store.products = update.products
        existing_store.products_hashed = self.__calculate_hash(update.products)
        db.add(existing_store)
        await self.__create_embedding(existing_store.id_hashed, existing_store.products)
        await db.commit()
        await db.refresh(existing_store)
        return StoreOut.model_validate(existing_store)

    async def __delete_store(
        self,
        db: AsyncSession = Depends(get_session),
        store_id: str = Depends(get_store_identity)
    ):
        statement = select(Store).where(Store.id == store_id)
        result = await db.execute(statement)
        existing_store = result.scalar_one_or_none()
        if not existing_store:
            raise HTTPException(status_code=404, detail="Store not found")
        await db.delete(existing_store)
        await db.commit()
        return StoreOut.model_validate(existing_store)
    
    async def __handle_broker_message(self, msg):
        subject = msg.subject
        logging.info(f"Received a message on subject: {subject}")
        data = msg.data.decode()

        # Parse the JSON content
        try:
            json_data = json.loads(data)
            
            # Access values from the JSON object
            # For example, if the JSON contains a key
            hashed_store_id = json_data.get("hashed_store_id")
            embedded_index_path = json_data.get("path")
            async for db in get_session():
                result = await db.execute(select(Store).where(Store.id_hashed == hashed_store_id))
                store = result.scalar_one_or_none()
                if not store:
                    logging.error(f"Store with id_hashed {hashed_store_id} not found")
                    return
                
                store.embbded_index_path = embedded_index_path
                store.embedded = True
                db.add(store) # Ensure the store object is tracked by the session
                    
                await db.commit()
                logging.info(f"Store with id_hashed {hashed_store_id} updated successfully")
        
        except MultipleResultsFound as e:
            logging.error(f"Multiple stores found with the same id_hashed: {hashed_store_id}")
            
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON: {e}") 
    
    def get_router(self):
        return self.__router
    
    
