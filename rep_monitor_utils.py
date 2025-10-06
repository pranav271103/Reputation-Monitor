"""
🔬 Advanced NLP Pipeline for Reputation Monitoring
Enhanced sentiment analysis and keyword extraction utilities
"""

import re
import logging
from collections import Counter
from typing import List, Dict, Any
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import textblob
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)
    
try:
    nltk.data.find('punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
    
try:
    nltk.data.find('stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
    
try:
    nltk.data.find('wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

class NLPPipeline:
    """🚀 Advanced NLP Pipeline with Multiple Sentiment Models"""
    
    def __init__(self):
        """Initialize the NLP pipeline with multiple analyzers"""
        try:
            self.vader = SentimentIntensityAnalyzer()
            self.lemmatizer = WordNetLemmatizer()
            self.stop_words = set(stopwords.words('english'))
            
            # Extended stop words for social media
            self.stop_words.update([
                'rt', 'via', 'amp', 'http', 'https', 'www', 'com', 'org', 'net',
                'said', 'says', 'like', 'get', 'got', 'go', 'going', 'gone',
                'new', 'one', 'two', 'first', 'last', 'next', 'back', 'way',
                'time', 'year', 'day', 'week', 'month', 'today', 'now', 'just'
            ])
            
            logger.info("✅ NLP Pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing NLP Pipeline: {e}")
            raise
    
    def preprocess_text(self, text: str) -> str:
        """🧹 Advanced text preprocessing"""
        if not text or not isinstance(text, str):
            return ""
            
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove mentions and hashtags but keep the text
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#(\w+)', r'\1', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove non-ASCII characters
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        
        return text.lower()
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """🎭 Multi-model sentiment analysis with confidence scoring"""
        if not text:
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'scores': {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
            }
        
        try:
            # Preprocess text
            clean_text = self.preprocess_text(text)
            
            # VADER Analysis
            vader_scores = self.vader.polarity_scores(clean_text)
            
            # TextBlob Analysis  
            blob = textblob.TextBlob(clean_text)
            blob_sentiment = blob.sentiment.polarity
            
            # Combine results with weighted average
            vader_compound = vader_scores['compound']
            
            # Enhanced sentiment classification
            if vader_compound >= 0.1 and blob_sentiment > 0:
                sentiment = 'positive' 
                confidence = min(abs(vader_compound), abs(blob_sentiment))
            elif vader_compound <= -0.1 and blob_sentiment < 0:
                sentiment = 'negative'
                confidence = min(abs(vader_compound), abs(blob_sentiment))
            else:
                sentiment = 'neutral'
                confidence = 1.0 - max(abs(vader_compound), abs(blob_sentiment))
            
            return {
                'sentiment': sentiment,
                'confidence': round(confidence, 3),
                'scores': {
                    'positive': round(vader_scores['pos'], 3),
                    'negative': round(vader_scores['neg'], 3), 
                    'neutral': round(vader_scores['neu'], 3)
                },
                'vader_compound': round(vader_compound, 3),
                'textblob_polarity': round(blob_sentiment, 3)
            }
            
        except Exception as e:
            logger.error(f"❌ Sentiment analysis error: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'scores': {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
            }
    
    def extract_keywords(self, text: str, max_keywords: int = 15) -> List[str]:
        """🔤 Advanced keyword extraction using TF-IDF"""
        if not text:
            return []
            
        try:
            # Preprocess text
            clean_text = self.preprocess_text(text)
            
            # Tokenize and filter
            tokens = word_tokenize(clean_text)
            
            # Remove stopwords and short words
            filtered_tokens = [
                self.lemmatizer.lemmatize(token) 
                for token in tokens 
                if (token.isalpha() and 
                    len(token) > 2 and 
                    token not in self.stop_words)
            ]
            
            if len(filtered_tokens) < 2:
                return []
            
            # Use TF-IDF for better keyword extraction
            try:
                tfidf = TfidfVectorizer(
                    max_features=max_keywords * 2,
                    ngram_range=(1, 2),
                    stop_words='english'
                )
                
                # Reconstruct text for TF-IDF
                processed_text = ' '.join(filtered_tokens)
                tfidf_matrix = tfidf.fit_transform([processed_text])
                
                # Get feature names and scores
                feature_names = tfidf.get_feature_names_out()
                scores = tfidf_matrix.toarray()[0]
                
                # Sort by TF-IDF score
                keyword_scores = list(zip(feature_names, scores))
                keyword_scores.sort(key=lambda x: x[1], reverse=True)
                
                # Extract top keywords
                keywords = [kw[0] for kw in keyword_scores[:max_keywords] if kw[1] > 0]
                
            except Exception:
                # Fallback to frequency-based extraction
                word_freq = Counter(filtered_tokens)
                keywords = [word for word, freq in word_freq.most_common(max_keywords)]
            
            return keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"❌ Keyword extraction error: {e}")
            return []
    
    def analyze_emotion(self, text: str) -> Dict[str, float]:
        """😊 Enhanced emotion analysis"""
        if not text:
            return {'joy': 0.0, 'anger': 0.0, 'fear': 0.0, 'sadness': 0.0}
            
        try:
            # Simple emotion keywords mapping
            emotion_keywords = {
                'joy': ['happy', 'joy', 'excited', 'pleased', 'delighted', 'thrilled', 'amazing', 'awesome', 'fantastic', 'great', 'excellent', 'wonderful', 'brilliant', 'perfect', 'love', 'loved'],
                'anger': ['angry', 'mad', 'furious', 'annoyed', 'irritated', 'hate', 'disgusted', 'outraged', 'frustrated', 'terrible', 'awful', 'horrible', 'worst', 'disgusting', 'pathetic'],
                'fear': ['scared', 'afraid', 'worried', 'anxious', 'nervous', 'terrified', 'frightened', 'concerned', 'panic', 'stress', 'danger', 'risk', 'threat', 'warning'],
                'sadness': ['sad', 'depressed', 'disappointed', 'unhappy', 'miserable', 'devastated', 'heartbroken', 'grief', 'sorrow', 'regret', 'loss', 'tragedy', 'unfortunate']
            }
            
            clean_text = self.preprocess_text(text)
            tokens = word_tokenize(clean_text)
            
            emotion_scores = {}
            total_tokens = len(tokens)
            
            for emotion, keywords in emotion_keywords.items():
                score = sum(1 for token in tokens if token in keywords)
                emotion_scores[emotion] = round(score / max(total_tokens, 1), 3)
            
            return emotion_scores
            
        except Exception as e:
            logger.error(f"❌ Emotion analysis error: {e}")
            return {'joy': 0.0, 'anger': 0.0, 'fear': 0.0, 'sadness': 0.0}
    
    def get_text_stats(self, text: str) -> Dict[str, Any]:
        """📊 Comprehensive text statistics"""
        if not text:
            return {
                'word_count': 0,
                'char_count': 0,
                'sentence_count': 0,
                'avg_word_length': 0.0,
                'readability_score': 0.0
            }
            
        try:
            # Basic counts
            words = text.split()
            word_count = len(words)
            char_count = len(text)
            sentence_count = len(re.split(r'[.!?]+', text))
            
            # Average word length
            avg_word_length = sum(len(word) for word in words) / max(word_count, 1)
            
            # Simple readability score (Flesch-like)
            avg_sentence_length = word_count / max(sentence_count, 1)
            readability_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length)
            
            return {
                'word_count': word_count,
                'char_count': char_count,
                'sentence_count': sentence_count,
                'avg_word_length': round(avg_word_length, 2),
                'readability_score': round(max(0, min(100, readability_score)), 1)
            }
            
        except Exception as e:
            logger.error(f"❌ Text stats error: {e}")
            return {
                'word_count': 0,
                'char_count': 0,
                'sentence_count': 0,
                'avg_word_length': 0.0,
                'readability_score': 0.0
            }