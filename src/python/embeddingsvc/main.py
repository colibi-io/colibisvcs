import asyncio
import os
import time
import nats
from nats.aio.client import Client

from app import EmbeddingService
from embedding.v1.embedding_pb2_grpc import add_EmbeddingServiceServicer_to_server
from embedding.v1.embedding_pb2 import DESCRIPTOR
import grpc
from concurrent import futures
from grpc_reflection.v1alpha import reflection
import logging
import hupper


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

async def grpc_server(broker: Client):
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    add_EmbeddingServiceServicer_to_server(EmbeddingService(broker=broker), server)

    # Enable reflection
    SERVICE_NAMES = (
        DESCRIPTOR.services_by_name["EmbeddingService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.add_insecure_port(f"[::]:{os.getenv('GRPC_PORT')}")
    await server.start()
    logging.info(f"gRPC server started, listening on port {os.getenv('GRPC_PORT')}")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await server.stop(0)
        
    await server.wait_for_termination()
    await broker.drain()
   
async def app():
   nc = await nats.connect(os.getenv("MESSAGE_BROKER_HOST"))
   logging.info(f"NATS servers ${nc.servers}")
   await grpc_server(nc)

def run_app():
    asyncio.run(app())


if __name__ == "__main__":
    if os.getenv("ENV") == "DEV":
        reloader = hupper.start_reloader("main.run_app")
    else:
        run_app()
