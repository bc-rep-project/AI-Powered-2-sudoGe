import logging
from typing import List, Optional
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from redis import Redis
from pymongo.database import Database
from pymongo.collection import Collection

from sklearn.metrics.pairwise import cosine_similarity

from api.core.config import Settings

from api.core.database import get_mongo_db, get_redis_client
from api.core.security import verify_token
from api.models.movie import MovieResponse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/", response_model=List[MovieResponse])
async def get_recommendations(
    payload: dict = Depends(verify_token),
    db: Database = Depends(get_mongo_db),
    redis_client: Redis = Depends(get_redis_client),
    settings: Settings = Depends(),
):
    """
    Get movie recommendations for a user.

    This endpoint retrieves movie recommendations based on user interactions and cached data.

    Args:
        payload: The decoded JWT payload (containing user information).
        db: The MongoDB database instance.
        redis_client: The Redis client instance.
        settings: The application settings.

    Returns:
        A list of MovieResponse objects representing the recommended movies.

    Raises:
        HTTPException: If any error occurs during the recommendation process.
    """
    try:
        user_id = payload["sub"]
        logging.info(f"Generating recommendations for user: {user_id}")

        # Check Redis cache for recommendations
        cached_recommendations = redis_client.get(f"recommendations:{user_id}")
        if cached_recommendations:
            logging.info(f"Recommendations found in cache for user: {user_id}")
            movie_ids = cached_recommendations.split(",")
            movies_collection: Collection = db["movies"]
            movies = list(movies_collection.find({"movieId_ml": {"$in": movie_ids}},{"embedding": 0}))
            return [MovieResponse(**movie) for movie in movies]


        # If not cached, fall back to basic recommendations (e.g., most popular)
        logging.info(f"Recommendations not found in cache for user: {user_id}. Generating fallback recommendations.")
        movies_collection: Collection = db["movies"]
        top_movies = list(movies_collection.find({},{"embedding": 0}).limit(10))

        if not top_movies:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

        # Cache basic recommendations for the user (optional)
        movie_ids_to_cache = [movie["movieId_ml"] for movie in top_movies]
        redis_client.set(f"recommendations:{user_id}", ",".join(movie_ids_to_cache), ex=3600)  # Cache for 1 hour

        return [MovieResponse(**movie) for movie in top_movies]

    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error generating recommendations for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating recommendations",
        ) from e

@router.get("/item/{movie_id_ml}", response_model=List[MovieResponse])
async def get_item_recommendations(
    movie_id_ml: str,
    payload: dict = Depends(verify_token),
    db: Database = Depends(get_mongo_db),
    redis_client: Redis = Depends(get_redis_client),
    settings: Settings = Depends(),
):
    """
    Get movie recommendations based on a given movie.

    This endpoint retrieves movie recommendations based on the similarity to a given movie.

    Args:
        movie_id_ml: The ID of the movie to get recommendations for.
        payload: The decoded JWT payload (containing user information).
        db: The MongoDB database instance.
        redis_client: The Redis client instance.
        settings: The application settings.

    Returns:
        A list of MovieResponse objects representing the recommended movies.

    Raises:
        HTTPException: If any error occurs during the recommendation process.
    """
    try:
        user_id = payload["sub"]
        logging.info(f"Generating recommendations based on movie: {movie_id_ml} for user: {user_id}")

        # 1. Check Redis cache for recommendations
        cached_recommendations = redis_client.get(f"item_recommendations:{movie_id_ml}")
        if cached_recommendations:
            logging.info(f"Recommendations found in cache for movie: {movie_id_ml}")
            movie_ids = cached_recommendations.split(",")
            movies_collection: Collection = db["movies"]
            movies = list(movies_collection.find({"movieId_ml": {"$in": movie_ids}},{"embedding": 0}))
            return [MovieResponse(**movie) for movie in movies]

        # 2. Fetch the embedding for the target movie
        movies_collection: Collection = db["movies"]
        target_movie = movies_collection.find_one({"movieId_ml": movie_id_ml},{"embedding":1})

        if not target_movie or "embedding" not in target_movie:
            logging.warning(f"Could not find embedding for movie: {movie_id_ml}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie embedding not found.")

        target_embedding = np.array(target_movie["embedding"]).reshape(1, -1)

        # 3. Fetch candidate movie embeddings (Limit to 500 candidates)
        candidate_movies = list(movies_collection.aggregate([
            { "$match": { "movieId_ml": { "$ne": movie_id_ml } } },
            { "$sample": { "size": 500 } }
        ]))
        candidate_embeddings = np.array([movie["embedding"] for movie in candidate_movies])

        # 4. Calculate similarity
        similarities = cosine_similarity(target_embedding, candidate_embeddings)[0]

        # 5. Aggregate and rank
        ranked_candidates = sorted(zip(candidate_movies, similarities), key=lambda x: x[1], reverse=True)

        # 6. Filter out seen movies (if user data is available)
        interactions_collection: Collection = db["interactions"]
        seen_movie_ids = {interaction["movieId_ml"] for interaction in interactions_collection.find({"userId": user_id})}
        filtered_candidates = [(movie, score) for movie, score in ranked_candidates if movie["movieId_ml"] not in seen_movie_ids]

        # 7. Get top N recommendations (e.g., top 10)
        top_n = 10
        top_recommendations = [movie for movie, score in filtered_candidates[:top_n]]

        # 8. Fetch movie details (excluding embeddings)
        recommended_movie_ids = [movie["movieId_ml"] for movie in top_recommendations]
        recommended_movies = list(movies_collection.find({"movieId_ml": {"$in": recommended_movie_ids}},{"embedding": 0}))

        # 9. Store in cache
        redis_client.set(f"item_recommendations:{movie_id_ml}", ",".join(recommended_movie_ids), ex=3600)  # Cache for 1 hour

        logging.info(f"Generated recommendations for movie {movie_id_ml}")
        return [MovieResponse(**movie) for movie in recommended_movies]

    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error generating item-based recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating item-based recommendations",
        ) from e