"""Reporting module for handling user reports on posts."""
import json
import os
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional

class ReportManager:
    def __init__(self, storage_file: str = "reports.json"):
        self.storage_file = storage_file
        self.reports = self._load_reports()
    
    def _load_reports(self) -> Dict[str, List[Dict]]:
        if not os.path.exists(self.storage_file):
            return {"reports": []}
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"reports": []}
    
    def _save_reports(self) -> None:
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.reports, f, indent=2, ensure_ascii=False)
    
    def report_post(
        self, 
        post_id: str, 
        platform: str, 
        reason: str, 
        reported_by: str = "anonymous",
        additional_info: Optional[Dict] = None
    ) -> Dict:
        report = {
            "report_id": f"{platform}_{post_id}_{int(datetime.utcnow().timestamp())}",
            "post_id": post_id,
            "platform": platform,
            "reason": reason,
            "reported_by": reported_by,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending",
            "additional_info": additional_info or {}
        }
        
        self.reports["reports"].append(report)
        self._save_reports()
        
        return {"status": "success", "report_id": report["report_id"]}

def report_post_ui(post_data: Dict, report_manager: Optional[ReportManager] = None) -> None:
    """Streamlit UI for reporting a post."""
    if report_manager is None:
        report_manager = ReportManager()
    
    # Display post preview in a clean card
    with st.container():
        st.markdown("### 📝 Post Being Reported")
        st.markdown(f"**Platform:** {post_data.get('platform', 'unknown').title()}")
        
        # Display post content in a scrollable container
        if 'text' in post_data:
            st.markdown("**Content Preview:**")
            st.markdown(
                f'<div style="border-left: 4px solid #ddd; padding: 10px; margin: 10px 0; max-height: 150px; overflow-y: auto;">'
                f'{post_data["text"][:500]}{"..." if len(post_data["text"]) > 500 else ""}'
                '</div>',
                unsafe_allow_html=True
            )
        
        if 'url' in post_data and post_data['url']:
            st.markdown(f"**Link:** [{post_data['url'][:50]}...]({post_data['url']})")
    
    # Reason selection
    st.markdown("---")
    st.markdown("### 🎯 Reason for Reporting")
    
    # Use a selectbox for better mobile experience
    selected_reason = st.selectbox(
        "Select a reason:",
        [
            "Spam or misleading",
            "Harassment or bullying",
            "Hate speech or offensive content",
            "False information",
            "Other (please specify)"
        ],
        key=f"reason_{post_data.get('id', '')}"
    )
    
    # Custom reason if "Other" is selected
    custom_reason = ""
    if selected_reason == "Other (please specify)":
        custom_reason = st.text_input(
            "Please specify the reason:",
            key=f"custom_reason_{post_data.get('id', '')}",
            placeholder="Please describe the issue..."
        )
    
    # Additional notes
    notes = st.text_area(
        "Additional details (optional):", 
        key=f"notes_{post_data.get('id', '')}",
        placeholder="Provide any additional information that might be helpful..."
    )
    
    # Action buttons in a single row
    col1, col2 = st.columns([1, 1])
    
    with col1:
        submit_clicked = st.button("✅ Submit Report", 
                                 type="primary", 
                                 key=f"submit_{post_data.get('id', '')}",
                                 use_container_width=True)
    
    with col2:
        if st.button("❌ Cancel", 
                    key=f"cancel_{post_data.get('id', '')}",
                    use_container_width=True):
            if 'reporting_post' in st.session_state:
                del st.session_state['reporting_post']
            st.rerun()
    
    # Handle form submission
    if submit_clicked:
        if selected_reason == "Other (please specify)" and not custom_reason.strip():
            st.error("Please specify a reason for reporting.")
        else:
            # Determine the final reason
            reason = custom_reason if selected_reason == "Other (please specify)" else selected_reason
            
            # Submit the report
            result = report_manager.report_post(
                post_id=post_data.get("id", ""),
                platform=post_data.get("platform", "unknown").lower(),
                reason=reason,
                additional_info={
                    "notes": notes,
                    "content_preview": post_data.get("text", "")[:500],
                    "url": post_data.get("url", "")
                }
            )
            
            if result["status"] == "success":
                st.success("✅ Report submitted successfully!")
                if 'reporting_post' in st.session_state:
                    del st.session_state['reporting_post']
                st.rerun()
            else:
                st.error("❌ Failed to submit report. Please try again.")
