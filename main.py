import os
import logging
from dotenv import load_dotenv
from database import MongoDBManager
from google_search import GoogleSearchMonitor
from twitter_monitor import TwitterMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to demonstrate the reputation monitoring system."""
    # Load environment variables
    load_dotenv()
    
    # Initialize database
    try:
        db = MongoDBManager()
        if not db.is_connected():
            raise RuntimeError("Failed to connect to database")
        
        # Initialize monitors
        google_monitor = GoogleSearchMonitor(db=db)
        twitter_monitor = TwitterMonitor(db=db)
        
        # Example search
        brand_name = os.getenv("BRAND_NAME", "example")
        logger.info(f"Monitoring brand: {brand_name}")
        
        # Search Google
        logger.info("Searching Google...")
        google_results = google_monitor.search(brand_name, num_results=5)
        logger.info(f"Found {len(google_results)} Google results")
        
        # Search Twitter
        logger.info("Searching Twitter...")
        twitter_results = twitter_monitor.search_tweets(brand_name, max_results=5)
        logger.info(f"Found {len(twitter_results)} Twitter mentions")
        
        # Get stats
        stats = db.get_mention_stats()
        logger.info(f"Database stats: {stats}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main()