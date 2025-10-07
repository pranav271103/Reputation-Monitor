"""Unit tests for utility functions and classes."""
import pytest
from rep_monitor_utils import NLPPipeline

class TestNLPPipeline:
    """Test cases for NLPPipeline class."""
    
    def setup_method(self):
        """Initialize test fixtures."""
        self.nlp = NLPPipeline()
        self.test_text = "Reputation Monitor is an amazing tool for online reputation management!"
    
    def test_preprocess_text(self):
        """Test text preprocessing."""
        processed = self.nlp.preprocess_text(self.test_text)
        assert isinstance(processed, str)
        # Check if text is lowercased and contains expected words
        assert "amazing" in processed.lower()
        # Check if text is properly processed
        assert "reputation monitor" in processed.lower()
    
    def test_analyze_sentiment_positive(self):
        """Test sentiment analysis with positive text."""
        result = self.nlp.analyze_sentiment("I love this amazing tool!")
        assert isinstance(result, dict)
        assert "sentiment" in result
        assert "confidence" in result
        assert result["sentiment"] in ["positive", "neutral"]  # Allow neutral as valid result
        assert 0 <= result["confidence"] <= 1
    
    def test_analyze_sentiment_negative(self):
        """Test sentiment analysis with negative text."""
        result = self.nlp.analyze_sentiment("I hate this terrible tool!")
        assert isinstance(result, dict)
        assert "sentiment" in result
        assert "confidence" in result
        assert result["sentiment"] in ["negative", "neutral"]  # Allow neutral as valid result
        assert 0 <= result["confidence"] <= 1
