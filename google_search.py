import os
import json
import re
import time
import random
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from urllib.parse import urlparse, quote_plus
from dotenv import load_dotenv

# Import local modules
from database import MongoDBManager
from nlp_processor import NLPProcessor

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GoogleSearchMonitor:
    """Monitor Google Search results for brand mentions."""
    
    def __init__(self, api_key: str = None, cse_id: str = None, 
                 brand_name: str = None, db: MongoDBManager = None, 
                 nlp: NLPProcessor = None):
        """Initialize the Google Search monitor.
        
        Args:
            api_key: Google Custom Search API key
            cse_id: Google Custom Search Engine ID
            brand_name: Name of the brand to monitor
            db: Database manager instance
            nlp: NLP processor instance
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.cse_id = cse_id or os.getenv('GOOGLE_CSE_ID')
        self.brand_name = brand_name or os.getenv('BRAND_NAME', '')
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        # Initialize services
        self.db = db or MongoDBManager()
        self.nlp = nlp or NLPProcessor()
        
        if not all([self.api_key, self.cse_id]):
            raise ValueError("Google API key and CSE ID must be provided or set in environment variables")

    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search Google for the given query.
        
        Args:
            query: Search query string
            num_results: Number of results to return (1-100)
            
        Returns:
            List of search result dictionaries with analysis
        """
        try:
            # Validate inputs
            if not query or not isinstance(query, str):
                raise ValueError("Query must be a non-empty string")
                
            num_results = max(1, min(100, int(num_results)))  # Ensure between 1-100
            
            # Prepare the search query
            search_query = f"{query} {self.brand_name}" if self.brand_name else query
            
            # Execute the search with pagination
            results = []
            start = 1
            max_retries = 3
            
            while len(results) < num_results and start <= 100:  # Google Custom Search max 100 results
                for attempt in range(max_retries):
                    try:
                        # Prepare request parameters
                        params = {
                            'q': search_query,
                            'key': self.api_key,
                            'cx': self.cse_id,
                            'num': min(10, num_results - len(results)),  # Max 10 per request
                            'start': start,
                            'lr': 'lang_en',  # English results only
                            'cr': 'countryUS',  # US results
                            'gl': 'us'  # US region
                        }
                        
                        # Make API request with timeout
                        response = requests.get(
                            self.base_url,
                            params=params,
                            timeout=15
                        )
                        
                        # Check for rate limiting (429) or server errors (5xx)
                        if response.status_code == 429:
                            retry_after = int(response.headers.get('Retry-After', 60))
                            logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                            time.sleep(retry_after)
                            continue
                            
                        response.raise_for_status()
                        data = response.json()
                        
                        # Process results
                        if 'items' in data:
                            for item in data.get('items', []):
                                result = {
                                    'title': item.get('title', ''),
                                    'link': item.get('link', ''),
                                    'snippet': item.get('snippet', ''),
                                    'source': 'google_search',
                                    'query': query,
                                    'search_timestamp': datetime.utcnow(),
                                    'domain': urlparse(item.get('link', '')).netloc
                                }
                                
                                # Analyze content (sentiment, PII, etc.)
                                self._analyze_result(result)
                                
                                results.append(result)
                                
                                if len(results) >= num_results:
                                    break
                        
                        # Check for more results
                        if 'queries' in data and 'nextPage' in data['queries']:
                            start += 10
                        else:
                            start = 101  # Break outer loop
                            
                        break  # Success, exit retry loop
                        
                    except requests.exceptions.RequestException as e:
                        if attempt == max_retries - 1:  # Last attempt
                            logger.error(f"Request failed after {max_retries} attempts: {e}")
                            raise
                        wait_time = (2 ** attempt) + (random.random() * 0.5)  # Exponential backoff with jitter
                        time.sleep(wait_time)
                
            return results
            
        except Exception as e:
            logger.error(f"Error in Google search: {e}", exc_info=True)
            return []

    def _analyze_result(self, result: Dict) -> None:
        """Analyze search result content
        
        Args:
            result: Dictionary containing search result data
        """
        try:
            if not self.nlp:
                raise RuntimeError("NLP processor not initialized")
                
            # Combine title and snippet for analysis
            text = f"{result.get('title', '')} {result.get('snippet', '')}"
            if not text.strip():
                raise ValueError("No text content to analyze")
            
            # Sentiment analysis
            sentiment = self.nlp.analyze_sentiment(text)
            result['sentiment'] = sentiment
            
            # PII detection
            pii = self.nlp.detect_pii(text)
            result['pii_detected'] = any(pii.values())
            result['pii_details'] = pii
            
            # Calculate risk score (0-100) based on sentiment and PII
            risk_score = 0
            
            # Sentiment contributes up to 70% to risk score
            if sentiment['compound'] < -0.2:  # Negative sentiment
                risk_score += 70 * (1 + sentiment['compound'])  # Scale by how negative
            
            # PII detection adds up to 30% to risk score
            if result['pii_detected']:
                risk_score += 30
            
            result['risk_score'] = min(100, max(0, int(risk_score)))  # Ensure 0-100 range
            
            # Extract keywords
            keywords = self.nlp.extract_keywords(text, top_n=5)
            result['keywords'] = [k[0] for k in keywords] if keywords else []
            
            # Categorize the result
            result['category'] = self._categorize_result(result)
            
            # Add analysis timestamp
            result['analyzed_at'] = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error analyzing search result: {e}", exc_info=True)
            # Set default values on error
            result.update({
                'sentiment': {"positive": 0.0, "neutral": 1.0, "negative": 0.0, "compound": 0.0},
                'pii_detected': False,
                'pii_details': {},
                'risk_score': 0,
                'keywords': [],
                'category': 'unknown',
                'analysis_error': str(e)
            })

    def _categorize_result(self, result: Dict) -> str:
        """Categorize search result based on content and domain
        
        Args:
            result: Search result dictionary
            
        Returns:
            str: Category name
        """
        # Check domain patterns
        domain = result.get('domain', '').lower()
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        
        # News sites
        news_domains = ['reuters.com', 'bloomberg.com', 'cnbc.com', 'wsj.com', 'ft.com']
        if any(nd in domain for nd in news_domains):
            return 'news'
        
        # Social media
        social_domains = ['twitter.com', 'facebook.com', 'linkedin.com', 'reddit.com']
        if any(sd in domain for sd in social_domains):
            return 'social_media'
        
        # Forums and Q&A
        forum_domains = ['quora.com', 'stackexchange.com', 'reddit.com']
        if any(fd in domain for fd in forum_domains):
            return 'forum'
        
        # Job sites
        job_terms = ['career', 'job', 'hiring', 'recruit']
        if any(jt in domain or jt in title for jt in job_terms):
            return 'jobs'
        
        # Reviews
        review_terms = ['review', 'complaint', 'scam', 'rating']
        if any(rt in title or rt in snippet for rt in review_terms):
            return 'reviews'
        
        # Company website
        if self.brand_name and self.brand_name.lower() in domain:
            return 'official'
        
        return 'other'