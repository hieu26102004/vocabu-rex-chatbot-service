"""MongoDB database connection and initialization"""
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from ..shared.config import settings
from .database.models import User, ChatConversation, ChatMessage
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager"""
    client: AsyncIOMotorClient = None
    database = None


mongodb = MongoDB()


async def connect_to_mongo():
    """Create database connection"""
    try:
        # Create MongoDB connection
        mongodb.client = AsyncIOMotorClient(settings.mongodb_url)
        mongodb.database = mongodb.client[settings.mongodb_database]
        
        # Initialize Beanie with document models
        await init_beanie(
            database=mongodb.database,
            document_models=[User, ChatConversation, ChatMessage]
        )
        
        logger.info(f"Connected to MongoDB: {settings.mongodb_database}")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close database connection"""
    try:
        if mongodb.client:
            mongodb.client.close()
            logger.info("Disconnected from MongoDB")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")


async def get_database():
    """Get database instance"""
    return mongodb.database