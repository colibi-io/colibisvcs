# Embedding Service

This repository provides a gRPC-based service for managing and querying product embeddings using the ColBERT (Contextualized Late Interaction over BERT) model. The service is designed to handle large-scale text retrieval tasks efficiently by leveraging deep contextualized language models.

## Features

- **Create Product Embeddings**: Allows users to create embeddings for products by providing text descriptions. The embeddings are indexed and stored for efficient retrieval.
- **Query Product Embeddings**: Enables users to query the indexed embeddings using natural language queries. The service returns relevant results based on the query.
- **gRPC Interface**: The service is built using gRPC, providing a robust and scalable interface for communication.
- **Reflection Support**: gRPC reflection is enabled for easy inspection and interaction with the service.

## Components

### Main Application (`main.py`)

The main application sets up and starts the gRPC server, registering the `EmbeddingService` and enabling reflection. It listens on port 10000 for incoming requests.

### Embedding Service (`embedding_service.py`)

The core service implementation, `EmbeddingService`, provides methods for creating and querying product embeddings. It uses the ColBERT model for embedding creation and retrieval.

### Unit Tests (`test_embedding_service.py`)

Unit tests for the `EmbeddingService` are provided to ensure the correctness of the create and query functionalities. The tests use a gRPC test server to simulate real interactions.

### Starting DEV environment with docker-compose and .env file
```bash
docker compose --env-file .env.dev -f docker-compose.dev.yml up
```