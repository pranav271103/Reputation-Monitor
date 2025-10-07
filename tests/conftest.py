"""Test configuration and fixtures for pytest."""
import pytest
from unittest.mock import MagicMock, patch
import os
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    env_vars = {
        "TWITTER_BEARER_TOKEN": "test_twitter_token",
        "REDDIT_CLIENT_ID": "test_reddit_id",
        "REDDIT_CLIENT_SECRET": "test_reddit_secret",
        "REDDIT_USER_AGENT": "test_user_agent",
        "GOOGLE_API_KEY": "test_google_key",
        "GOOGLE_CSE_ID": "test_cse_id"
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars

@pytest.fixture
def mock_twitter_response():
    """Mock Twitter API response."""
    return {
        "data": [
            {
                "id": "123",
                "text": "Test tweet about Reputation Monitor",
                "created_at": "2023-10-07T00:00:00Z",
                "public_metrics": {"retweet_count": 5, "like_count": 10},
                "author_id": "456"
            }
        ],
        "includes": {
            "users": [
                {
                    "id": "456",
                    "username": "testuser",
                    "name": "Test User"
                }
            ]
        }
    }

@pytest.fixture
def mock_reddit_response():
    """Mock Reddit API response."""
    mock_submission = MagicMock()
    mock_submission.id = "test123"
    mock_submission.title = "Test Reddit Post"
    mock_submission.selftext = "This is a test post about Reputation Monitor"
    mock_submission.score = 10
    mock_submission.created_utc = 1672531200  # 2023-01-01
    mock_submission.url = "https://reddit.com/r/test/comments/test123"
    mock_submission.subreddit.display_name = "test"
    mock_submission.author.name = "testuser"
    return [mock_submission]
