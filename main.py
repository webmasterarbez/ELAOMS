"""Main FastAPI application for ELAOMS."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from database import init_db
from webhooks import post_call, client_data, search_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Eleven Labs Agents Open Memory System (ELAOMS)",
    description="Webhook service for integrating Eleven Labs Agents with OpenMemory",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include webhook routers
app.include_router(post_call.router)
app.include_router(client_data.router)
app.include_router(search_data.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Eleven Labs Agents Open Memory System (ELAOMS)",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

