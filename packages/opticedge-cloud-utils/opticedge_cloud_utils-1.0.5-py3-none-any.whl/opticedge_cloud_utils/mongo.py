import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from opticedge_cloud_utils.secrets import get_secret

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---- Module-level singletons ----
_mongo_client: Optional[MongoClient] = None

def get_mongo_client(project_id: str, uri_secret: str) -> MongoClient:
    """Return a cached MongoClient."""
    global _mongo_client
    if _mongo_client is not None:
        return _mongo_client

    uri = get_secret(project_id, uri_secret)
    try:
        logger.info("Creating new MongoClient (will be cached).")
        client = MongoClient(uri)
        client.admin.command("ping")  # test connection
    except Exception:
        logger.exception("Failed to connect to MongoDB")
        raise

    _mongo_client = client
    return _mongo_client

def get_mongo_client_with_uri(uri: str) -> MongoClient:
    """Return a cached MongoClient."""
    global _mongo_client
    if _mongo_client is not None:
        return _mongo_client

    try:
        logger.info("Creating new MongoClient (will be cached).")
        client = MongoClient(uri)
        client.admin.command("ping")  # test connection
    except Exception:
        logger.exception("Failed to connect to MongoDB")
        raise

    _mongo_client = client
    return _mongo_client

def get_mongo_db(project_id: str, uri_secret: str, db_name: str) -> Database:
    """Return a Database instance for use in request handlers."""
    client = get_mongo_client(project_id, uri_secret)
    logger.info("Using database: %s", db_name)
    return client[db_name]

def get_mongo_db_with_uri(uri: str, db_name: str) -> Database:
    """Return a Database instance for use in request handlers."""
    client = get_mongo_client_with_uri(uri)
    logger.info("Using database: %s", db_name)
    return client[db_name]
