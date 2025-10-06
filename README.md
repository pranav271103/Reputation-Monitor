<div align="center">
  <img src="https://raw.githubusercontent.com/pranav271103/Reputation-Monitor/main/assets/unnamed-removebg-preview.png" alt="Reputation Monitor Logo" width="200"/>
  <h1>Reputation Monitor</h1>
  
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
  [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
  [![Documentation](https://github.com/pranav271103/Reputation-Monitor/actions/workflows/gh-pages.yml/badge.svg)](https://github.com/pranav271103/Reputation-Monitor/actions/workflows/gh-pages.yml)
  [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

## Overview

Advanced Reputation Monitor is a powerful tool that tracks and analyzes online mentions across multiple platforms including Twitter, Reddit, and web search results. It provides comprehensive sentiment analysis, confidence scoring, and interactive visualizations to help you monitor your brand's online reputation.

## Key Features

- **Multi-Platform Monitoring**
  - Twitter mentions and hashtags
  - Reddit discussions and comments
  - Web search results

- **Advanced Sentiment Analysis**
  - Real-time sentiment classification (Positive/Negative/Neutral)
  - Confidence scoring for each analysis
  - Multi-model analysis combining VADER and TextBlob

- **Interactive Dashboard**
  - Sentiment distribution charts
  - Source breakdown visualization
  - Timeline analysis of mentions
  - Top keywords extraction

- **Data Export**
  - Export results to CSV for further analysis
  - Copy direct links to mentions

## Technologies

### Core
- Python 3.8+
- Streamlit (Web Interface)
- Pandas (Data Manipulation)
- Plotly (Interactive Visualizations)

### APIs & Services
- Twitter API (via Tweepy)
- Reddit API (via PRAW)
- Google Custom Search API
- (Optional) OpenAI API for enhanced analysis

### NLP & Machine Learning
- NLTK (Natural Language Toolkit)
- TextBlob (Sentiment Analysis)
- VADER (Valence Aware Dictionary and sEntiment Reasoner)
- scikit-learn (TF-IDF for keyword extraction)

### Frontend
- Streamlit (Web interface)
- Plotly (Interactive visualizations)
- Bootstrap (UI components)

### DevOps
- Docker (Containerization)
- GitHub Actions (CI/CD)
- Pytest (Testing)
- Black & Flake8 (Code formatting)

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- API keys for the services you want to use (Twitter, Reddit, Google Custom Search)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/pranav271103/Online-bad-reputation-.git
   cd Online-bad-reputation-
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your environment variables**:
   - Create a `.env` file in the project root
   - Add your API keys (see Configuration section below)

## ⚙️ Configuration

Create a `.env` file in the root directory with the following variables:

```env
# Twitter API (Required for Twitter monitoring)
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Reddit API (Required for Reddit monitoring)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_user_agent

# Google Custom Search API (Required for web search)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id

# OpenAI API (Optional, for enhanced analysis)
OPENAI_API_KEY=your_openai_api_key
```

## 🏃‍♂️ Usage

1. **Start the application**:
   ```bash
   streamlit run reputation_monitor.py
   ```

2. Open your web browser and navigate to `http://localhost:8501`

3. **In the sidebar**:
   - Enter the brand or person you want to monitor
   - Select the number of days to look back
   - Choose the maximum number of mentions to fetch
   - Select data sources (Twitter, Reddit, Web)

4. Click the "Search" button to start the analysis

5. Explore the results in the interactive dashboard

## 📊 Features in Detail

### Sentiment Analysis
- Real-time sentiment classification of mentions
- Confidence scores for each analysis
- Multi-model ensemble for improved accuracy

### Data Visualization
- Interactive sentiment distribution pie chart
- Source breakdown bar chart
- Timeline analysis of mentions
- Top keywords extraction

### Data Export
- Export results to CSV for further analysis
- Copy direct links to mentions

## 🔧 Troubleshooting

### Rate Limiting
- The application implements rate limiting to comply with API restrictions
- Twitter searches may take 1-2 minutes due to rate limits
- For faster results, reduce the number of days or maximum mentions

### API Errors
- Ensure all required API keys are correctly set in the `.env` file
- Check that your API keys have the necessary permissions
- Verify that your API keys haven't exceeded their rate limits

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing web framework
- [Tweepy](https://www.tweepy.org/) for Twitter API access
- [PRAW](https://praw.readthedocs.io/) for Reddit API access
- [NLTK](https://www.nltk.org/) and [TextBlob](https://textblob.readthedocs.io/) for NLP capabilities
