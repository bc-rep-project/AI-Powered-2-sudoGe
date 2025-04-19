import redis
import logging
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from pymongo.database import Database
from pymongo.collection import Collection
from api.models.user import User

from api.core.config import Settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_mongo_db(settings: Settings):
    """Connects to MongoDB and returns the database.

    Args:
        settings: An instance of the Settings class.

    Returns:
        The MongoDB database object.
    """
    try:
        client = MongoClient(settings.MONGODB_URI)
        db = client.get_database()
        client.admin.command('ping')
        logging.info("Connected to MongoDB successfully.")
        return db
    except ConnectionFailure as e:
        logging.error(f"Could not connect to MongoDB: {e}")
        raise


def get_redis_client(settings: Settings):
    """Connects to Redis and returns the client.

    Args:
        settings: An instance of the Settings class.

    Returns:
        The Redis client object.
    """
    try:
        client = redis.Redis.from_url(settings.REDIS_URL, password=settings.REDIS_PASSWORD, decode_responses=True)
        client.ping()
        logging.info("Connected to Redis successfully.")
        return client
    except redis.exceptions.ConnectionError as e:
        logging.error(f"Could not connect to Redis: {e}")
        raise


def create_user(db: Database, user: User):
    """Creates a new user in the database.

    Args:
        db: The MongoDB database object.
        user: The User object to be created.

    Returns:
        The created user as a dictionary if successful.

    Raises:
        HTTPException: If there is a duplicate key error.
    """
    try:
        users_collection: Collection = db["users"]
        user_dict = user.model_dump()
        result = users_collection.insert_one(user_dict)
        created_user = users_collection.find_one(
            {"_id": result.inserted_id}
        )

        logging.info(f"User {user.username} created successfully.")
        return created_user
    except DuplicateKeyError:
        logging.warning(f"Username {user.username} already exists.")
        return None


def find_user_by_username(db: Database, username: str):
    """Finds a user by username in the database.

    Args:
        db: The MongoDB database object.
        username: The username to search for.

    Returns:
        The user document as a dictionary if found, None otherwise.
    """
    users_collection: Collection = db["users"]
    user = users_collection.find_one({"username": username})
    if user:
        logging.info(f"User {username} found.")
    return user