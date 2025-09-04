"""
NLP processing utilities for sentiment analysis and text processing.
"""
import re
import spacy
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict, List, Tuple, Optional
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import logging

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPProcessor:
    """Handles all NLP-related processing."""
    
    def __init__(self, model_name: str = 'textblob'):
        """Initialize the NLP processor.
        
        Args:
            model_name: The name of the sentiment analysis model to use.
                       Options: 'textblob', 'vader', or 'spacy'
        """
        self.model_name = model_name
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Initialize the selected model
        if model_name == 'spacy':
            try:
                self.nlp = spacy.load('en_core_web_sm')
            except OSError:
                logger.warning("spaCy model 'en_core_web_sm' not found. Falling back to TextBlob.")
                self.model_name = 'textblob'
        
        if model_name == 'vader':
            self.analyzer = SentimentIntensityAnalyzer()
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess the input text.
        
        Args:
            text: The input text to preprocess
            
        Returns:
            The preprocessed text
        """
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove mentions and hashtags
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                 if token not in self.stop_words and len(token) > 2]
        
        return ' '.join(tokens)
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze the sentiment of the given text.
        
        Args:
            text: The text to analyze
            
        Returns:
            A dictionary containing sentiment scores
        """
        if not text:
            return {"positive": 0.0, "neutral": 1.0, "negative": 0.0, "compound": 0.0}
        
        if self.model_name == 'vader':
            return self._analyze_with_vader(text)
        elif self.model_name == 'spacy':
            return self._analyze_with_spacy(text)
        else:  # Default to TextBlob
            return self._analyze_with_textblob(text)
    
    def _analyze_with_textblob(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using TextBlob."""
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        
        # Convert polarity to positive/neutral/negative
        if polarity > 0.1:
            return {"positive": 1.0, "neutral": 0.0, "negative": 0.0, "compound": polarity}
        elif polarity < -0.1:
            return {"positive": 0.0, "neutral": 0.0, "negative": 1.0, "compound": polarity}
        else:
            return {"positive": 0.0, "neutral": 1.0, "negative": 0.0, "compound": polarity}
    
    def _analyze_with_vader(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using VADER."""
        scores = self.analyzer.polarity_scores(text)
        
        # VADER returns 'pos', 'neu', 'neg', 'compound'
        return {
            "positive": scores['pos'],
            "neutral": scores['neu'],
            "negative": scores['neg'],
            "compound": scores['compound']
        }
    
    def _analyze_with_spacy(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using spaCy's text categorization."""
        doc = self.nlp(text)
        
        # This is a simplified example - in a real app, you'd train a custom text classifier
        # For now, we'll just return neutral sentiment
        return {"positive": 0.0, "neutral": 1.0, "negative": 0.0, "compound": 0.0}
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Extract top N keywords from the text.
        
        Args:
            text: The input text
            top_n: Number of keywords to extract
            
        Returns:
            List of (keyword, score) tuples, sorted by score in descending order
        """
        # Simple implementation using term frequency
        tokens = word_tokenize(text.lower())
        tokens = [t for t in tokens if t.isalpha() and t not in self.stop_words]
        
        # Count term frequencies
        freq_dist = nltk.FreqDist(tokens)
        
        # Get top N terms
        return freq_dist.most_common(top_n)
    
    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """Detect Personally Identifiable Information (PII) in the text.
        
        Args:
            text: The input text
            
        Returns:
            Dictionary mapping PII types to lists of detected values
        """
        pii = {
            "emails": [],
            "phone_numbers": [],
            "credit_cards": [],
            "ssn": []
        }
        
        # Email detection
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        pii["emails"] = re.findall(email_pattern, text)
        
        # Phone number detection (US format)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        pii["phone_numbers"] = re.findall(phone_pattern, text)
        
        # Credit card detection (simplified)
        cc_pattern = r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
        pii["credit_cards"] = re.findall(cc_pattern, text)
        
        # SSN detection (US format)
        ssn_pattern = r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b'
        pii["ssn"] = re.findall(ssn_pattern, text)
        
        return pii

# Global instance
nlp_processor = NLPProcessor()

def get_nlp_processor() -> NLPProcessor:
    """Get the global NLP processor instance."""
    return nlp_processor
