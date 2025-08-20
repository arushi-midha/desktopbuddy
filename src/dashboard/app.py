import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import DASHBOARD_UPDATE_INTERVAL, LOGGING_CONFIG
from src.data_processing.database_manager import DatabaseManager
from src.data_processing.data_processor import DataProcessor
from src.data_collection.data_collector import DataCollector

# Configure page
st.set_page_config(
    page_title="DeskBuddy - Productivity Dashboard",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def init_components():
    """Initialize data components"""
    return {
        'db_manager': DatabaseManager(),
        'data_processor': DataProcessor(),
        'data_collector': DataCollector()
    }

def main():
    """Main dashboard application"""
    # Initialize components
    components = init_components()
    db_manager = components['db_manager']
    data_processor = components['data_processor']
    data_collector = components['data_collector']
    
    # Sidebar
    st.sidebar.title("🖥️ DeskBuddy")
    st.sidebar.markdown("AI-Powered Productivity Companion")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigate to:",
        ["Real-time Dashboard", "Daily Analysis", "Weekly Trends", "Settings", "Data Collection"]
    )
    
    # Page routing
    if page == "Real-time Dashboard":
        show_realtime_dashboard(data_collector, db_manager)
    elif page == "Daily Analysis":
        show_daily_analysis(data_processor)
    elif page == "Weekly Trends":
        show_weekly_trends(data_processor)
    elif page == "Settings":
        show_settings()
    elif page == "Data Collection":
        show_data_collection(data_collector)

def show_realtime_dashboard(data_collector, db_manager):
    """Real-time productivity dashboard"""
    st.title("📊 Real-time Productivity Dashboard")
    
    # Auto-refresh controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        auto_refresh = st.checkbox("Auto-refresh (10s)", value=True)
    with col2:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    with col3:
        if st.button("📊 Export Data"):
            export_data(db_manager)
    
    # Auto-refresh logic
    if auto_refresh:
        placeholder = st.empty()
        time.sleep(DASHBOARD_UPDATE_INTERVAL)
        st.rerun()
    
    # Get real-time data
    try:
        current_time = datetime.now()
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get today's data
        keystroke_data = db_manager.get_keystroke_data(today_start, current_time)
        window_data = db_manager.get_window_data(today_start, current_time)
        attention_data = db_manager.get_attention_data(today_start, current_time)
        
        # Show current status
        show_current_status(keystroke_data, window_data, attention_data)
        
        # Show activity charts
        col1, col2 = st.columns(2)
        
        with col1:
            show_keystroke_activity_chart(keystroke_data)
            show_application_usage_chart(window_data)
        
        with col2:
            show_attention_chart(attention_data)
            show_productivity_gauge(keystroke_data, window_data, attention_data)
            
    except Exception as e:
        st.error(f"Error loading real-time data: {e}")
        st.info("Make sure data collection is running in the background.")

