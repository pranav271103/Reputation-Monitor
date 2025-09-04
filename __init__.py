"""
Brand Reputation Monitoring System

This package provides tools for monitoring and analyzing brand mentions
across various online platforms including Google Search and Twitter.
"""

__version__ = '1.0.0'

# Import key components for easier access
from .database import MongoDBManager
from .nlp_processor import NLPProcessor
from .twitter_monitor import TwitterMonitor
from .google_search import GoogleSearchMonitor

# Initialize global instances
db_manager = None
nlp_processor = None

def init_services():
    """Initialize global service instances"""
    global db_manager, nlp_processor
    
    # Initialize database manager
    db_manager = MongoDBManager()
    
    # Initialize NLP processor
    nlp_processor = NLPProcessor()
    
    return db_manager, nlp_processor

# Initialize services when package is imported
db_manager, nlp_processor = init_services()
