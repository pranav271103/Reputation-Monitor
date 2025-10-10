# Reporting Functionality

This module provides functionality for users to report inappropriate content from the reputation monitoring system.

## Features

- Report posts with different categories (spam, harassment, hate speech, etc.)
- Store reports in a JSON file
- Simple console-based reporting interface
- Basic report management

## Usage

### Basic Reporting

```python
from reporting import ReportManager, report_post_ui

# Initialize the report manager
report_manager = ReportManager("reports.json")

# Example post data (would come from your data source)
post_data = {
    "id": "tweet_123456789",
    "platform": "twitter",
    "text": "Content to be reported...",
    "url": "https://twitter.com/user/status/123456789"
}

# Show reporting UI
report_post_ui(post_data, report_manager)
```

### Managing Reports

```python
# Get all reports
reports = report_manager.reports.get("reports", [])

# Get reports by status
pending_reports = [r for r in reports if r["status"] == "pending"]

# Update a report status
report_manager.update_report_status(report_id="twitter_tweet123_1234567890", 
                                 status="reviewed", 
                                 notes="Reviewed by admin")
```

## Report Structure

Each report contains the following fields:

- `report_id`: Unique identifier for the report
- `post_id`: Original post ID
- `platform`: Source platform (e.g., 'twitter', 'reddit')
- `reason`: Reason for reporting
- `reported_by`: Username or 'anonymous'
- `timestamp`: When the report was created
- `status`: Current status (pending/reviewed/resolved/dismissed)
- `additional_info`: Additional metadata including notes and content preview

## Integration

To integrate with your existing code:

1. Import the reporting module
2. Initialize the ReportManager with a storage file path
3. Call `report_post_ui()` when a user wants to report a post
4. Use the ReportManager methods to manage reports

## Example

See `examples/reporting_demo.py` for a complete example.
