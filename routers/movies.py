import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from pymongo.collection import Collection

from api.core.config import Settings
from api.core.database import get_mongo_db
from api.core.security import verify_token
from api.models.movie import MovieListResponse, MovieResponse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/", response_model=MovieListResponse)
async def get_movies(
    skip: int = 0,
    limit: int = 10,
    db: Database = Depends(get_mongo_db),
    settings: Settings = Depends(),
    payload: dict = Depends(verify_token)
):
    """
    List movies with pagination.

    Args:
        skip: Number of movies to skip.
        limit: Maximum number of movies to return.
        db: MongoDB database dependency.
        settings: Application settings.
        payload: Decoded JWT payload.

    Returns:
        A MovieListResponse containing a list of movies and the total count.
    """
    try:
        movies_collection: Collection = db["movies"]
        total = movies_collection.count_documents({})
        movies = list(movies_collection.find({}, {"embedding": 0, "_id": 0}).skip(skip).limit(limit))
        movies_response = [MovieResponse(**movie) for movie in movies]
        logging.info(f"Retrieved {len(movies)} movies. Total movies: {total}")

        return MovieListResponse(movies=movies_response, total=total)
    except Exception as e:
        logging.error(f"Error retrieving movies: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving movies") from e


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(
    movie_id: str,
    db: Database = Depends(get_mongo_db),
    payload: dict = Depends(verify_token)
):
    """
    Get details for a specific movie by its ID.

    Args:
        movie_id: The ID of the movie to retrieve.
        db: MongoDB database dependency.
        payload: Decoded JWT payload.

    Returns:
        The MovieResponse for the requested movie.
    """
    try:
        movies_collection: Collection = db["movies"]
        movie = movies_collection.find_one({"movieId_ml": movie_id}, {"embedding": 0, "_id": 0})
        if movie:
            logging.info(f"Retrieved movie with ID: {movie_id}")
            return MovieResponse(**movie)
        else:
            logging.warning(f"Movie with ID {movie_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
    except Exception as e:
        logging.error(f"Error retrieving movie with ID {movie_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving movie") from e