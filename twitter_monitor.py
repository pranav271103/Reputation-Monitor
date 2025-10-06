"""
Twitter monitoring module for tracking brand mentions and sentiment.
"""
import os
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
import logging
from dotenv import load_dotenv

# Import local modules
from database import MongoDBManager
from nlp_processor import NLPProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TwitterMonitor:
    """Monitor Twitter for brand mentions and analyze sentiment."""
    
    def __init__(self, bearer_token: str = None, db: MongoDBManager = None, nlp: NLPProcessor = None):
        """Initialize the Twitter monitor.
        
        Args:
            bearer_token: Twitter API bearer token. If not provided, will try to load from environment.
            db: Database manager instance. If not provided, a new one will be created.
            nlp: NLP processor instance. If not provided, a new one will be created.
        """
        load_dotenv()
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
        if not self.bearer_token:
            raise ValueError("Twitter bearer token not provided and not found in environment")
            
        # Initialize services
        self.db = db or MongoDBManager()
        self.nlp = nlp or NLPProcessor()
        
        if not self.db or not self.nlp:
            raise RuntimeError("Failed to initialize required services")
        self.brand_name = os.getenv("BRAND_NAME", "")
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Twitter API client."""
        if not self.bearer_token:
            logger.error("Twitter Bearer Token not found in environment variables")
            return
        
        try:
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                wait_on_rate_limit=True
            )
            logger.info("Successfully initialized Twitter client")
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {e}")
            raise
    
    def search_tweets(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search for tweets containing the query
        
        Args:
            query: Search query
            max_results: Maximum number of results to return (1-100)
            
        Returns:
            List of tweet data dictionaries
        """
        try:
            # Validate inputs
            if not query or not isinstance(query, str):
                raise ValueError("Query must be a non-empty string")
                
            max_results = max(1, min(100, int(max_results)))  # Ensure between 1-100
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "User-Agent": "v2FullArchiveSearchPython"
            }
            
            # Prepare query parameters
            params = {
                'query': f"{query} -is:retweet",
                'max_results': max_results,
                'tweet.fields': 'created_at,public_metrics,text,author_id,entities,conversation_id,referenced_tweets',
                'expansions': 'author_id,referenced_tweets.id',
                'user.fields': 'name,username,profile_image_url,verified',
                'media.fields': 'url,preview_image_url,type'
            }
            
            # Make the request with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(
                        "https://api.twitter.com/2/tweets/search/recent",
                        headers=headers,
                        params=params,
                        timeout=10
                    )
                    
                    # Check rate limits
                    remaining_requests = int(response.headers.get('x-rate-limit-remaining', 1))
                    reset_time = int(response.headers.get('x-rate-limit-reset', 0))
                    
                    if response.status_code == 429:  # Rate limited
                        wait_time = max(reset_time - int(time.time()) + 5, 5)  # At least 5 seconds
                        logger.warning(f"Rate limited. Waiting {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                        
                    # Process successful response
                    if response.status_code == 200:
                        return self._process_twitter_response(response.json())
                    else:
                        logger.error(f"Twitter API error: {response.status_code} - {response.text}")
                        if response.status_code >= 500:  # Server error, retry
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        return []
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request failed: {str(e)} (Attempt {attempt + 1}/{max_retries})")
                    if attempt == max_retries - 1:  # Last attempt
                        raise
                    time.sleep(2 ** attempt)  # Exponential backoff
            
            return []
            
        except Exception as e:
            logger.error(f"Error in search_tweets: {str(e)}", exc_info=True)
            return []
    
    def _process_twitter_response(self, data: Dict) -> List[Dict]:
        """Process Twitter API response data
        
        Args:
            data: Twitter API response data
            
        Returns:
            List of processed tweet data dictionaries
        """
        tweets = []
        users = {user['id']: user for user in data.get('includes', {}).get('users', [])}
        
        for tweet in data.get('data', []):
            user = users.get(tweet['author_id'], {})
            tweet_data = {
                "tweet_id": tweet['id'],
                "text": tweet['text'],
                "created_at": tweet['created_at'],
                "author_username": user.get('username', 'unknown'),
                "author_name": user.get('name', 'Unknown'),
                "author_image": user.get('profile_image_url', ''),
                "retweets": tweet.get('public_metrics', {}).get('retweet_count', 0),
                "replies": tweet.get('public_metrics', {}).get('reply_count', 0),
                "likes": tweet.get('public_metrics', {}).get('like_count', 0),
                "quotes": tweet.get('public_metrics', {}).get('quote_count', 0),
                "source": "twitter",
                "url": f"https://twitter.com/{user.get('username')}/status/{tweet['id']}" if user.get('username') else ""
            }
            
            # Analyze sentiment
            sentiment = self.nlp.analyze_sentiment(tweet['text'])
            tweet_data.update({
                "sentiment": self._get_sentiment_label(sentiment),
                "sentiment_scores": sentiment
            })
            
            # Detect PII
            pii = self.nlp.detect_pii(tweet['text'])
            tweet_data["pii_detected"] = any(pii.values())
            tweet_data["pii_details"] = pii
            
            tweets.append(tweet_data)
        
        return tweets
    
    def _get_sentiment_label(self, sentiment_scores: Dict[str, float]) -> str:
        """Convert sentiment scores to a label (positive, neutral, negative)."""
        if sentiment_scores["compound"] >= 0.05:
            return "positive"
        elif sentiment_scores["compound"] <= -0.05:
            return "negative"
        else:
            return "neutral"
    
    def monitor_brand_mentions(self, save_to_db: bool = True) -> List[Dict]:
        """Monitor tweets mentioning the brand.
        
        Args:
            save_to_db: Whether to save results to the database
            
        Returns:
            List of processed tweets
        """
        if not self.brand_name:
            logger.error("Brand name not configured")
            return []
        
        # Search for brand mentions (excluding retweets)
        query = f"{self.brand_name} -is:retweet"
        tweets = self.search_tweets(query)
        
        if save_to_db and tweets:
            for tweet in tweets:
                self._save_to_db(tweet)
        
        return tweets
    
    def _save_to_db(self, tweet_data: Dict) -> bool:
        """Save tweet data to the database
        
        Args:
            tweet_data: Dictionary containing tweet data
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Add timestamp if not present
            if 'created_at' not in tweet_data:
                tweet_data['created_at'] = datetime.utcnow()
                
            # Add source and ensure required fields
            tweet_data.update({
                'source': 'twitter',
                'tweet_id': str(tweet_data.get('tweet_id', '')),
                'created_at': tweet_data.get('created_at', datetime.utcnow())
            })
            
            # Check if tweet already exists
            existing = self.db.find_mentions({"tweet_id": tweet_data['tweet_id']}, limit=1)
            if existing:
                logger.debug(f"Tweet {tweet_data['tweet_id']} already exists in database")
                return True
                
            # Insert new tweet
            result = self.db.insert_mention(tweet_data)
            if result:
                logger.info(f"Saved tweet {tweet_data['tweet_id']} to database")
                return True
                
            logger.error(f"Failed to save tweet {tweet_data.get('tweet_id')}")
            return False
                
        except Exception as e:
            logger.error(f"Error saving tweet to database: {e}", exc_info=True)
            return False
    
    def get_trending_hashtags(self, limit: int = 10) -> List[Dict]:
        """Get currently trending hashtags related to the brand.
        
        Args:
            limit: Maximum number of hashtags to return
            
        Returns:
            List of trending hashtags with counts
        """
        if not self.client:
            logger.error("Twitter client not initialized")
            return []
        
        try:
            # Get recent tweets about the brand
            tweets = self.search_tweets(f"{self.brand_name} -is:retweet", max_results=100)
            
            # Extract hashtags
            hashtags = {}
            for tweet in tweets:
                text = tweet.get('text', '').lower()
                matches = set(re.findall(r'#(\w+)', text))
                for tag in matches:
                    if tag != self.brand_name.lower() and len(tag) > 2:  # Exclude brand name and very short tags
                        hashtags[tag] = hashtags.get(tag, 0) + 1
            
            # Sort by frequency and limit results
            sorted_hashtags = sorted(hashtags.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            return [{"tag": tag, "count": count} for tag, count in sorted_hashtags]
            
        except Exception as e:
            logger.error(f"Error getting trending hashtags: {e}")
            return []

# Global instance
twitter_monitor = TwitterMonitor()

def get_twitter_monitor() -> TwitterMonitor:
    """Get the global Twitter monitor instance."""
    return twitter_monitor
