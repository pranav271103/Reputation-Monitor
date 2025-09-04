import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import re
from urllib.parse import urlparse
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import json
import time
from typing import List, Dict, Any, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import local modules
from database import MongoDBManager
from nlp_processor import NLPProcessor

# Initialize services
try:
    db = MongoDBManager()
    nlp = NLPProcessor()
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    st.error("Failed to initialize application services. Please check the logs.")
    st.stop()

# Set page config
st.set_page_config(
    page_title="Brand Reputation Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database functions are now handled by the MongoDBManager instance

def get_mentions(days: int = 30) -> List[Dict]:
    """Retrieve mentions from MongoDB for the specified number of days
    
    Args:
        days: Number of days of data to retrieve
        
    Returns:
        List of mention documents
    """
    try:
        if not db:
            st.error("Database connection not available")
            return []
            
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query database
        query = {
            "created_at": {"$gte": start_date, "$lte": end_date}
        }
        
        mentions = db.find_mentions(query)
        
        # Convert ObjectId to string for serialization
        for mention in mentions:
            if '_id' in mention:
                mention['_id'] = str(mention['_id'])
                
        return mentions
        
    except Exception as e:
        logger.error(f"Error retrieving mentions: {e}", exc_info=True)
        st.error(f"Error retrieving mentions: {e}")
        return []

def delete_mention(mention_id: str) -> bool:
    """Delete a mention from MongoDB
    
    Args:
        mention_id: ID of the mention to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        if not db:
            st.error("Database connection not available")
            return False
            
        result = db.delete_mention(mention_id)
        if result:
            logger.info(f"Deleted mention: {mention_id}")
        else:
            logger.warning(f"Failed to delete mention: {mention_id}")
            
        return result
        
    except Exception as e:
        logger.error(f"Error deleting mention {mention_id}: {e}", exc_info=True)
        st.error(f"Error deleting mention: {e}")
        return False

def clear_all_mentions() -> bool:
    """Clear all mentions from the database
    
    Returns:
        bool: True if operation was successful, False otherwise
    """
    try:
        if not db:
            st.error("Database connection not available")
            return False
            
        if st.button("Confirm Clear All Data"):
            result = db.clear_mentions()
            if result:
                st.success("Successfully cleared all mentions")
            return result
        return False
        
    except Exception as e:
        logger.error(f"Error clearing mentions: {e}", exc_info=True)
        st.error(f"Error clearing mentions: {e}")
        return False

def extract_domain(url):
    """Extract domain from URL"""
    try:
        domain = urlparse(url).netloc
        # Remove www. if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return url

def show_dashboard():
    """Main dashboard view"""
    st.title("🛡️ Privacy & Reputation Dashboard")
    st.caption("AI-powered monitoring and protection for your online presence")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Privacy Analysis", "Dark Web Scan", "Social Media", "Privacy Tools"])
    
    # Add clear buttons
    with st.sidebar.expander("⚠️ Delete Mentions"):
        # Delete specific mention
        st.write("Delete specific mention:")
        mention_to_delete = st.text_input("Enter title to delete", "")
        if mention_to_delete and st.button("🗑️ Delete This Mention"):
            success, message = delete_mention_by_title(mention_to_delete)
            if success:
                st.success(message)
                st.experimental_rerun()
            else:
                st.warning(message)
        
        # Clear all button
        st.write("---")
        st.write("Danger Zone:")
        if st.button("🚮 Clear ALL Mentions", help="WARNING: This will delete ALL mention history"):
            if clear_all_mentions():
                st.success("All mentions have been cleared!")
                st.experimental_rerun()
    
    # Sentiment filter
    sentiment_options = ["All", "positive", "neutral", "negative"]
    selected_sentiment = st.sidebar.selectbox("Sentiment:", sentiment_options)
    
    # Get data
    mentions = get_mentions(days)
    
    if not mentions:
        st.warning("No data found for the selected filters.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(mentions)
    
    # Apply filters
    df = df[df['riskScore'] >= min_risk]
    if selected_sentiment != "All":
        df = df[df['sentiment'] == selected_sentiment]
    
    # Display metrics with better formatting
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Mentions", len(df), 
                 help="Total number of mentions found in the selected period")
    
    with col2:
        avg_risk = df['riskScore'].mean()
        risk_color = "red" if avg_risk > 70 else "orange" if avg_risk > 40 else "green"
        st.metric("Avg Risk Score", 
                 f"{avg_risk:.1f}",
                 delta_color="off",
                 help="Average risk score (0-100) of all mentions")
    
    with col3:
        pii_count = df['piiDetected'].sum()
        st.metric("PII Detected", 
                 f"{pii_count}",
                 "⚠️ High Risk" if pii_count > 0 else "✅ All Clear",
                 help="Number of mentions containing Personally Identifiable Information")
    
    with col4:
        sentiment_dist = df['sentiment'].value_counts(normalize=True) * 100
        pos_pct = sentiment_dist.get('positive', 0)
        st.metric("Positive Sentiment", 
                 f"{pos_pct:.1f}%",
                 help="Percentage of mentions with positive sentiment")
    
    st.markdown("---")
    
    # Sentiment distribution with better visualization
    st.subheader("📈 Sentiment Analysis")
    
    # Sentiment over time
    try:
        df['date'] = pd.to_datetime(df['createdAt']).dt.date
        sentiment_over_time = df.groupby(['date', 'sentiment']).size().unstack(fill_value=0)
        
        fig_time = px.area(
            sentiment_over_time,
            title="Sentiment Trend Over Time",
            labels={'value': 'Number of Mentions', 'date': 'Date'},
            color_discrete_map={
                'positive': '#2ecc71',
                'neutral': '#3498db',
                'negative': '#e74c3c'
            }
        )
        fig_time.update_layout(
            hovermode='x unified',
            legend_title_text='Sentiment',
            xaxis_title='Date',
            yaxis_title='Number of Mentions'
        )
        st.plotly_chart(fig_time, use_container_width=True)
        
    except Exception as e:
        st.warning(f"Could not generate time series: {str(e)}")
    
    # Sentiment distribution pie chart
    col1, col2 = st.columns(2)
    
    with col1:
        sentiment_counts = df['sentiment'].value_counts().reset_index()
        sentiment_counts.columns = ['Sentiment', 'Count']
        
        fig_pie = px.pie(
            sentiment_counts, 
            values='Count', 
            names='Sentiment',
            color='Sentiment',
            color_discrete_map={
                'positive': '#2ecc71',
                'neutral': '#3498db',
                'negative': '#e74c3c'
            },
            hole=0.4,
            title="Overall Sentiment Distribution"
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label+value',
            hovertemplate='%{label}: %{value} (%{percent})<extra></extra>',
            textfont_size=14
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Risk score distribution
    with col2:
        fig_risk = px.histogram(
            df,
            x='riskScore',
            nbins=20,
            title="Risk Score Distribution",
            labels={'riskScore': 'Risk Score', 'count': 'Number of Mentions'},
            color_discrete_sequence=['#e74c3c']
        )
        fig_risk.update_layout(
            xaxis_title="Risk Score (0-100)",
            yaxis_title="Number of Mentions",
            showlegend=False,
            xaxis=dict(range=[0, 100])
        )
        # Add vertical lines for risk thresholds
        for threshold, color in [(40, 'orange'), (70, 'red')]:
            fig_risk.add_vline(
                x=threshold, 
                line_dash="dash", 
                line_color=color,
                opacity=0.5,
                annotation_text=f"{threshold}%"
            )
        st.plotly_chart(fig_risk, use_container_width=True)
    
    # Add source analysis section if source data is available
    if 'source' in df.columns:
        st.markdown("---")
        st.subheader("🌐 Source Analysis")
        
        # Top sources by mention count
        source_counts = df['source'].value_counts().reset_index()
        source_counts.columns = ['Source', 'Mentions']
        
        # Limit to top 10 sources for better visualization
        top_sources = source_counts.head(10)
        
        fig_sources = px.bar(
            top_sources,
            x='Source',
            y='Mentions',
            title='Top 10 Sources by Number of Mentions',
            color='Mentions',
            color_continuous_scale='Viridis'
        )
        fig_sources.update_layout(
            xaxis_title="Source",
            yaxis_title="Number of Mentions",
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_sources, use_container_width=True)
        
        # Sentiment by source
        try:
            source_sentiment = df.groupby(['source', 'sentiment']).size().unstack(fill_value=0)
            source_sentiment_pct = source_sentiment.div(source_sentiment.sum(axis=1), axis=0) * 100
            
            # Sort by total mentions
            source_sentiment['total'] = source_sentiment.sum(axis=1)
            source_sentiment = source_sentiment.sort_values('total', ascending=False).drop('total', axis=1)
            
            # Take top 10 sources
            top_sources_sentiment = source_sentiment.head(10)
            
            fig_source_sentiment = px.bar(
                top_sources_sentiment,
                title='Sentiment Distribution by Top Sources',
                labels={'value': 'Number of Mentions', 'source': 'Source'},
                color_discrete_map={
                    'positive': '#2ecc71',
                    'neutral': '#3498db',
                    'negative': '#e74c3c'
                }
            )
            
            fig_source_sentiment.update_layout(
                barmode='stack',
                xaxis_title="Source",
                yaxis_title="Number of Mentions",
                legend_title="Sentiment"
            )
            
            st.plotly_chart(fig_source_sentiment, use_container_width=True)
            
        except Exception as e:
            st.warning(f"Could not generate source sentiment analysis: {str(e)}")
    
    # Recent mentions section removed as requested
    df['source'] = df['link'].apply(extract_domain)
    
    # 1. Sentiment Trends Over Time
    st.subheader("📈 Sentiment Trends")
    
    # Group by date and sentiment
    sentiment_over_time = df.groupby(['date', 'sentiment']).size().unstack(fill_value=0)
    
    # Plot sentiment trends
    fig_trend = px.area(
        sentiment_over_time, 
        title="Sentiment Over Time",
        labels={'value': 'Number of Mentions', 'date': 'Date'},
        color_discrete_map={
            'positive': '#2ecc71',
            'neutral': '#3498db',
            'negative': '#e74c3c'
        }
    )
    fig_trend.update_layout(showlegend=True, legend_title='Sentiment')
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # 2. Source Analysis
    st.subheader("🌐 Top Sources")
    
    try:
        # Group by source and sentiment
        source_analysis = df.groupby(['source', 'sentiment']).size().unstack(fill_value=0)
        
        # Ensure we have all sentiment columns
        for sentiment in ['positive', 'neutral', 'negative']:
            if sentiment not in source_analysis.columns:
                source_analysis[sentiment] = 0
        
        # Get top 10 sources by total mentions
        source_analysis['total'] = source_analysis.sum(axis=1)
        top_sources = source_analysis.nlargest(10, 'total')
        
        # Create a horizontal stacked bar chart
        fig_sources = px.bar(
            top_sources.reset_index(),
            x=['negative', 'neutral', 'positive'],
            y='source',
            orientation='h',
            title="Top Sources by Sentiment",
            labels={'value': 'Number of Mentions', 'variable': 'Sentiment', 'source': 'Source'},
            color_discrete_map={
                'positive': '#2ecc71',
                'neutral': '#3498db',
                'negative': '#e74c3c'
            }
        )
        fig_sources.update_layout(barmode='stack')
        st.plotly_chart(fig_sources, use_container_width=True)
        
    except Exception as e:
        st.warning(f"Could not generate source analysis: {str(e)}")
        st.write("Sample data for debugging:")
        st.write(df[['source', 'sentiment']].head())
    
    # 3. Sentiment Distribution by Source
    st.subheader("Sentiment by Source")
    
    try:
        # Group by source and sentiment
        source_analysis = df.groupby(['source', 'sentiment']).size().unstack(fill_value=0)
        
        # Calculate percentages
        source_analysis_pct = source_analysis.div(source_analysis.sum(axis=1), axis=0) * 100
        
        # Create a horizontal stacked bar chart
        fig_source = px.bar(
            source_analysis,
            orientation='h',
            title='Sentiment Distribution by Source',
            labels={'value': 'Number of Mentions', 'source': 'Source'},
            color_discrete_map={
                'positive': '#2ecc71',
                'neutral': '#3498db',
                'negative': '#e74c3c'
            }
        )
        
        # Update layout for better readability
        fig_source.update_layout(
            barmode='stack',
            height=400,
            legend_title_text='Sentiment',
            xaxis_title='Number of Mentions',
            yaxis_title='Source',
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig_source, use_container_width=True)
        
        # Add a grouped bar chart for percentage view
        st.subheader("Sentiment Percentage by Source")
        
        # Create a new figure for percentage view
        fig_sentiment = go.Figure()
        
        # Add a bar for each sentiment
        for sentiment, color in [('positive', '#2ecc71'), ('neutral', '#3498db'), ('negative', '#e74c3c')]:
            if sentiment in source_analysis.columns:
                fig_sentiment.add_trace(go.Bar(
                    x=source_analysis_pct.index,
                    y=source_analysis_pct[sentiment],
                    name=sentiment.capitalize(),
                    marker_color=color,
                    text=source_analysis_pct[sentiment].round(1).astype(str) + '%',
                    textposition='auto'
                ))
        
        fig_sentiment.update_layout(
            barmode='group',
            xaxis_title="Source",
            yaxis_title="Percentage of Mentions",
            legend_title="Sentiment"
        )
        st.plotly_chart(fig_sentiment, use_container_width=True)
        
    except Exception as e:
        st.warning(f"Could not generate sentiment distribution: {str(e)}")
        st.write("Sample source data for debugging:", source_analysis.head() if 'source_analysis' in locals() else "No source data available")

if __name__ == "__main__":
    main()
