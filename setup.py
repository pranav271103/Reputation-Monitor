#!/usr/bin/env python3
"""
Setup script for Advanced Reputation Monitor
"""
import os
import subprocess
import sys
from setuptools import setup, find_packages
import nltk

def install_requirements():
    print("Installing Python packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Successfully installed all packages!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        return False
    return True

def download_nltk_data():
    print("Downloading NLTK data...")
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        nltk.download('omw-1.4', quiet=True)
        nltk.download('vader_lexicon', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        print("NLTK data downloaded successfully!")
    except Exception as e:
        print(f"Error downloading NLTK data: {e}")
        return False
    return True

def create_env_template():
    env_template = """# Twitter API Keys (Get from https://developer.twitter.com/)
TWITTER_BEARER_TOKEN=your_bearer_token_here

# Reddit API Keys (Get from https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=ReputationMonitor/1.0

# Google Custom Search API (Get from https://developers.google.com/custom-search/v1/overview)
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_custom_search_engine_id_here

# OpenAI API Key (Optional, for enhanced analysis)
OPENAI_API_KEY=your_openai_api_key_here
"""

    env_path = '.env'
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write(env_template)
        print(f"Created {env_path} template. Please update it with your API keys.")
    else:
        print(f"ℹ {env_path} already exists. Skipping creation.")

def main():
    print("Setting up Advanced Reputation Monitor...\n")
    
    # Install requirements
    if not install_requirements():
        print(" Setup failed while installing requirements.")
        sys.exit(1)
    
    # Download NLTK data
    if not download_nltk_data():
        print(" Setup completed with warnings (NLTK data not downloaded).")
    else:
        print("NLTK data setup completed successfully!")
    
    # Create .env template if it doesn't exist
    create_env_template()
    
    print("Next steps:")
    print("1. Edit the .env file and add your API keys")
    print("2. Run the app with: streamlit run reputation_monitor.py")
    print("Happy monitoring!")

if __name__ == "__main__":
    main()

# Package configuration
setup(
    name="reputation-monitor",
    version="1.0.0",
    description="Advanced Online Reputation Monitoring Tool with Sentiment Analysis",
    long_description=open("README.md", "r", encoding="utf-8").read() if os.path.exists("README.md") else "Advanced Online Reputation Monitoring Tool with Sentiment Analysis",
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/reputation-monitor",
    packages=find_packages(),
    install_requires=[
        'streamlit>=1.22.0',
        'pandas>=1.3.0',
        'plotly>=5.5.0',
        'tweepy>=4.10.0',
        'praw>=7.5.0',
        'python-dotenv>=0.19.0',
        'requests>=2.26.0',
        'beautifulsoup4>=4.10.0',
        'nltk>=3.6.0',
        'textblob>=0.17.1',
        'scikit-learn>=1.0.0',
        'google-api-python-client>=2.0.0'
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'reputation-monitor=reputation_monitor:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing :: Linguistic",
    ],
    keywords="reputation monitoring sentiment analysis social media monitoring brand monitoring",
    include_package_data=True,
)