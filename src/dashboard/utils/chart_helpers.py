import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

def create_productivity_gauge(score: float, title: str = "Productivity Score") -> go.Figure:
    """Create a gauge chart for productivity score"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        delta={'reference': 70},
        gauge={
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
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_attention_timeline(attention_data: pd.DataFrame, 
                            resample_interval: str = '5T') -> go.Figure:
    """Create attention score timeline chart"""
    if attention_data.empty:
        return go.Figure().add_annotation(
            text="No attention data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Ensure timestamp is datetime
    attention_data['timestamp'] = pd.to_datetime(attention_data['timestamp'])
    attention_data = attention_data.set_index('timestamp')
    
    # Resample data
    resampled = attention_data.resample(resample_interval).agg({
        'attention_score': 'mean',
        'face_detected': 'mean',
        'blink_rate': 'mean'
    }).reset_index()
    
    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Attention score
    fig.add_trace(
        go.Scatter(
            x=resampled['timestamp'],
            y=resampled['attention_score'],
            mode='lines+markers',
            name='Attention Score',
            line=dict(color='green', width=2),
            marker=dict(size=4)
        ),
        secondary_y=False,
    )
    
    # Face detection rate
    fig.add_trace(
        go.Scatter(
            x=resampled['timestamp'],
            y=resampled['face_detected'],
            mode='lines',
            name='Face Detection Rate',
            line=dict(color='blue', dash='dash'),
            opacity=0.7
        ),
        secondary_y=True,
    )
    
    # Update layout
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Attention Score", secondary_y=False)
    fig.update_yaxes(title_text="Face Detection Rate", secondary_y=True)
    
    fig.update_layout(
        title="Attention Tracking Over Time",
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_typing_activity_chart(keystroke_data: pd.DataFrame,
                               resample_interval: str = '5T') -> go.Figure:
    """Create typing activity chart with keystrokes and speed"""
    if keystroke_data.empty:
        return go.Figure().add_annotation(
            text="No keystroke data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Ensure timestamp is datetime
    keystroke_data['timestamp'] = pd.to_datetime(keystroke_data['timestamp'])
    keystroke_data = keystroke_data.set_index('timestamp')
    
    # Resample data
    resampled = keystroke_data.resample(resample_interval).agg({
        'key_count': 'sum',
        'typing_speed': 'mean',
        'is_active': 'any'
    }).reset_index()
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Keystrokes per Interval', 'Typing Speed (WPM)'),
        vertical_spacing=0.1
    )
    
    # Keystrokes bar chart
    colors = ['lightgreen' if active else 'lightcoral' 
             for active in resampled['is_active']]
    
    fig.add_trace(
        go.Bar(
            x=resampled['timestamp'],
            y=resampled['key_count'],
            name='Keystrokes',
            marker_color=colors,
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Typing speed line chart
    fig.add_trace(
        go.Scatter(
            x=resampled['timestamp'],
            y=resampled['typing_speed'],
            mode='lines+markers',
            name='Typing Speed',
            line=dict(color='orange', width=2),
            marker=dict(size=4),
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Keystrokes", row=1, col=1)
    fig.update_yaxes(title_text="WPM", row=2, col=1)
    
    fig.update_layout(
        title="Typing Activity Analysis",
        height=500,
        hovermode='x unified'
    )
    
    return fig

def create_app_usage_pie(window_data: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Create pie chart for application usage"""
    if window_data.empty:
        return go.Figure().add_annotation(
            text="No application data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Calculate app usage in minutes
    app_usage = window_data.groupby('application_name')['duration_seconds'].sum() / 60
    app_usage = app_usage.sort_values(ascending=False)
    
    # Take top N apps and group others
    if len(app_usage) > top_n:
        top_apps = app_usage.head(top_n)
        others_sum = app_usage.iloc[top_n:].sum()
        if others_sum > 0:
            top_apps = pd.concat([top_apps, pd.Series([others_sum], index=['Others'])])
    else:
        top_apps = app_usage
    
    # Create pie chart
    fig = px.pie(
        values=top_apps.values,
        names=top_apps.index,
        title=f"Application Usage (Top {top_n})"
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Time: %{value:.1f} min<br>Percentage: %{percent}<extra></extra>'
    )
    
    fig.update_layout(height=400)
    
    return fig

def create_category_breakdown_chart(window_data: pd.DataFrame) -> go.Figure:
    """Create horizontal bar chart for category breakdown"""
    if window_data.empty:
        return go.Figure().add_annotation(
            text="No category data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Calculate category usage in minutes
    category_usage = window_data.groupby('category')['duration_seconds'].sum() / 60
    category_usage = category_usage.sort_values(ascending=True)
    
    # Color mapping for categories
    color_map = {
        'productivity': 'green',
        'communication': 'blue',
        'browsing': 'orange',
        'entertainment': 'red',
        'other': 'gray'
    }
    
    colors = [color_map.get(cat, 'gray') for cat in category_usage.index]
    
    fig = go.Figure(go.Bar(
        x=category_usage.values,
        y=category_usage.index,
        orientation='h',
        marker_color=colors,
        text=[f'{val:.1f} min' for val in category_usage.values],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Time by Application Category",
        xaxis_title="Time (minutes)",
        yaxis_title="Category",
        height=300
    )
    
    return fig

def create_hourly_pattern_heatmap(data: pd.DataFrame, 
                                value_col: str, 
                                title: str = "Activity Pattern") -> go.Figure:
    """Create heatmap showing hourly activity patterns"""
    if data.empty:
        return go.Figure().add_annotation(
            text="No data available for heatmap",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Ensure timestamp is datetime
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data['hour'] = data['timestamp'].dt.hour
    data['day_of_week'] = data['timestamp'].dt.day_name()
    
    # Create pivot table for heatmap
    if value_col == 'count':
        heatmap_data = data.groupby(['day_of_week', 'hour']).size().reset_index(name='value')
    else:
        heatmap_data = data.groupby(['day_of_week', 'hour'])[value_col].sum().reset_index(name='value')
    
    pivot_data = heatmap_data.pivot(index='day_of_week', columns='hour', values='value').fillna(0)
    
    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot_data = pivot_data.reindex([day for day in day_order if day in pivot_data.index])
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='Viridis',
        hoverongaps=False,
        hovertemplate='<b>%{y}</b><br>Hour: %{x}<br>Value: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        height=400
    )
    
    return fig

def create_productivity_trends_chart(daily_data: List[Dict], 
                                   days: int = 7) -> go.Figure:
    """Create line chart showing productivity trends over time"""
    if not daily_data:
        return go.Figure().add_annotation(
            text="No trend data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    df = pd.DataFrame(daily_data)
    df['date'] = pd.to_datetime(df['date'])
    
    # Create subplots for different metrics
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Productivity Score', 'Active Time', 'Attention Score', 'Focus Sessions'),
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )
    
    # Productivity score
    if 'productivity_score' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'], y=df['productivity_score'],
                mode='lines+markers', name='Productivity',
                line=dict(color='blue')
            ),
            row=1, col=1
        )
    
    # Active time
    if 'active_time' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['date'], y=df['active_time'],
                name='Active Time', marker_color='green'
            ),
            row=1, col=2
        )
    
    # Attention score
    if 'avg_attention' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'], y=df['avg_attention'],
                mode='lines+markers', name='Attention',
                line=dict(color='orange')
            ),
            row=2, col=1
        )
    
    # Focus sessions
    if 'focus_sessions' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['date'], y=df['focus_sessions'],
                name='Focus Sessions', marker_color='purple'
            ),
            row=2, col=2
        )
    
    fig.update_layout(
        title=f"Productivity Trends (Last {days} days)",
        height=600,
        showlegend=False
    )
    
    return fig

