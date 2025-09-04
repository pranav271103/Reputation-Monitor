## Brand Reputation Monitoring System

<div align="center">
  <img src="Icon.ico" alt="Brand Reputation Monitor" width="120" />
  
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
  [![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
  [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
  [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
</div>

## Overview

A comprehensive brand reputation monitoring system that tracks and analyzes online mentions across multiple platforms. The system provides real-time insights, sentiment analysis, and risk assessment for brand mentions.

## Key Features

- **Multi-Platform Monitoring**
  - Web search integration
  - Social media tracking
  - News and forum mentions

- **Advanced Analytics**
  - Sentiment analysis
  - PII detection
  - Risk scoring
  - Trend analysis

- **Real-time Alerts**
  - Customizable thresholds
  - Dashboard widgets
  - Historical data tracking

- **Data Visualization**
  - Interactive charts
  - Sentiment trends
  - Source distribution

## Technologies

### Backend
- Python 3.8+
- FastAPI (REST API)
- MongoDB (Database)
- Pydantic (Data validation)
- Motor (Async MongoDB driver)

### NLP & AI
- spaCy (NLP processing)
- NLTK (Text processing)
- TextBlob (Sentiment analysis)
- VADER (Sentiment analysis)

### Frontend
- Streamlit (Web interface)
- Plotly (Interactive visualizations)
- Bootstrap (UI components)

### DevOps
- Docker (Containerization)
- GitHub Actions (CI/CD)
- Pytest (Testing)
- Black & Flake8 (Code formatting)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- MongoDB 4.4 or higher
- Google Custom Search API key
- Twitter API v2 Bearer Token

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/pranav271103/Online-bad-reputation-.git
   cd Online-bad-reputation-
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Initialize the database**
   ```bash
   python -m database
   ```

## Usage

### Running the Dashboard
```bash
streamlit run dashboard.py
```

### Running the API Server
```bash
uvicorn api:app --reload
```

## Data Model

### Collections
- **mentions**: Stores all brand mentions with metadata
- **users**: User accounts and preferences
- **alerts**: Configured alert rules
- **analytics**: Aggregated analytics data

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Project Link: [https://github.com/pranav271103/Online-bad-reputation-](https://github.com/pranav271103/Online-bad-reputation-)

## Acknowledgments

- [Font Awesome](https://fontawesome.com/) for icons
- [Shields.io](https://shields.io/) for badges
- [Streamlit](https://streamlit.io/) for the awesome dashboard framework
