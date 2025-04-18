import redis
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

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