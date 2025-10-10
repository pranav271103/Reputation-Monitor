"""Demo script for the reporting functionality."""
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reporting import report_post_ui, ReportManager

def main():
    # Example post data (this would come from your actual data source)
    example_post = {
        "id": "tweet_123456789",
        "platform": "twitter",
        "text": "This is an example tweet that might contain inappropriate content that needs to be reported.",
        "url": "https://twitter.com/user/status/123456789",
        "author": "example_user",
        "timestamp": "2023-10-10T10:30:00Z"
    }
    
    # Initialize the report manager
    report_manager = ReportManager("reports.json")
    
    # Show the reporting UI for the example post
    print("Testing Reporting Functionality")
    print("-" * 30)
    
    # Simulate a user reporting the post
    report_post_ui(example_post, report_manager)
    
    # Show a summary of reports
    print("\n" + "="*50)
    print("REPORTS SUMMARY")
    print("="*50)
    
    reports = report_manager.reports.get("reports", [])
    if not reports:
        print("No reports found.")
    else:
        print(f"Total reports: {len(reports)}")
        for i, report in enumerate(reports, 1):
            print(f"\nReport #{i}:")
            print(f"- ID: {report['report_id']}")
            print(f"- Post: {report['post_id']} on {report['platform']}")
            print(f"- Reason: {report['reason']}")
            print(f"- Status: {report['status']}")
            print(f"- Reported at: {report['timestamp']}")
    
    print("\nDemo complete. Reports saved to 'reports.json'")

if __name__ == "__main__":
    main()
