import logging
import os

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import Settings
from api.routers import movies, interactions, recommendations, auth

app = FastAPI()

settings = Settings()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

origins = [os.getenv("FRONTEND_URL", "*")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies.router)
app.include_router(interactions.router)
app.include_router(recommendations.router)
app.include_router(auth.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logging.info("App is up and running")
    return {"status": "ok"}