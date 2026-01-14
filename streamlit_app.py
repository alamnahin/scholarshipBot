import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

# Set page config
st.set_page_config(
    page_title="🎓 Scholarship Hunter",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    h1 {
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .st-expander {
        border: 2px solid #667eea;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scholarships' not in st.session_state:
    st.session_state.scholarships = None
if 'last_updated' not in st.session_state:
    st.session_state.last_updated = None

# Header
st.markdown("# 🎓 Scholarship Hunter Dashboard")
st.markdown("*AI-Powered Fully Funded Master's Scholarship Finder*")

# Sidebar navigation
with st.sidebar:
    st.markdown("### 🚀 Navigation")
    page = st.radio(
        "Select Page",
        ["📊 Dashboard", "🔍 Run Search", "💾 Saved Scholarships", "📈 Analytics", "⚙️ Settings"],
        key="page_nav"
    )

# Load scholarships from Google Sheets
@st.cache_data(ttl=300)
def load_scholarships():
    """Load scholarships from Google Sheets"""
    try:
        from main import ScholarshipHunter
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Load credentials
        creds_path = os.getenv('GOOGLE_SHEETS_CREDS_PATH')
        if creds_path and os.path.exists(creds_path):
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
            client = gspread.authorize(creds)
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
            spreadsheet = client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet("Scholarships")
            records = worksheet.get_all_records()
            
            if records:
                df = pd.DataFrame(records)
                return df
    except Exception as e:
        st.warning(f"Could not load from sheet: {e}")
    
    return pd.DataFrame()

# Page: Dashboard
if page == "📊 Dashboard":
    st.markdown("## 📊 Overview")
    
    # Load data
    df = load_scholarships()
    
    if df.empty:
        st.info("📭 No scholarships found yet. Run a search to get started!")
    else:
        # Calculate metrics
        total_scholarships = len(df)
        avg_match_score = df['Match Score'].astype(float).mean() if 'Match Score' in df.columns else 0
        
        # Create metric columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🎯 Total Scholarships",
                total_scholarships,
                delta="Found so far"
            )
        
        with col2:
            st.metric(
                "⭐ Avg Match Score",
                f"{avg_match_score:.1f}%",
                delta="AI Confidence"
            )
        
        with col3:
            # Count upcoming deadlines (within 60 days)
            upcoming = 0
            if 'Application Deadline' in df.columns:
                try:
                    upcoming = len(df[pd.to_datetime(df['Application Deadline'], errors='coerce') > datetime.now()])
                except:
                    upcoming = 0
            st.metric(
                "📅 Upcoming Deadlines",
                upcoming,
                delta="Next 60 days"
            )
        
        with col4:
            # Last updated
            if 'Date Found' in df.columns and len(df) > 0:
                last_date = pd.to_datetime(df['Date Found'], errors='coerce').max()
                days_ago = (datetime.now() - last_date).days
                st.metric(
                    "🕐 Last Updated",
                    f"{days_ago}d ago",
                    delta="Most recent"
                )
        
        st.divider()
        
        # Charts Section
        st.markdown("### 📈 Visual Insights")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("#### Match Score Distribution")
            if 'Match Score' in df.columns:
                match_scores = df['Match Score'].astype(float)
                fig = px.histogram(
                    match_scores,
                    nbins=10,
                    title="Scholarship Match Scores",
                    labels={"value": "Match Score (%)", "count": "Number of Scholarships"},
                    color_discrete_sequence=["#667eea"]
                )
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with chart_col2:
            st.markdown("#### Deadline Timeline")
            if 'Application Deadline' in df.columns:
                try:
                    df_deadline = df[['Program Name', 'Application Deadline']].copy()
                    df_deadline['Date'] = pd.to_datetime(df_deadline['Application Deadline'], errors='coerce')
                    df_deadline = df_deadline.dropna(subset=['Date'])
                    df_deadline = df_deadline.sort_values('Date').head(10)
                    
                    if not df_deadline.empty:
                        fig = px.bar(
                            df_deadline,
                            x='Date',
                            y='Program Name',
                            orientation='h',
                            title="Next 10 Application Deadlines",
                            color_discrete_sequence=["#764ba2"]
                        )
                        fig.update_layout(height=400, showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                except:
                    st.info("Could not parse deadline dates")
        
        st.divider()
        
        # Table
        st.markdown("### 📋 All Scholarships")
        st.dataframe(
            df,
            use_container_width=True,
            height=400,
            hide_index=True
        )

# Page: Run Search
elif page == "🔍 Run Search":
    st.markdown("## 🔍 Run Scholarship Search")
    
    st.info("🤖 This will search for scholarships, analyze them with AI, and save matches to your Google Sheet.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input(
            "Search Query",
            value="fully funded msc in AI scholarship 2026 international",
            placeholder="Enter your search query..."
        )
    
    with col2:
        max_results = st.number_input(
            "Max Results",
            min_value=1,
            max_value=20,
            value=10
        )
    
    if st.button("🚀 Start Search", use_container_width=True):
        with st.spinner("🔄 Searching and analyzing scholarships..."):
            try:
                from main import ScholarshipHunter
                
                # Create hunter instance
                hunter = ScholarshipHunter()
                hunter.search_query = search_query
                hunter.max_results = max_results
                
                # Run search
                search_results = hunter.search_scholarships()
                
                if not search_results:
                    st.error("❌ No search results found. Try a different query.")
                else:
                    st.success(f"✅ Found {len(search_results)} results!")
                    
                    # Create progress bar
                    progress_bar = st.progress(0)
                    matches_found = 0
                    
                    for idx, result in enumerate(search_results):
                        progress = (idx + 1) / len(search_results)
                        progress_bar.progress(progress, text=f"Processing {idx + 1}/{len(search_results)}")
                        
                        # Scrape
                        page_text = hunter.scrape_page(result['url'])
                        if not page_text:
                            continue
                        
                        # Analyze
                        match = hunter.analyze_with_gemini(page_text, result['url'])
                        
                        if match:
                            hunter.save_to_database(match)
                            matches_found += 1
                    
                    progress_bar.empty()
                    
                    # Success message
                    st.balloons()
                    st.success(f"""
                    ✅ **Search Complete!**
                    - Processed: {len(search_results)} pages
                    - Matches Found: {matches_found}
                    - Check "Saved Scholarships" tab to view results
                    """)
                    
                    # Clear cache to refresh data
                    st.cache_data.clear()
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Make sure all environment variables are set correctly.")

# Page: Saved Scholarships
elif page == "💾 Saved Scholarships":
    st.markdown("## 💾 Saved Scholarships")
    
    df = load_scholarships()
    
    if df.empty:
        st.info("📭 No scholarships saved yet. Run a search first!")
    else:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'Match Score' in df.columns:
                min_score = st.slider(
                    "Minimum Match Score",
                    min_value=0,
                    max_value=100,
                    value=70,
                    step=5
                )
                df_filtered = df[df['Match Score'].astype(float) >= min_score]
            else:
                df_filtered = df
        
        with col2:
            if 'Application Deadline' in df.columns:
                sort_by = st.selectbox(
                    "Sort by",
                    ["Match Score (High to Low)", "Deadline (Earliest)", "Date Found (Newest)"]
                )
        
        with col3:
            st.metric("📊 Showing", len(df_filtered), f"of {len(df)}")
        
        # Sort
        if sort_by == "Match Score (High to Low)":
            df_filtered['Match Score'] = pd.to_numeric(df_filtered['Match Score'], errors='coerce')
            df_filtered = df_filtered.sort_values('Match Score', ascending=False)
        elif sort_by == "Deadline (Earliest)":
            df_filtered['Application Deadline'] = pd.to_datetime(df_filtered['Application Deadline'], errors='coerce')
            df_filtered = df_filtered.sort_values('Application Deadline')
        else:
            df_filtered['Date Found'] = pd.to_datetime(df_filtered['Date Found'], errors='coerce')
            df_filtered = df_filtered.sort_values('Date Found', ascending=False)
        
        # Display scholarships
        for idx, row in df_filtered.iterrows():
            with st.expander(f"🎓 {row.get('Program Name', 'Unknown')} - {row.get('Match Score', 'N/A')}%"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**Program:** {row.get('Program Name', 'N/A')}")
                    st.markdown(f"**Deadline:** {row.get('Application Deadline', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Match Score:** {row.get('Match Score', 'N/A')}%")
                    st.markdown(f"**Status:** {row.get('Status', 'New')}")
                
                with col3:
                    st.markdown(f"**Found:** {row.get('Date Found', 'N/A')}")
                
                st.markdown("---")
                st.markdown(f"**Notes:** {row.get('Notes', 'No notes')}")
                
                # Link
                url = row.get('Official URL', '')
                if url:
                    st.markdown(f"[📄 Visit Official Page]({url})")

# Page: Analytics
elif page == "📈 Analytics":
    st.markdown("## 📈 Advanced Analytics")
    
    df = load_scholarships()
    
    if df.empty:
        st.info("📭 No data yet. Run a search to generate analytics!")
    else:
        # Key metrics
        st.markdown("### 📊 Key Metrics")
        
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.metric("📊 Total Scholarships", len(df))
        
        with metric_col2:
            if 'Match Score' in df.columns:
                highest_score = df['Match Score'].astype(float).max()
                st.metric("🏆 Highest Match", f"{highest_score:.0f}%")
        
        with metric_col3:
            if 'Match Score' in df.columns:
                above_80 = len(df[df['Match Score'].astype(float) >= 80])
                st.metric("🔥 Above 80%", above_80)
        
        with metric_col4:
            avg_processing = len(df)
            st.metric("✅ Processed", avg_processing)
        
        st.divider()
        
        # Detailed charts
        st.markdown("### 📉 Detailed Visualizations")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("#### Match Score Statistics")
            if 'Match Score' in df.columns:
                scores = df['Match Score'].astype(float)
                stats_data = {
                    'Metric': ['Min', 'Q1', 'Median', 'Q3', 'Max', 'Mean'],
                    'Score': [
                        scores.min(),
                        scores.quantile(0.25),
                        scores.median(),
                        scores.quantile(0.75),
                        scores.max(),
                        scores.mean()
                    ]
                }
                stats_df = pd.DataFrame(stats_data)
                
                fig = px.bar(
                    stats_df,
                    x='Metric',
                    y='Score',
                    color='Score',
                    color_continuous_scale='viridis',
                    title="Match Score Statistics"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with chart_col2:
            st.markdown("#### Status Distribution")
            if 'Status' in df.columns:
                status_counts = df['Status'].value_counts()
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Scholarship Status",
                    color_discrete_sequence=["#667eea", "#764ba2", "#f093fb"]
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

# Page: Settings
elif page == "⚙️ Settings":
    st.markdown("## ⚙️ Settings & Configuration")
    
    with st.expander("🔑 API Keys Status"):
        env_vars = {
            "GEMINI_API_KEY": "✅" if os.getenv('GEMINI_API_KEY') else "❌",
            "GOOGLE_SEARCH_API_KEY": "✅" if os.getenv('GOOGLE_SEARCH_API_KEY') else "❌",
            "GOOGLE_SEARCH_ENGINE_ID": "✅" if os.getenv('GOOGLE_SEARCH_ENGINE_ID') else "❌",
            "SPREADSHEET_ID": "✅" if os.getenv('SPREADSHEET_ID') else "❌",
            "GOOGLE_SHEETS_CREDS_PATH": "✅" if os.getenv('GOOGLE_SHEETS_CREDS_PATH') else "❌",
        }
        
        for key, status in env_vars.items():
            st.write(f"{status} {key}")
    
    with st.expander("📋 About"):
        st.markdown("""
        ### 🎓 Scholarship Hunter
        
        An AI-powered automation tool that searches for fully funded Master's scholarships and matches them against your CV.
        
        **Tech Stack:**
        - 🔍 Google Custom Search API
        - 🤖 Gemini AI (Analysis)
        - 📊 Google Sheets (Database)
        - 🌐 Streamlit (Web Interface)
        
        **How it works:**
        1. Searches the web for scholarships
        2. Scrapes scholarship pages
        3. Analyzes with AI to find full matches
        4. Saves results to Google Sheet
        
        **Version:** 1.0.0
        """)
    
    with st.expander("🚀 Deployment"):
        st.markdown("""
        ### Deploy on Streamlit Cloud (FREE)
        
        1. Push code to GitHub
        2. Go to https://streamlit.io/cloud
        3. Click "New app"
        4. Connect your repo
        5. Add secrets in "Advanced settings"
        6. Deploy!
        """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: white; font-size: 12px; margin-top: 20px;'>
    🎓 Scholarship Hunter v1.0 | Made with ❤️ | Powered by AI
</div>
""", unsafe_allow_html=True)