def show_current_status(keystroke_data, window_data, attention_data):
    """Show current activity status"""
    st.subheader("🔴 Current Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Current typing activity
    with col1:
        current_typing = "🟢 Active" if not keystroke_data.empty and keystroke_data.iloc[-1]['is_active'] else "🔴 Idle"
        typing_speed = keystroke_data['typing_speed'].iloc[-1] if not keystroke_data.empty else 0
        st.metric("Typing Status", current_typing, f"{typing_speed:.1f} WPM")
    
    # Current application
    with col2:
        current_app = window_data['application_name'].iloc[-1] if not window_data.empty else "Unknown"
        app_category = window_data['category'].iloc[-1] if not window_data.empty else "other"
        st.metric("Current App", current_app, app_category.title())
    
    # Attention level
    with col3:
        if not attention_data.empty:
            current_attention = attention_data['attention_score'].iloc[-1]
            face_detected = "👤 Yes" if attention_data['face_detected'].iloc[-1] else "❌ No"
            st.metric("Attention Level", f"{current_attention:.2f}", face_detected)
        else:
            st.metric("Attention Level", "No Data", "Camera Off")
    
    # Session duration
    with col4:
        if not keystroke_data.empty:
            session_start = keystroke_data['timestamp'].min()
            duration = (datetime.now() - session_start).total_seconds() / 3600
            st.metric("Session Duration", f"{duration:.1f} hours")
        else:
            st.metric("Session Duration", "0.0 hours")

def show_keystroke_activity_chart(keystroke_data):
    """Show keystroke activity over time"""
    st.subheader("⌨️ Typing Activity")
    
    if keystroke_data.empty:
        st.info("No keystroke data available")
        return
    
    # Resample data to 5-minute intervals
    keystroke_data['timestamp'] = pd.to_datetime(keystroke_data['timestamp'])
    keystroke_data = keystroke_data.set_index('timestamp')
    
    # Create 5-minute aggregations
    activity_data = keystroke_data.resample('5T').agg({
        'key_count': 'sum',
        'typing_speed': 'mean',
        'is_active': 'any'
    }).reset_index()
    
    # Create subplot
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Keystrokes per 5 minutes', 'Typing Speed (WPM)'),
        vertical_spacing=0.1
    )
    
    # Keystrokes chart
    fig.add_trace(
        go.Bar(
            x=activity_data['timestamp'],
            y=activity_data['key_count'],
            name='Keystrokes',
            marker_color='lightblue'
        ),
        row=1, col=1
    )
    
    # Typing speed chart
    fig.add_trace(
        go.Scatter(
            x=activity_data['timestamp'],
            y=activity_data['typing_speed'],
            mode='lines+markers',
            name='Typing Speed',
            line=dict(color='orange')
        ),
        row=2, col=1
    )
    
    fig.update_layout(height=400, showlegend=False)
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Keystrokes", row=1, col=1)
    fig.update_yaxes(title_text="WPM", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

def show_application_usage_chart(window_data):
    """Show application usage breakdown"""
    st.subheader("💻 Application Usage")
    
    if window_data.empty:
        st.info("No application data available")
        return
    
    # Calculate total time per application
    app_usage = window_data.groupby('application_name')['duration_seconds'].sum().sort_values(ascending=False)
    app_usage_minutes = app_usage / 60  # Convert to minutes
    
    # Take top 10 applications
    top_apps = app_usage_minutes.head(10)
    
    # Create pie chart
    fig = px.pie(
        values=top_apps.values,
        names=top_apps.index,
        title="Time Distribution (Top 10 Apps)"
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=350)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show category breakdown
    category_usage = window_data.groupby('category')['duration_seconds'].sum() / 60
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Productive Time", f"{category_usage.get('productivity', 0):.0f} min")
    with col2:
        st.metric("Entertainment Time", f"{category_usage.get('entertainment', 0):.0f} min")

def show_attention_chart(attention_data):
    """Show attention levels over time"""
    st.subheader("👁️ Attention Tracking")
    
    if attention_data.empty:
        st.info("No attention data available. Make sure webcam is enabled.")
        return
    
    # Resample to 2-minute intervals
    attention_data['timestamp'] = pd.to_datetime(attention_data['timestamp'])
    attention_data = attention_data.set_index('timestamp')
    
    attention_resampled = attention_data.resample('2T').agg({
        'attention_score': 'mean',
        'face_detected': 'mean',
        'blink_rate': 'mean'
    }).reset_index()
    
    # Create attention chart
    fig = go.Figure()
    
    # Attention score
    fig.add_trace(go.Scatter(
        x=attention_resampled['timestamp'],
        y=attention_resampled['attention_score'],
        mode='lines+markers',
        name='Attention Score',
        line=dict(color='green', width=2)
    ))
    
    # Face detection rate
    fig.add_trace(go.Scatter(
        x=attention_resampled['timestamp'],
        y=attention_resampled['face_detected'],
        mode='lines',
        name='Face Detection Rate',
        line=dict(color='blue', dash='dash'),
        yaxis='y2'
    ))
    
    # Update layout for dual y-axis
    fig.update_layout(
        title="Attention & Face Detection Over Time",
        xaxis_title="Time",
        yaxis=dict(title="Attention Score", side="left"),
        yaxis2=dict(title="Face Detection Rate", side="right", overlaying="y"),
        height=350
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show attention metrics
    avg_attention = attention_data['attention_score'].mean()
    face_detection_rate = attention_data['face_detected'].mean() * 100
    avg_blink_rate = attention_data['blink_rate'].mean()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Avg Attention", f"{avg_attention:.2f}")
    with col2:
        st.metric("Face Detection", f"{face_detection_rate:.0f}%")
    with col3:
        st.metric("Blink Rate", f"{avg_blink_rate:.1f}/min")

def show_productivity_gauge(keystroke_data, window_data, attention_data):
    """Show overall productivity gauge"""
    st.subheader("🎯 Productivity Score")
    
    # Calculate productivity score
    productivity_score = calculate_productivity_score(keystroke_data, window_data, attention_data)
    
    # Create gauge chart
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = productivity_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Overall Productivity"},
        delta = {'reference': 70},  # Reference score
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 25], 'color': "lightgray"},
                {'range': [25, 50], 'color': "yellow"},
                {'range': [50, 75], 'color': "orange"},
                {'range': [75, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # Show productivity components
    components = calculate_productivity_components(keystroke_data, window_data, attention_data)
    
    st.write("**Productivity Breakdown:**")
    for component, score in components.items():
        st.progress(score / 100, text=f"{component}: {score:.0f}%")

def calculate_productivity_score(keystroke_data, window_data, attention_data):
    """Calculate overall productivity score"""
    try:
        scores = []
        weights = []
        
        # Activity score (25% weight)
        if not keystroke_data.empty:
            active_ratio = keystroke_data['is_active'].mean()
            activity_score = active_ratio * 100
            scores.append(activity_score)
            weights.append(0.25)
        
        # Application productivity score (40% weight)
        if not window_data.empty:
            productive_categories = ['productivity', 'communication']
            productive_time = window_data[window_data['category'].isin(productive_categories)]['duration_seconds'].sum()
            total_time = window_data['duration_seconds'].sum()
            if total_time > 0:
                app_score = (productive_time / total_time) * 100
                scores.append(app_score)
                weights.append(0.4)
        
        # Attention score (35% weight)
        if not attention_data.empty:
            avg_attention = attention_data['attention_score'].mean()
            attention_score = avg_attention * 100
            scores.append(attention_score)
            weights.append(0.35)
        
        # Calculate weighted average
        if scores and weights:
            total_weight = sum(weights)
            weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
            return weighted_sum / total_weight
        
        return 0.0
        
    except Exception as e:
        st.error(f"Error calculating productivity score: {e}")
        return 0.0

def calculate_productivity_components(keystroke_data, window_data, attention_data):
    """Calculate individual productivity components"""
    components = {}
    
    try:
        # Activity component
        if not keystroke_data.empty:
            active_ratio = keystroke_data['is_active'].mean()
            components['Activity Level'] = active_ratio * 100
        
        # Application component
        if not window_data.empty:
            productive_categories = ['productivity', 'communication']
            productive_time = window_data[window_data['category'].isin(productive_categories)]['duration_seconds'].sum()
            total_time = window_data['duration_seconds'].sum()
            if total_time > 0:
                components['App Productivity'] = (productive_time / total_time) * 100
        
        # Attention component
        if not attention_data.empty:
            avg_attention = attention_data['attention_score'].mean()
            components['Attention Level'] = avg_attention * 100
        
        # Fill missing components with 0
        all_components = ['Activity Level', 'App Productivity', 'Attention Level']
        for comp in all_components:
            if comp not in components:
                components[comp] = 0.0
        
        return components
        
    except Exception as e:
        st.error(f"Error calculating components: {e}")
        return {}

def show_daily_analysis(data_processor):
    """Show detailed daily analysis"""
    st.title("📈 Daily Analysis")
    
    # Date selector
    selected_date = st.date_input("Select Date", value=datetime.now().date())
    
    if st.button("Generate Analysis"):
        with st.spinner("Analyzing daily data..."):
            try:
                # Convert date to datetime
                analysis_date = datetime.combine(selected_date, datetime.min.time())
                
                # Get daily summary
                summary = data_processor.get_daily_summary(analysis_date)
                
                if not summary:
                    st.warning("No data available for the selected date.")
                    return
                
                # Show productivity metrics
                show_productivity_metrics(summary)
                
                # Show detailed breakdowns
                col1, col2 = st.columns(2)
                
                with col1:
                    show_keystroke_summary(summary['keystroke_summary'])
                    show_attention_summary(summary['attention_summary'])
                
                with col2:
                    show_window_summary(summary['window_summary'])
                    show_insights(summary['insights'])
                    
            except Exception as e:
                st.error(f"Error generating analysis: {e}")

def show_productivity_metrics(summary):
    """Show productivity metrics section"""
    st.subheader("🎯 Productivity Metrics")
    
    metrics = summary.get('productivity_metrics', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        overall_score = metrics.get('overall_productivity_score', 0)
        st.metric("Overall Score", f"{overall_score:.1f}%")
    
    with col2:
        focus_quality = metrics.get('focus_quality_score', 0)
        st.metric("Focus Quality", f"{focus_quality:.1f}%")
    
    with col3:
        distraction_level = metrics.get('distraction_level', 0)
        st.metric("Distraction Level", f"{distraction_level:.1f}%")
    
    with col4:
        efficiency = metrics.get('efficiency_metrics', {}).get('typing_efficiency', 0)
        st.metric("Typing Efficiency", f"{efficiency:.1f}")

def show_keystroke_summary(keystroke_summary):
    """Show keystroke analysis summary"""
    st.subheader("⌨️ Typing Analysis")
    
    if not keystroke_summary:
        st.info("No keystroke data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Keystrokes", f"{keystroke_summary.get('total_keystrokes', 0):,}")
        st.metric("Average Speed", f"{keystroke_summary.get('avg_typing_speed', 0):.1f} WPM")
    
    with col2:
        st.metric("Active Time", f"{keystroke_summary.get('active_time_minutes', 0):.0f} min")
        st.metric("Activity %", f"{keystroke_summary.get('activity_percentage', 0):.1f}%")
    
    # Show typing pattern
    if 'typing_pattern' in keystroke_summary:
        pattern_data = pd.DataFrame(keystroke_summary['typing_pattern'])
        if not pattern_data.empty:
            fig = px.bar(pattern_data, x='hour', y='keystrokes', title="Typing Activity by Hour")
            st.plotly_chart(fig, use_container_width=True)

def show_window_summary(window_summary):
    """Show window usage summary"""
    st.subheader("💻 Application Usage")
    
    if not window_summary:
        st.info("No application data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Apps", window_summary.get('total_applications', 0))
        st.metric("Context Switches", window_summary.get('context_switches', 0))
    
    with col2:
        st.metric("Productive Time", f"{window_summary.get('productivity_apps_time', 0):.0f} min")
        st.metric("Entertainment Time", f"{window_summary.get('distraction_apps_time', 0):.0f} min")
    
    # Show category breakdown
    if 'category_breakdown' in window_summary:
        categories = window_summary['category_breakdown']
        if categories:
            fig = px.pie(values=list(categories.values()), names=list(categories.keys()), 
                        title="Time by Category")
            st.plotly_chart(fig, use_container_width=True)

def show_attention_summary(attention_summary):
    """Show attention analysis summary"""
    st.subheader("👁️ Attention Analysis")
    
    if not attention_summary:
        st.info("No attention data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Avg Attention", f"{attention_summary.get('avg_attention_score', 0):.2f}")
        st.metric("Screen Looking", f"{attention_summary.get('screen_looking_percentage', 0):.1f}%")
    
    with col2:
        st.metric("Face Detection", f"{attention_summary.get('face_detection_rate', 0):.1f}%")
        st.metric("Focus Sessions", len(attention_summary.get('focus_sessions', [])))
    
    # Show focus sessions
    focus_sessions = attention_summary.get('focus_sessions', [])
    if focus_sessions:
        st.write("**Focus Sessions:**")
        for i, session in enumerate(focus_sessions[:5]):  # Show top 5
            duration = session['duration_minutes']
            avg_attention = session['avg_attention']
            st.write(f"Session {i+1}: {duration:.1f} min (Avg attention: {avg_attention:.2f})")

def show_insights(insights):
    """Show insights and recommendations"""
    st.subheader("💡 Insights & Recommendations")
    
    if not insights:
        st.info("No insights available")
        return
    
    for insight in insights:
        st.write(f"• {insight}")

def show_weekly_trends(data_processor):
    """Show weekly trends analysis"""
    st.title("📊 Weekly Trends")
    
    # Date range selector
    end_date = st.date_input("End Date", value=datetime.now().date())
    
    if st.button("Generate Weekly Report"):
        with st.spinner("Analyzing weekly trends..."):
            try:
                end_datetime = datetime.combine(end_date, datetime.max.time())
                trends = data_processor.get_weekly_trends(end_datetime)
                
                if not trends or not trends.get('weekly_data'):
                    st.warning("No data available for the selected week.")
                    return
                
                # Show trend summary
                show_trend_summary(trends)
                
                # Show weekly charts
                show_weekly_charts(trends)
                
            except Exception as e:
                st.error(f"Error generating weekly trends: {e}")

def show_trend_summary(trends):
    """Show weekly trend summary"""
    st.subheader("📈 Trend Summary")
    
    trend_data = trends.get('trends', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        productivity_trend = trend_data.get('productivity', 'unknown')
        trend_emoji = {'improving': '📈', 'declining': '📉', 'stable': '➡️'}.get(productivity_trend, '❓')
        st.metric("Productivity Trend", productivity_trend.title(), delta=trend_emoji)
    
    with col2:
        attention_trend = trend_data.get('attention', 'unknown')
        trend_emoji = {'improving': '📈', 'declining': '📉', 'stable': '➡️'}.get(attention_trend, '❓')
        st.metric("Attention Trend", attention_trend.title(), delta=trend_emoji)
    
    with col3:
        activity_trend = trend_data.get('activity', 'unknown')
        trend_emoji = {'improving': '📈', 'declining': '📉', 'stable': '➡️'}.get(activity_trend, '❓')
        st.metric("Activity Trend", activity_trend.title(), delta=trend_emoji)

def show_weekly_charts(trends):
    """Show weekly trend charts"""
    weekly_data = pd.DataFrame(trends['weekly_data'])
    
    if weekly_data.empty:
        st.info("No weekly data available")
        return
    
    # Productivity score over time
    fig1 = px.line(weekly_data, x='date', y='productivity_score', 
                   title="Daily Productivity Score", markers=True)
    fig1.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig1, use_container_width=True)
    
    # Activity metrics
    col1, col2 = st.columns(2)
    
    with col1:
        fig2 = px.bar(weekly_data, x='date', y='active_time', 
                      title="Daily Active Time (minutes)")
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        fig3 = px.line(weekly_data, x='date', y='avg_attention', 
                       title="Average Attention Score", markers=True)
        fig3.update_layout(yaxis_range=[0, 1])
        st.plotly_chart(fig3, use_container_width=True)

def show_settings():
    """Show settings page"""
    st.title("⚙️ Settings")
    
    st.subheader("Data Collection Settings")
    
    # Data collection toggles
    col1, col2, col3 = st.columns(3)
    
    with col1:
        enable_keystroke = st.checkbox("Enable Keystroke Logging", value=True)
    with col2:
        enable_window = st.checkbox("Enable Window Tracking", value=True)
    with col3:
        enable_webcam = st.checkbox("Enable Webcam Monitoring", value=True)
    
    st.subheader("Privacy Settings")
    
    # Privacy settings
    anonymize_data = st.checkbox("Anonymize collected data", value=True)
    store_facial_images = st.checkbox("Store facial images (not recommended)", value=False)
    
    # Data retention
    retention_days = st.slider("Data retention (days)", min_value=1, max_value=90, value=30)
    
    st.subheader("Dashboard Settings")
    
    # Dashboard settings
    auto_refresh_interval = st.slider("Auto-refresh interval (seconds)", min_value=5, max_value=60, value=10)
    default_time_range = st.selectbox("Default time range", ["today", "week", "month"])
    
    if st.button("Save Settings"):
        st.success("Settings saved! (Note: This is a demo - settings are not actually saved)")

def show_data_collection(data_collector):
    """Show data collection control page"""
    st.title("🔄 Data Collection Control")
    
    st.info("Control the background data collection processes from here.")
    
    # Collection status
    st.subheader("Collection Status")
    
    # This is a simplified status display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Keystroke Logger", "🟢 Running" if True else "🔴 Stopped")
    with col2:
        st.metric("Window Tracker", "🟢 Running" if True else "🔴 Stopped")
    with col3:
        st.metric("Webcam Monitor", "🟢 Running" if True else "🔴 Stopped")
    
    # Control buttons
    st.subheader("Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🟢 Start Collection"):
            st.info("Start data collection by running: `python src/data_collection/data_collector.py`")
    
    with col2:
        if st.button("🔄 Restart Collection"):
            st.info("Restart the data collection process")
    
    with col3:
        if st.button("🛑 Stop Collection"):
            st.info("Stop the data collection process")
    
    # Recent statistics
    st.subheader("Recent Statistics")
    
    try:
        # Get recent stats from database
        db_manager = DatabaseManager()
        current_time = datetime.now()
        hour_ago = current_time - timedelta(hours=1)
        
        keystroke_data = db_manager.get_keystroke_data(hour_ago, current_time)
        window_data = db_manager.get_window_data(hour_ago, current_time)
        attention_data = db_manager.get_attention_data(hour_ago, current_time)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Keystroke Records (1h)", len(keystroke_data))
        with col2:
            st.metric("Window Records (1h)", len(window_data))
        with col3:
            st.metric("Attention Records (1h)", len(attention_data))
            
    except Exception as e:
        st.error(f"Error getting statistics: {e}")

def export_data(db_manager):
    """Export data functionality"""
    try:
        current_time = datetime.now()
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get today's data
        keystroke_data = db_manager.get_keystroke_data(today_start, current_time)
        window_data = db_manager.get_window_data(today_start, current_time)
        attention_data = db_manager.get_attention_data(today_start, current_time)
        
        # Convert to CSV format
        today_str = current_time.strftime("%Y-%m-%d")
        
        if not keystroke_data.empty:
            keystroke_csv = keystroke_data.to_csv(index=False)
            st.download_button(
                "📥 Download Keystroke Data",
                keystroke_csv,
                f"keystroke_data_{today_str}.csv",
                "text/csv"
            )
        
        if not window_data.empty:
            window_csv = window_data.to_csv(index=False)
            st.download_button(
                "📥 Download Window Data",
                window_csv,
                f"window_data_{today_str}.csv",
                "text/csv"
            )
        
        if not attention_data.empty:
            attention_csv = attention_data.to_csv(index=False)
            st.download_button(
                "📥 Download Attention Data",
                attention_csv,
                f"attention_data_{today_str}.csv",
                "text/csv"
            )
            
    except Exception as e:
        st.error(f"Error exporting data: {e}")

if __name__ == "__main__":
    main()
