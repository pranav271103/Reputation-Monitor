# Getting Started

This guide will help you set up and configure the Reputation Monitor system.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- API keys for the services you want to monitor (Twitter, Reddit, Google Custom Search)
- (Optional) OpenAI API key for enhanced analysis

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/pranav271103/Reputation-Monitor.git
cd Reputation-Monitor
```

### 2. Create and Activate Virtual Environment (Recommended)

#### Windows
```bash
python -m venv venv
.\venv\Scripts\activate
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root and add your API keys:

```env
# Twitter API (Required for Twitter monitoring)
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Reddit API (Required for Reddit monitoring)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_user_agent

# Google Custom Search API
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id

# Optional: OpenAI API for enhanced analysis
OPENAI_API_KEY=your_openai_api_key
```

### 2. Configure Data Storage

By default, the application stores data in a local SQLite database. For production use, you can configure a different database by setting the `DATABASE_URL` environment variable:

```env
DATABASE_URL=postgresql://user:password@localhost/reputation_monitor
```

## First Run

1. Start the application:

```bash
streamlit run reputation_monitor.py
```

2. Open your web browser and navigate to:
   ```
   http://localhost:8501
   ```

3. You should see the Reputation Monitor dashboard. Start by configuring your first monitoring job in the sidebar.

## Next Steps

- Learn how to [configure monitoring jobs](user_guide.md#monitoring-setup)
- Check out the [API documentation](api_reference.md) for integration options
- Read the [developer guide](developer_guide.md) for advanced configuration
