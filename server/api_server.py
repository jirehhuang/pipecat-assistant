"""FastAPI server for standalone query processing."""

import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel, Field

from custom._standalone_processor import _standalone_processor_factory

load_dotenv(override=True)


async def verify_api_key(x_api_key: str = Header(...)):
    """Verify the API key from the request header."""
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API Key")


class QueryRequest(BaseModel):
    """Request model for query endpoint."""

    query: str = Field(..., description="The query to process")


class QueryResponse(BaseModel):
    """Response model for query endpoint."""

    response: str = Field(..., description="The assistant's response")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize resources on startup."""
    logger.info("Initializing API server...")
    _ = _standalone_processor_factory.standalone_processor
    logger.info("API server ready")
    yield
    logger.info("Shutting down API server...")


app = FastAPI(
    title="Pipecat Assistant API",
    description="Direct API access to the Pipecat assistant",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post(
    "/query",
    response_model=QueryResponse,
    dependencies=[Depends(verify_api_key)],
)
async def process_query(request: QueryRequest):
    """Process a query and return the assistant's response.

    Parameters
    ----------
    request
        Query request containing the query.

    Returns
    -------
        QueryResponse with the assistant's response
    """
    try:
        processor = _standalone_processor_factory.standalone_processor
        response = await processor.process_query(
            query=request.query,
        )
        return QueryResponse(response=response)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Pipecat Assistant API",
        "endpoints": {
            "POST /query": "Process a query",
            "GET /health": "Health check",
        },
    }


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )
