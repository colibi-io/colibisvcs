import asyncio
from functools import lru_cache
import logging
import os
from fastapi import FastAPI, Request, Security
from fastapi.middleware.cors import CORSMiddleware
import nats
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
import uvicorn
from app.auth.token_verifier import TokenVerifier
from app.store import StoreService
from app.semantic_search import SemanticSearchService          
from app.health import health_router
import hupper
from fastapi import APIRouter


logging.basicConfig(level=logging.INFO)

class CORSAddr(BaseSettings):
    model_config = ConfigDict(
        prefix="API_",
        env_file=".env.dev" if os.getenv("ENV") == "dev" else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    api_cors_origins: str

class WebApi:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)


    @lru_cache()
    def __get_cors_addrs(self):
        return CORSAddr()
    

    async def config_services(self):
        nc = await nats.connect(os.getenv("MESSAGE_BROKER_HOST"))
        logging.info(f"Connectt to NATS servers")
        
        token_verifier = TokenVerifier()
        
        app = FastAPI()
        # Configure CORS 
        cors_origins = self.__get_cors_addrs().api_cors_origins.split(",")
        logging.info(f"Configuring CORS for origins: {cors_origins}")
        app.add_middleware(
            CORSMiddleware,
            allow_origins="*",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
                
        # Include the store router
        
        app.include_router(health_router)
        
        store_service = StoreService(broker=nc)
        app.include_router(store_service.get_router(), prefix="/api", dependencies=[Security(token_verifier.verify)])
        
        
        # semantic_search_service = SemanticSearchService()
        # app.include_router(semantic_search_service.get_router(), prefix="/internal")
        
    
        # Start the FastAPI server
        logging.info(f"Starting FastAPI server on port {os.getenv('SERVER_PORT')}")
        config = uvicorn.Config(app, host="0.0.0.0", port=int(os.getenv("SERVER_PORT")), log_level="info")
        await uvicorn.Server(config).serve()

    def run(self):
        asyncio.run(self.config_services())

def start():
    api = WebApi()
    api.run()

if __name__ == "__main__":
    if os.getenv("ENV") == "dev":
        logging.info("Running in development mode")
        reloader = hupper.start_reloader("main.start")
    else:
       start() 