import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBManager:
    """MongoDB database manager for the reputation monitoring system."""
    
    def __init__(self, connection_string: str = None, db_name: str = None):
        """Initialize MongoDB connection.
        
        Args:
            connection_string: MongoDB connection string
            db_name: Database name
        """
        load_dotenv()
        
        self.connection_string = connection_string or os.getenv("MONGO_URI")
        self.db_name = db_name or os.getenv("MONGO_DB", "reputation_monitor")
        self.client = None
        self.db = None
        
        self._connect()
    
    def _connect(self) -> bool:
        """Establish connection to MongoDB.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            if not self.connection_string:
                raise ValueError("MongoDB connection string not provided")
                
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=30000,         # 30 second connection timeout
                socketTimeoutMS=30000           # 30 second socket timeout
            )
            
            # Test the connection
            self.client.server_info()
            self.db = self.client[self.db_name]
            
            # Create indexes
            self._create_indexes()
            
            logger.info(f"Connected to MongoDB: {self.db_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            self.db = None
            return False
    
    def _create_indexes(self) -> None:
        """Create necessary indexes for optimal query performance."""
        try:
            if not self.db:
                raise RuntimeError("Database not connected")
                
            # Index for mentions collection
            self.db.mentions.create_index([("created_at", DESCENDING)])
            self.db.mentions.create_index([("source", ASCENDING)])
            self.db.mentions.create_index([("risk_score", DESCENDING)])
            self.db.mentions.create_index([("category", ASCENDING)])
            self.db.mentions.create_index([("pii_detected", ASCENDING)])
            
            logger.debug("Created database indexes")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def is_connected(self) -> bool:
        """Check if the database connection is active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            if self.client:
                self.client.server_info()  # Will raise an exception if not connected
                return True
            return False
        except:
            return False
    
    def insert_mention(self, data: Dict) -> bool:
        """Insert a new mention into the database.
        
        Args:
            data: Dictionary containing mention data
            
        Returns:
            bool: True if insert was successful, False otherwise
        """
        try:
            if not self.db:
                raise RuntimeError("Database not connected")
                
            # Add timestamps
            data['created_at'] = data.get('created_at', datetime.utcnow())
            data['updated_at'] = datetime.utcnow()
            
            # Insert the document
            result = self.db.mentions.insert_one(data)
            return result.inserted_id is not None
            
        except Exception as e:
            logger.error(f"Error inserting mention: {e}")
            return False
    
    def find_mentions(self, query: Dict = None, limit: int = 100, sort: tuple = None) -> List[Dict]:
        """Find mentions matching the query.
        
        Args:
            query: MongoDB query document
            limit: Maximum number of results to return
            sort: Tuple of (field, direction) to sort by
            
        Returns:
            List of matching mention documents
        """
        try:
            if not self.db:
                raise RuntimeError("Database not connected")
                
            cursor = self.db.mentions.find(query or {})
            
            if sort:
                cursor = cursor.sort(*sort)
            if limit > 0:
                cursor = cursor.limit(limit)
                
            return list(cursor)
            
        except Exception as e:
            logger.error(f"Error finding mentions: {e}")
            return []
    
    def update_mention(self, mention_id: str, updates: Dict) -> bool:
        """Update a mention in the database.
        
        Args:
            mention_id: ID of the mention to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            if not self.db:
                raise RuntimeError("Database not connected")
                
            # Add updated_at timestamp
            updates['updated_at'] = datetime.utcnow()
            
            result = self.db.mentions.update_one(
                {"_id": mention_id},
                {"$set": updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating mention {mention_id}: {e}")
            return False
    
    def delete_mention(self, mention_id: str) -> bool:
        """Delete a mention from the database.
        
        Args:
            mention_id: ID of the mention to delete
            
        Returns:
            bool: True if delete was successful, False otherwise
        """
        try:
            if not self.db:
                raise RuntimeError("Database not connected")
                
            result = self.db.mentions.delete_one({"_id": mention_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting mention {mention_id}: {e}")
            return False
    
    def clear_mentions(self) -> bool:
        """Remove all mentions from the database.
        
        Returns:
            bool: True if operation was successful, False otherwise
        """
        try:
            if not self.db:
                raise RuntimeError("Database not connected")
                
            result = self.db.mentions.delete_many({})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error clearing mentions: {e}")
            return False
    
    def get_mention_stats(self) -> Dict[str, Any]:
        """Get statistics about mentions in the database.
        
        Returns:
            Dictionary containing various statistics
        """
        try:
            if not self.db:
                raise RuntimeError("Database not connected")
                
            stats = {
                "total_mentions": self.db.mentions.count_documents({}),
                "by_source": list(self.db.mentions.aggregate([
                    {"$group": {"_id": "$source", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ])),
                "by_category": list(self.db.mentions.aggregate([
                    {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ])),
                "pii_detected": self.db.mentions.count_documents({"pii_detected": True}),
                "high_risk": self.db.mentions.count_documents({"risk_score": {"$gte": 70}})
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting mention stats: {e}")
            return {}
    
    def close(self) -> None:
        """Close the database connection."""
        try:
            if self.client:
                self.client.close()
                self.client = None
                self.db = None
                logger.info("Closed MongoDB connection")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

    def __del__(self):
        """Destructor to ensure connections are closed."""
        self.close()