import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from pymongo.results import InsertOneResult

from api.core.config import Settings
from api.core.database import get_mongo_db
from api.core.security import verify_token
from api.models.interaction import InteractionCreate, InteractionResponse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("/", response_model=InteractionResponse)
async def create_interaction(
    interaction: InteractionCreate,
    payload: dict = Depends(verify_token),
    db: Database = Depends(get_mongo_db),
    settings: Settings = Depends(),
):
    """
    Create a new interaction.

    Args:
        interaction: The interaction data.
        payload: The decoded JWT payload.
        db: The MongoDB database.
        settings: The application settings.

    Returns:
        The created interaction.
    """
    try:
        user_id = payload["sub"]
        interaction_data = interaction.model_dump()
        interaction_data["userId"] = user_id
        interaction_data["timestamp"] = datetime.utcnow()

        interactions_collection = db["interactions"]
        result: InsertOneResult = interactions_collection.insert_one(interaction_data)
        
        created_interaction = interactions_collection.find_one({"_id": result.inserted_id})
        logging.info(f"Interaction created successfully for user: {user_id}")
        return InteractionResponse(**created_interaction)

    except Exception as e:
        logging.error(f"Error creating interaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating interaction",
        ) from e