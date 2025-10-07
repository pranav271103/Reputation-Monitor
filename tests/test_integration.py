"""Integration tests for the application."""
import pytest
from unittest.mock import patch, MagicMock, ANY
from datetime import datetime, timedelta, timezone
import pandas as pd
from reputation_monitor import fetch_twitter_safe, fetch_reddit_safe, fetch_all

class TestIntegration:
    """Integration test cases."""
    
    @patch('tweepy.Client')
    def test_twitter_integration(self, mock_tweepy, mock_env_vars, mock_twitter_response):
        """Test Twitter API integration."""
        # Setup mock
        mock_client = MagicMock()
        mock_tweepy.return_value = mock_client
        mock_client.search_recent_tweets.return_value = mock_twitter_response
        
        # Convert string date to datetime for the test
        since_date = datetime(2023, 10, 1, tzinfo=timezone.utc)
        
        try:
            # Test the function
            results = fetch_twitter_safe("test", since=since_date, limit=5)
            
            # Assertions
            assert isinstance(results, (list, pd.DataFrame))
            if hasattr(results, 'shape'):  # If it's a DataFrame
                assert not results.empty
            elif results:  # If it's a list
                assert isinstance(results[0], dict)
                assert "text" in results[0]
        except Exception as e:
            pytest.fail(f"fetch_twitter_safe raised an exception: {e}")
        
        # Verify the API was called with expected arguments
        mock_client.search_recent_tweets.assert_called_once()
    
    @patch('praw.Reddit')
    def test_reddit_integration(self, mock_praw, mock_env_vars, mock_reddit_response):
        """Test Reddit API integration."""
        # Setup mock
        mock_reddit = MagicMock()
        mock_praw.return_value = mock_reddit
        
        # Create a mock submission
        mock_submission = MagicMock()
        mock_submission.title = "Test Reddit Post"
        mock_submission.selftext = "This is a test post"
        mock_submission.created_utc = 1672531200
        mock_submission.url = "https://reddit.com/r/test/comments/123"
        mock_submission.id = "123"
        mock_submission.subreddit.display_name = "test"
        mock_submission.author = MagicMock()
        mock_submission.author.name = "testuser"
        
        mock_reddit.subreddit.return_value.search.return_value = [mock_submission]
        
        try:
            # Test the function with a datetime object
            since_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
            results = fetch_reddit_safe("test", since=since_date.timestamp(), limit=5)
            
            # Assertions
            assert isinstance(results, (list, pd.DataFrame))
            if hasattr(results, 'shape'):  # If it's a DataFrame
                assert not results.empty
            elif results:  # If it's a list
                assert isinstance(results[0], dict)
                assert "title" in results[0] or "selftext" in results[0]
        except Exception as e:
            pytest.fail(f"fetch_reddit_safe raised an exception: {e}")
        
        # Verify the API was called
        mock_reddit.subreddit.return_value.search.assert_called_once()
    
    @patch('reputation_monitor.fetch_twitter_safe')
    @patch('reputation_monitor.fetch_reddit_safe')
    def test_fetch_all_integration(self, mock_reddit, mock_twitter):
        """Test the complete data fetching pipeline."""
        # Setup mocks to return DataFrames
        mock_twitter.return_value = pd.DataFrame([{"text": "Test tweet", "created_at": "2023-10-07T00:00:00Z"}])
        mock_reddit.return_value = pd.DataFrame([{"title": "Test post", "created_utc": 1672531200}])
        
        try:
            # Test the function
            results = fetch_all("test", days=7, limit=5)
            
            # Assertions - check if results is a DataFrame
            assert isinstance(results, pd.DataFrame)
            assert not results.empty
            
            # Verify both mocks were called
            mock_twitter.assert_called_once()
            mock_reddit.assert_called_once()
            
        except Exception as e:
            pytest.fail(f"fetch_all raised an exception: {e}")
