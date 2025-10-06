import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, timezone
import tweepy
import praw
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import logging
import time
from rep_monitor_utils import NLPPipeline
from googleapiclient.discovery import build
import random
import threading
from collections import defaultdict

# Load environment
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="🔍 Reputation Monitor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global rate limiters for each API
class APIRateLimiter:
    def __init__(self):
        self.locks = defaultdict(threading.Lock)
        self.last_calls = defaultdict(float)
        self.call_counts = defaultdict(list)
        
    def wait_if_needed(self, api_name, calls_per_minute=1, calls_per_hour=60):
        """Enhanced rate limiting with per-minute and per-hour limits"""
        with self.locks[api_name]:
            now = time.time()
            
            # Clean old call records (older than 1 hour)
            self.call_counts[api_name] = [
                call_time for call_time in self.call_counts[api_name] 
                if now - call_time < 3600
            ]
            
            # Check hourly limit
            if len(self.call_counts[api_name]) >= calls_per_hour:
                wait_time = 3600 - (now - min(self.call_counts[api_name]))
                if wait_time > 0:
                    logger.warning(f"{api_name}: Hourly limit reached, waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
            
            # Check per-minute limit
            minute_calls = [
                call_time for call_time in self.call_counts[api_name] 
                if now - call_time < 60
            ]
            
            if len(minute_calls) >= calls_per_minute:
                wait_time = 60 - (now - min(minute_calls)) + random.uniform(1, 3)
                logger.info(f"{api_name}: Rate limit, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
            
            # Minimum wait between calls
            last_call = self.last_calls[api_name]
            min_interval = 60.0 / calls_per_minute + random.uniform(0.5, 1.5)  # Add jitter
            
            if last_call > 0:
                elapsed = now - last_call
                if elapsed < min_interval:
                    wait_time = min_interval - elapsed
                    time.sleep(wait_time)
            
            # Record this call
            self.last_calls[api_name] = time.time()
            self.call_counts[api_name].append(time.time())

# Global rate limiter instance
rate_limiter = APIRateLimiter()

# Initialize APIs
def init_apis():
    twitter = tweepy.Client(
        bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    )
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT", "ReputationMonitor/1.0")
    )
    # Google API credentials
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")
    return twitter, reddit, google_api_key, google_cse_id

twitter_client, reddit_client, GOOGLE_API_KEY, GOOGLE_CSE_ID = init_apis()
nlp = NLPPipeline()

def fetch_twitter_safe(query, since, limit=10, max_retries=2):
    """Ultra-conservative Twitter API calls with enhanced error handling"""
    items = []
    
    # Clamp since to 7 days ago (recent search endpoint restriction)
    earliest = datetime.now(timezone.utc) - timedelta(days=6, hours=23)
    since = max(since, earliest)
    
    for attempt in range(max_retries + 1):
        try:
            # Wait according to rate limits (1 call per minute for safety)
            rate_limiter.wait_if_needed("twitter", calls_per_minute=1, calls_per_hour=50)
            
            logger.info(f"Making Twitter API call (attempt {attempt + 1}/{max_retries + 1})")
            
            # Use very conservative parameters
            res = twitter_client.search_recent_tweets(
                query=f'"{query}" -is:retweet lang:en',  # More specific query
                start_time=since.isoformat(timespec='seconds'),
                max_results=min(limit, 10),  # Stay within limits
                tweet_fields=["created_at", "public_metrics", "author_id"],
                expansions=["author_id"],
                user_auth=False  # Use app-only auth for better rate limits
            )
            
            if not res or not res.data:
                logger.info("No Twitter results found")
                return items
                
            users = {u.id: u for u in res.includes.get("users", [])} if res.includes else {}
            
            for t in res.data:
                dt = t.created_at.replace(tzinfo=timezone.utc)
                txt = t.text
                sent_analysis = nlp.analyze_sentiment(txt)
                sent = sent_analysis['sentiment']
                author = users.get(t.author_id)
                
                items.append({
                    "source": "Twitter",
                    "content": txt,
                    "created_at": dt,
                    "sentiment": sent,
                    "score": t.public_metrics.get("like_count", 0),
                    "url": f"https://twitter.com/{author.username}/status/{t.id}" if author else "",
                    "confidence": sent_analysis.get('confidence', 0.0)
                })
            
            logger.info(f"Successfully fetched {len(items)} Twitter items")
            return items
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "429" in error_msg or "too many requests" in error_msg:
                if attempt < max_retries:
                    # Progressive backoff: 2 min, 5 min, 10 min
                    backoff_time = [120, 300, 600][attempt]
                    logger.warning(f"Rate limit hit, backing off for {backoff_time/60:.1f} minutes...")
                    
                    # Show user-friendly message
                    if 'progress_info' in st.session_state:
                        st.session_state.progress_info.warning(
                            f"⏳ Twitter rate limit reached. Waiting {backoff_time//60} minutes... "
                            f"(This is normal for free Twitter API)"
                        )
                    
                    time.sleep(backoff_time)
                    continue
                else:
                    logger.error(f"Twitter API exhausted after {max_retries} retries")
                    if 'progress_info' in st.session_state:
                        st.session_state.progress_info.error(
                            "❌ Twitter API rate limit exceeded. Try again later or reduce search frequency."
                        )
                    return items
            else:
                logger.error(f"Twitter fetch error: {e}")
                if attempt < max_retries:
                    time.sleep(30)  # Wait 30 seconds for other errors
                    continue
                else:
                    return items
    
    return items

def fetch_reddit_safe(query, since, limit=10):
    """Safe Reddit API calls"""
    items = []
    
    try:
        rate_limiter.wait_if_needed("reddit", calls_per_minute=2, calls_per_hour=100)
        
        for sub in ["all", "news"]:
            try:
                subreddit = reddit_client.subreddit(sub)
                search_results = list(subreddit.search(query, limit=limit//2, time_filter="week"))
                
                for post in search_results:
                    dt = datetime.fromtimestamp(post.created_utc, timezone.utc)
                    if dt < since:
                        continue
                        
                    txt = post.title + " " + (post.selftext or "")
                    sent_analysis = nlp.analyze_sentiment(txt)
                    sent = sent_analysis['sentiment']
                    
                    items.append({
                        "source": "Reddit",
                        "content": txt,
                        "created_at": dt,
                        "sentiment": sent,
                        "score": post.score,
                        "url": "https://reddit.com" + post.permalink,
                        "confidence": sent_analysis.get('confidence', 0.0)
                    })
                    
                    # Process a few top comments safely
                    try:
                        post.comments.replace_more(limit=0)
                        for c in list(post.comments)[:2]:  # Convert to list first
                            if hasattr(c, 'body') and hasattr(c, 'created_utc') and len(c.body.strip()) > 10:
                                dtc = datetime.fromtimestamp(c.created_utc, timezone.utc)
                                if dtc < since:
                                    continue
                                    
                                sent_analysis_c = nlp.analyze_sentiment(c.body)
                                sentc = sent_analysis_c['sentiment']
                                
                                items.append({
                                    "source": "Reddit",
                                    "content": c.body,
                                    "created_at": dtc,
                                    "sentiment": sentc,
                                    "score": getattr(c, 'score', 0),
                                    "url": "https://reddit.com" + getattr(c, 'permalink', post.permalink),
                                    "confidence": sent_analysis_c.get('confidence', 0.0)
                                })
                    except Exception as ce:
                        logger.warning(f"Error processing Reddit comments: {ce}")
                        continue
                        
            except Exception as se:
                logger.warning(f"Error searching subreddit {sub}: {se}")
                continue
                
    except Exception as e:
        logger.error(f"Reddit fetch error: {e}")
        
    return items[:limit]

def fetch_web_safe(query, limit=10):
    """Safe Google Custom Search API calls"""
    items = []
    
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        logger.warning("Google API credentials missing, skipping web search.")
        return items
        
    try:
        rate_limiter.wait_if_needed("google", calls_per_minute=1, calls_per_hour=90)
        
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY, cache_discovery=False)
        res = service.cse().list(
            q=f'"{query}"',  # More specific query with quotes
            cx=GOOGLE_CSE_ID,
            num=min(limit, 10),
            dateRestrict='d7'  # Last 7 days only
        ).execute()
        
        for item in res.get('items', []):
            title = item.get('title', '')
            desc = item.get('snippet', '')
            url = item.get('link', '')
            dt = datetime.utcnow().replace(tzinfo=timezone.utc)
            
            sent_analysis = nlp.analyze_sentiment(f"{title} {desc}")
            sent = sent_analysis['sentiment']
            
            items.append({
                "source": "Web",
                "content": desc or title,
                "created_at": dt,
                "sentiment": sent,
                "score": 0,
                "url": url,
                "confidence": sent_analysis.get('confidence', 0.0)
            })
            
    except Exception as e:
        logger.error(f"Web fetch error: {e}")
        
    return items

def fetch_all(name, days, limit):
    """Coordinated fetching with enhanced progress tracking"""
    since = datetime.now(timezone.utc) - timedelta(days=min(days, 7))
    
    # Enhanced progress tracking
    progress_bar = st.progress(0)
    progress_info = st.empty()
    st.session_state.progress_info = progress_info  # Store for error messages
    
    # Twitter (most restrictive API)
    progress_info.info("🐦 Fetching Twitter mentions... (This may take 1-2 minutes due to rate limits)")
    progress_bar.progress(5)
    
    tw = fetch_twitter_safe(name, since, limit//3)
    progress_bar.progress(40)
    
    # Reddit
    progress_info.info("🔍 Fetching Reddit discussions...")
    rd = fetch_reddit_safe(name, since, limit//3)
    progress_bar.progress(70)
    
    # Web search
    progress_info.info("🌐 Searching the web...")
    wb = fetch_web_safe(name, limit - len(tw) - len(rd))
    progress_bar.progress(90)
    
    # Process results
    progress_info.info("📊 Processing and analyzing results...")
    all_items = tw + rd + wb
    df = pd.DataFrame(all_items)
    
    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])
        df.sort_values("created_at", ascending=False, inplace=True)
    
    progress_bar.progress(100)
    progress_info.success(f"✅ Analysis complete! Found {len(all_items)} mentions")
    
    time.sleep(2)  # Show success message
    progress_bar.empty()
    progress_info.empty()
    
    return df

# Enhanced UI
st.title("🔍 Advanced Reputation Monitor")
st.markdown("*AI-Powered Multi-Platform Sentiment Analysis with Robust Rate Limiting*")

# Important notice about rate limits
st.info("""
🔔 **Rate Limiting Notice**: This app uses conservative rate limits to comply with API restrictions. 
Twitter searches may take 1-2 minutes due to free tier limitations. Please be patient for best results.
""")

# Sidebar
st.sidebar.title("⚙️ Settings")
brand = st.sidebar.text_input("🏢 Brand or Person", "OpenAI")
days = st.sidebar.slider("📅 Days back", 1, 7, 3)
limit = st.sidebar.slider("📊 Max mentions", 5, 30, 15)  # Reduced for rate limiting

# Advanced filters
with st.sidebar.expander("🔧 Advanced Options"):
    filter_sources = st.multiselect("Data Sources", ["Twitter", "Reddit", "Web"], ["Twitter", "Reddit", "Web"])
    min_score = st.number_input("Minimum score", 0, 1000, 0)
    min_confidence = st.slider("Minimum confidence", 0.0, 1.0, 0.0, 0.1)

# API Status Check
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 API Status")
twitter_ok = bool(os.getenv("TWITTER_BEARER_TOKEN"))
reddit_ok = bool(os.getenv("REDDIT_CLIENT_ID"))
google_ok = bool(os.getenv("GOOGLE_API_KEY"))
openai_ok = bool(os.getenv("OPENAI_API_KEY"))

if twitter_ok:
    st.sidebar.success("✅ Twitter API")
else:
    st.sidebar.error("❌ Twitter API")

if reddit_ok:
    st.sidebar.success("✅ Reddit API")
else:
    st.sidebar.error("❌ Reddit API")

if google_ok:
    st.sidebar.success("✅ Google API")
else:
    st.sidebar.error("❌ Google API")
    
if openai_ok:
    st.sidebar.success("✅ OpenAI API (Enhanced Analysis)")
else:
    st.sidebar.warning("⚠️ OpenAI API (Basic Analysis Only)")

# Search button with rate limit warning
if st.sidebar.button("🔍 Search", type="primary"):
    if not any([twitter_ok, reddit_ok, google_ok]):
        st.error("❌ No API credentials found. Please check your .env file.")
    else:
        # Clear any previous rate limit messages
        if 'df' in st.session_state:
            del st.session_state.df
            
        with st.spinner("🔄 Starting comprehensive analysis..."):
            df = fetch_all(brand, days, limit)
            st.session_state.df = df

# Display results (rest of the UI code remains the same)
if "df" in st.session_state and not st.session_state.df.empty:
    df = st.session_state.df
    
    # Filter by sources
    if filter_sources:
        df = df[df.source.isin(filter_sources)]
    
    # Filter by score and confidence
    df = df[df.score >= min_score]
    if 'confidence' in df.columns:
        df = df[df.confidence >= min_confidence]
    
    if df.empty:
        st.warning("No results match your filters.")
    else:
        # Enhanced Metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📊 Total Mentions", len(df))
        
        with col2:
            pos_count = len(df[df.sentiment == "positive"])
            pos_pct = pos_count/len(df)*100 if len(df) > 0 else 0
            st.metric("😊 Positive", f"{pos_count} ({pos_pct:.1f}%)")
        
        with col3:
            neg_count = len(df[df.sentiment == "negative"])
            neg_pct = neg_count/len(df)*100 if len(df) > 0 else 0
            st.metric("😞 Negative", f"{neg_count} ({neg_pct:.1f}%)")
        
        with col4:
            neu_count = len(df[df.sentiment == "neutral"])
            neu_pct = neu_count/len(df)*100 if len(df) > 0 else 0
            st.metric("😐 Neutral", f"{neu_count} ({neu_pct:.1f}%)")
        
        with col5:
            avg_score = df.score.mean()
            st.metric("⭐ Avg Score", f"{avg_score:.1f}")

        # Enhanced Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎭 Sentiment Distribution")
            counts = df.sentiment.value_counts().reset_index()
            counts.columns = ["sentiment", "count"]
            fig = px.pie(counts, values="count", names="sentiment",
                        color="sentiment",
                        color_discrete_map={
                            "positive": "#2ecc71",
                            "negative": "#e74c3c", 
                            "neutral": "#95a5a6"
                        },
                        title="Overall Sentiment Breakdown")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📱 Source Breakdown")
            source_counts = df.source.value_counts().reset_index()
            source_counts.columns = ["source", "count"]
            fig = px.bar(source_counts, x="source", y="count",
                        color="source",
                        color_discrete_sequence=px.colors.qualitative.Set3,
                        title="Mentions by Platform")
            st.plotly_chart(fig, use_container_width=True)

        # Confidence Analysis (if available)
        if 'confidence' in df.columns:
            st.subheader("🎯 Analysis Confidence")
            col1, col2 = st.columns(2)
            
            with col1:
                avg_confidence = df.confidence.mean()
                st.metric("Average Confidence", f"{avg_confidence:.2f}")
                
            with col2:
                high_conf_count = len(df[df.confidence >= 0.7])
                st.metric("High Confidence Results", f"{high_conf_count}/{len(df)}")

        # Keyword analysis
        st.subheader("🔤 Top Keywords & Topics")
        all_text = " ".join(df.content.fillna("").astype(str))
        keywords = nlp.extract_keywords(all_text, 15)
        
        if keywords:
            keyword_cols = st.columns(5)
            for i, keyword in enumerate(keywords[:15]):
                with keyword_cols[i % 5]:
                    st.button(f"#{keyword}", disabled=True, key=f"keyword_{i}")

        # Timeline if enough data
        if len(df) > 5:
            st.subheader("📈 Sentiment Over Time")
            df_timeline = df.copy()
            df_timeline["date"] = df_timeline.created_at.dt.date
            timeline_data = df_timeline.groupby(["date", "sentiment"]).size().reset_index(name="count")
            fig = px.line(timeline_data, x="date", y="count", color="sentiment",
                         color_discrete_map={
                             "positive": "#2ecc71",
                             "negative": "#e74c3c",
                             "neutral": "#95a5a6"
                         },
                         title="Sentiment Trends Over Time")
            st.plotly_chart(fig, use_container_width=True)

        # Detailed mentions table
        st.subheader("📋 Recent Mentions")
        df_display = df.copy()
        df_display["time"] = df_display.created_at.dt.strftime("%Y-%m-%d %H:%M")
        
        # Add sentiment emojis
        sentiment_map = {"positive": "😊", "negative": "😞", "neutral": "😐"}
        df_display["sentiment_display"] = df_display.sentiment.map(sentiment_map) + " " + df_display.sentiment
        
        # Add confidence if available
        display_cols = ["source", "time", "sentiment_display", "score", "content", "url"]
        if 'confidence' in df_display.columns:
            df_display["confidence_display"] = df_display.confidence.round(2)
            display_cols.insert(-2, "confidence_display")
        
        available_cols = [col for col in display_cols if col in df_display.columns]
        
        column_config = {
            "url": st.column_config.LinkColumn("🔗 Link"),
            "sentiment_display": "😊 Sentiment",
            "score": "⭐ Score"
        }
        
        if 'confidence_display' in df_display.columns:
            column_config["confidence_display"] = "🎯 Confidence"
        
        st.dataframe(
            df_display[available_cols],
            column_config=column_config,
            use_container_width=True,
            hide_index=True
        )

        # Export option
        if st.button("📥 Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{brand}_reputation_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

else:
    # Welcome screen
    st.markdown("""
    ## Welcome to Advanced Reputation Monitor
    
    Monitor your brand's online reputation across multiple platforms with **AI-powered sentiment analysis**.
    
    ### Rate Limit Optimized Features:
    
    - **Smart Rate Limiting**: Automatic API quota management with intelligent backoff
    - **Multi-Platform Monitoring**: Twitter, Reddit, and Web mentions  
    - **Conservative Limits**: Optimized for free API tiers
    - **Confidence Scoring**: Reliability metrics for each prediction
    - **Real-time Analytics**: Interactive charts and timeline tracking
    - **Keyword Discovery**: AI-powered topic and theme extraction
    - **Export Capabilities**: Download results for further analysis
    
    ### Get Started:
    
    1. **Configure APIs**: Ensure your `.env` file contains valid API keys
    2. **Enter Search Term**: Brand name, person, or product in the sidebar
    3. **Adjust Settings**: Time range and limits (start small for testing)
    4. **Run Analysis**: Click "Search" and be patient with rate limits
    5. **Explore Results**: Interactive dashboard with sentiment insights
    
    ### Important Notes:
    
    - **Twitter searches take 1-2 minutes** due to free tier rate limits
    - Start with **smaller limits (5-15 mentions)** for faster results  
    - **Be patient** - the app waits between API calls to avoid errors
    - Results are cached until you search again
    
    ### Required API Keys:
    - `TWITTER_BEARER_TOKEN` - For Twitter mentions (most restrictive)
    - `REDDIT_CLIENT_ID` & `REDDIT_CLIENT_SECRET` - For Reddit discussions  
    - `GOOGLE_API_KEY` & `GOOGLE_CSE_ID` - For web search results
    - `OPENAI_API_KEY` - For enhanced sentiment analysis (optional)
    """)

st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Pro Tips")
st.sidebar.info("""
- Start with 5-10 mentions to test quickly
- Use specific brand names for better results
- Be patient with Twitter rate limits
- Monitor during off-peak hours for faster results
- Higher confidence scores = more reliable predictions
""")

# Footer
st.markdown("---")
st.markdown("*Powered by Twitter API v2, Reddit API, Google Custom Search & Advanced Rate Limiting*")