def create_focus_sessions_timeline(focus_sessions: List[Dict]) -> go.Figure:
    """Create Gantt chart for focus sessions"""
    if not focus_sessions:
        return go.Figure().add_annotation(
            text="No focus sessions to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Prepare data for Gantt chart
    gantt_data = []
    for i, session in enumerate(focus_sessions):
        start_time = session['start_time']
        end_time = session['end_time']
        avg_attention = session['avg_attention']
        
        gantt_data.append(dict(
            Task=f"Session {i+1}",
            Start=start_time,
            Finish=end_time,
            Resource=f"Attention: {avg_attention:.2f}"
        ))
    
    # Create Gantt chart
    fig = px.timeline(
        gantt_data,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Resource",
        title="Focus Sessions Timeline"
    )
    
    fig.update_layout(height=300)
    
    return fig

def create_comparison_radar_chart(current_metrics: Dict, 
                                previous_metrics: Dict) -> go.Figure:
    """Create radar chart comparing current vs previous metrics"""
    categories = ['Productivity', 'Attention', 'Activity', 'Focus Quality', 'App Usage']
    
    current_values = [
        current_metrics.get('productivity_score', 0),
        current_metrics.get('attention_score', 0) * 100,
        current_metrics.get('activity_percentage', 0),
        current_metrics.get('focus_quality', 0),
        current_metrics.get('app_productivity', 0)
    ]
    
    previous_values = [
        previous_metrics.get('productivity_score', 0),
        previous_metrics.get('attention_score', 0) * 100,
        previous_metrics.get('activity_percentage', 0),
        previous_metrics.get('focus_quality', 0),
        previous_metrics.get('app_productivity', 0)
    ]
    
    fig = go.Figure()
    
    # Current metrics
    fig.add_trace(go.Scatterpolar(
        r=current_values,
        theta=categories,
        fill='toself',
        name='Current',
        line_color='blue'
    ))
    
    # Previous metrics
    fig.add_trace(go.Scatterpolar(
        r=previous_values,
        theta=categories,
        fill='toself',
        name='Previous',
        line_color='red',
        opacity=0.6
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="Performance Comparison",
        height=400
    )
    
    return fig

def create_insights_wordcloud_data(insights: List[str]) -> Dict[str, int]:
    """Extract key words from insights for word cloud visualization"""
    from collections import Counter
    import re
    
    # Common words to exclude
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
        'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
        'might', 'must', 'can', 'a', 'an', 'this', 'that', 'these', 'those',
        'you', 'your', 'yours', 'yourself', 'yourselves'
    }
    
    # Extract words from insights
    all_words = []
    for insight in insights:
        # Remove emojis and special characters, keep only words
        clean_text = re.sub(r'[^\w\s]', ' ', insight)
        words = clean_text.lower().split()
        # Filter out stop words and short words
        filtered_words = [word for word in words if len(word) > 3 and word not in stop_words]
        all_words.extend(filtered_words)
    
    # Count word frequencies
    word_counts = Counter(all_words)
    
    return dict(word_counts.most_common(20))  # Top 20 words
