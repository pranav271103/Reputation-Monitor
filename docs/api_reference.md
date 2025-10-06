# API Reference

This document provides detailed information about the Reputation Monitor API.

## Base URL

```
https://api.reputationmonitor.com/v1
```

## Authentication

All API requests require authentication using an API key.

### Header

```
Authorization: Bearer YOUR_API_KEY
```

## Rate Limiting

- **Rate Limit**: 100 requests per minute per API key
- **Response Headers**:
  - `X-RateLimit-Limit`: Request limit per minute
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets (UTC epoch seconds)

## Endpoints

### 1. Mentions

#### Get All Mentions

```http
GET /mentions
```

**Query Parameters:**
- `query` (string): Search query
- `start_date` (string): ISO 8601 date
- `end_date` (string): ISO 8601 date
- `source` (string): twitter, reddit, web
- `sentiment` (string): positive, negative, neutral
- `limit` (integer): Number of results (default: 20, max: 100)
- `offset` (integer): Pagination offset (default: 0)

**Response:**
```json
{
  "data": [
    {
      "id": "123",
      "source": "twitter",
      "content": "Loving the new update!",
      "author": "@user123",
      "url": "https://twitter.com/user/status/123",
      "sentiment": "positive",
      "sentiment_score": 0.85,
      "created_at": "2023-01-01T12:00:00Z",
      "metrics": {
        "likes": 10,
        "shares": 5,
        "comments": 2
      }
    }
  ],
  "pagination": {
    "total": 100,
    "limit": 20,
    "offset": 0
  }
}
```

### 2. Sentiment Analysis

#### Analyze Text

```http
POST /analyze/sentiment
```

**Request Body:**
```json
{
  "text": "I really love this product! It's amazing.",
  "language": "en"
}
```

**Response:**
```json
{
  "sentiment": "positive",
  "confidence": 0.92,
  "scores": {
    "positive": 0.92,
    "neutral": 0.06,
    "negative": 0.02
  },
  "key_phrases": ["love", "amazing product"]
}
```

### 3. Alerts

#### Create Alert

```http
POST /alerts
```

**Request Body:**
```json
{
  "name": "Negative Mentions",
  "query": "brand_name sentiment:negative",
  "channels": ["email", "webhook"],
  "recipients": ["team@example.com"],
  "webhook_url": "https://your-webhook-url.com/alert"
}
```

**Response:**
```json
{
  "id": "alert_123",
  "status": "active",
  "created_at": "2023-01-01T12:00:00Z"
}
```

## Webhooks

### Payload Format

```json
{
  "event": "new_mention",
  "data": {
    "id": "123",
    "source": "twitter",
    "content": "Having issues with the service",
    "sentiment": "negative",
    "url": "https://twitter.com/user/status/123"
  },
  "triggered_at": "2023-01-01T12:00:00Z"
}
```

### Event Types

- `new_mention`: New mention detected
- `sentiment_change`: Significant sentiment change
- `volume_spike`: Unusual increase in mentions
- `alert_triggered`: Custom alert triggered

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "invalid_request",
    "message": "The request is missing a required parameter",
    "details": {
      "param": "query"
    }
  }
}
```

### Common Error Codes

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | invalid_request | Invalid request parameters |
| 401 | unauthorized | Invalid or missing API key |
| 403 | forbidden | Insufficient permissions |
| 404 | not_found | Resource not found |
| 429 | rate_limit_exceeded | Rate limit exceeded |
| 500 | server_error | Internal server error |

## SDKs

### Python

```python
from reputation_monitor import Client

client = Client(api_key="your_api_key")

# Get mentions
mentions = client.mentions.list(
    query="brand_name",
    start_date="2023-01-01",
    sentiment="positive"
)

# Analyze sentiment
result = client.analyze.sentiment(
    text="I love this product!"
)
```

### JavaScript

```javascript
const { Client } = require('reputation-monitor-sdk');

const client = new Client('your_api_key');

// Get mentions
const mentions = await client.mentions.list({
  query: 'brand_name',
  startDate: '2023-01-01',
  sentiment: 'positive'
});
```

## Changelog

### v1.0.0 (2023-10-01)
- Initial API release
- Basic mention tracking
- Sentiment analysis
- Alerting system
