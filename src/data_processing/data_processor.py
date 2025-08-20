import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.data_processing.database_manager import DatabaseManager
from config.settings import IDLE_THRESHOLD, FOCUS_SESSION_MIN_DURATION

class DataProcessor:
    """Processes and analyzes collected productivity data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager()
    
    def get_daily_summary(self, date: datetime = None) -> Dict[str, Any]:
        """Generate comprehensive daily productivity summary"""
        try:
            if not date:
                date = datetime.now()
            
            # Get data for the day
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            keystroke_data = self.db_manager.get_keystroke_data(start_date, end_date)
            window_data = self.db_manager.get_window_data(start_date, end_date)
            attention_data = self.db_manager.get_attention_data(start_date, end_date)
            
            # Process each data type
            keystroke_summary = self._process_keystroke_data(keystroke_data)
            window_summary = self._process_window_data(window_data)
            attention_summary = self._process_attention_data(attention_data)
            
            # Calculate productivity metrics
            productivity_metrics = self._calculate_productivity_metrics(
                keystroke_summary, window_summary, attention_summary
            )
            
            # Generate insights and recommendations
            insights = self._generate_insights(
                keystroke_summary, window_summary, attention_summary, productivity_metrics
            )
            
            summary = {
                'date': date.date(),
                'keystroke_summary': keystroke_summary,
                'window_summary': window_summary,
                'attention_summary': attention_summary,
                'productivity_metrics': productivity_metrics,
                'insights': insights,
                'generated_at': datetime.now()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating daily summary: {e}")
            return {}
    
    def _process_keystroke_data(self, keystroke_data: pd.DataFrame) -> Dict[str, Any]:
        """Process keystroke activity data"""
        try:
            if keystroke_data.empty:
                return {
                    'total_keystrokes': 0,
                    'avg_typing_speed': 0.0,
                    'active_time_minutes': 0.0,
                    'idle_time_minutes': 0.0,
                    'peak_typing_hour': None,
                    'typing_pattern': []
                }
            
            # Basic statistics
            total_keystrokes = keystroke_data['key_count'].sum()
            avg_typing_speed = keystroke_data['typing_speed'].mean()
            
            # Active vs idle time calculation
            active_records = keystroke_data[keystroke_data['is_active'] == True]
            active_time = len(active_records) * 1.0  # 1 second per record
            total_time = len(keystroke_data) * 1.0
            idle_time = total_time - active_time
            
            # Peak typing hour
            keystroke_data['hour'] = keystroke_data['timestamp'].dt.hour
            hourly_keystrokes = keystroke_data.groupby('hour')['key_count'].sum()
            peak_hour = hourly_keystrokes.idxmax() if not hourly_keystrokes.empty else None
            
            # Typing pattern throughout the day
            typing_pattern = []
            for hour in range(24):
                hour_data = keystroke_data[keystroke_data['hour'] == hour]
                typing_pattern.append({
                    'hour': hour,
                    'keystrokes': hour_data['key_count'].sum(),
                    'avg_speed': hour_data['typing_speed'].mean() if not hour_data.empty else 0,
                    'active_periods': len(hour_data[hour_data['is_active'] == True])
                })
            
            return {
                'total_keystrokes': int(total_keystrokes),
                'avg_typing_speed': float(avg_typing_speed),
                'active_time_minutes': active_time / 60,
                'idle_time_minutes': idle_time / 60,
                'peak_typing_hour': int(peak_hour) if peak_hour is not None else None,
                'typing_pattern': typing_pattern,
                'activity_percentage': (active_time / total_time * 100) if total_time > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error processing keystroke data: {e}")
            return {}
    
    def _process_window_data(self, window_data: pd.DataFrame) -> Dict[str, Any]:
        """Process window/application usage data"""
        try:
            if window_data.empty:
                return {
                    'total_applications': 0,
                    'total_time_minutes': 0.0,
                    'app_usage': {},
                    'category_breakdown': {},
                    'most_used_app': None,
                    'productivity_apps_time': 0.0,
                    'distraction_apps_time': 0.0,
                    'context_switches': 0
                }
            
            # Basic statistics
            total_apps = window_data['application_name'].nunique()
            total_time = window_data['duration_seconds'].sum() / 60  # Convert to minutes
            
            # Application usage breakdown
            app_usage = window_data.groupby('application_name')['duration_seconds'].sum().sort_values(ascending=False)
            app_usage_dict = (app_usage / 60).to_dict()  # Convert to minutes
            
            # Category breakdown
            category_breakdown = window_data.groupby('category')['duration_seconds'].sum().sort_values(ascending=False)
            category_breakdown_dict = (category_breakdown / 60).to_dict()  # Convert to minutes
            
            # Most used application
            most_used_app = app_usage.index[0] if not app_usage.empty else None
            
            # Productivity vs distraction time
            productive_categories = ['productivity', 'communication']
            distraction_categories = ['entertainment']
            
            productivity_time = window_data[
                window_data['category'].isin(productive_categories)
            ]['duration_seconds'].sum() / 60
            
            distraction_time = window_data[
                window_data['category'].isin(distraction_categories)
            ]['duration_seconds'].sum() / 60
            
            # Context switches (application changes)
            context_switches = len(window_data) - 1  # Number of transitions
            
            # Hourly usage pattern
            window_data['hour'] = window_data['timestamp'].dt.hour
            hourly_usage = window_data.groupby('hour')['duration_seconds'].sum() / 60
            usage_pattern = [{'hour': hour, 'minutes': hourly_usage.get(hour, 0)} for hour in range(24)]
            
            return {
                'total_applications': total_apps,
                'total_time_minutes': total_time,
                'app_usage': app_usage_dict,
                'category_breakdown': category_breakdown_dict,
                'most_used_app': most_used_app,
                'productivity_apps_time': productivity_time,
                'distraction_apps_time': distraction_time,
                'context_switches': context_switches,
                'usage_pattern': usage_pattern,
                'productivity_ratio': (productivity_time / total_time * 100) if total_time > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error processing window data: {e}")
            return {}
    
    def _process_attention_data(self, attention_data: pd.DataFrame) -> Dict[str, Any]:
        """Process webcam attention data"""
        try:
            if attention_data.empty:
                return {
                    'total_readings': 0,
                    'avg_attention_score': 0.0,
                    'face_detection_rate': 0.0,
                    'avg_blink_rate': 0.0,
                    'screen_looking_percentage': 0.0,
                    'focus_sessions': [],
                    'attention_pattern': []
                }
            
            # Basic statistics
            total_readings = len(attention_data)
            avg_attention = attention_data['attention_score'].mean()
            face_detection_rate = (attention_data['face_detected'].sum() / total_readings) * 100
            avg_blink_rate = attention_data['blink_rate'].mean()
            screen_looking_rate = (attention_data['looking_at_screen'].sum() / total_readings) * 100
            
            # Identify focus sessions (sustained attention periods)
            focus_sessions = self._identify_focus_sessions(attention_data)
            
            # Hourly attention pattern
            attention_data['hour'] = attention_data['timestamp'].dt.hour
            hourly_attention = attention_data.groupby('hour')['attention_score'].mean()
            attention_pattern = [
                {
                    'hour': hour, 
                    'avg_attention': hourly_attention.get(hour, 0),
                    'face_detection_rate': (
                        attention_data[attention_data['hour'] == hour]['face_detected'].mean() * 100
                        if hour in attention_data['hour'].values else 0
                    )
                } 
                for hour in range(24)
            ]
            
            return {
                'total_readings': total_readings,
                'avg_attention_score': avg_attention,
                'face_detection_rate': face_detection_rate,
                'avg_blink_rate': avg_blink_rate,
                'screen_looking_percentage': screen_looking_rate,
                'focus_sessions': focus_sessions,
                'attention_pattern': attention_pattern,
                'attention_variability': attention_data['attention_score'].std()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing attention data: {e}")
            return {}
    
    def _identify_focus_sessions(self, attention_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify sustained focus sessions from attention data"""
        try:
            if attention_data.empty:
                return []
            
            focus_threshold = 0.5  # Minimum attention score for focus
            min_duration = 5 * 60  # Minimum 5 minutes for a focus session
            
            # Sort by timestamp
            attention_data = attention_data.sort_values('timestamp')
            
            focus_sessions = []
            current_session = None
            
            for _, row in attention_data.iterrows():
                if row['attention_score'] >= focus_threshold and row['face_detected']:
                    if current_session is None:
                        # Start new session
                        current_session = {
                            'start_time': row['timestamp'],
                            'end_time': row['timestamp'],
                            'avg_attention': row['attention_score'],
                            'readings_count': 1,
                            'total_attention': row['attention_score']
                        }
                    else:
                        # Continue current session
                        current_session['end_time'] = row['timestamp']
                        current_session['readings_count'] += 1
                        current_session['total_attention'] += row['attention_score']
                        current_session['avg_attention'] = (
                            current_session['total_attention'] / current_session['readings_count']
                        )
                else:
                    # End current session if it meets minimum duration
                    if current_session is not None:
                        duration = (current_session['end_time'] - current_session['start_time']).total_seconds()
                        if duration >= min_duration:
                            current_session['duration_minutes'] = duration / 60
                            focus_sessions.append(current_session)
                        current_session = None
            
            # Handle final session
            if current_session is not None:
                duration = (current_session['end_time'] - current_session['start_time']).total_seconds()
                if duration >= min_duration:
                    current_session['duration_minutes'] = duration / 60
                    focus_sessions.append(current_session)
            
            return focus_sessions
            
        except Exception as e:
            self.logger.error(f"Error identifying focus sessions: {e}")
            return []
    
    def _calculate_productivity_metrics(self, keystroke_summary: Dict, 
                                      window_summary: Dict, 
                                      attention_summary: Dict) -> Dict[str, Any]:
        """Calculate comprehensive productivity metrics"""
        try:
            # Overall productivity score (0-100)
            productivity_components = []
            weights = []
            
            # Application usage productivity (40% weight)
            if 'productivity_ratio' in window_summary:
                productivity_components.append(window_summary['productivity_ratio'])
                weights.append(0.4)
            
            # Attention-based productivity (35% weight)
            if 'avg_attention_score' in attention_summary:
                attention_productivity = attention_summary['avg_attention_score'] * 100
                productivity_components.append(attention_productivity)
                weights.append(0.35)
            
            # Activity-based productivity (25% weight)
            if 'activity_percentage' in keystroke_summary:
                activity_productivity = keystroke_summary['activity_percentage']
                productivity_components.append(activity_productivity)
                weights.append(0.25)
            
            # Calculate weighted average
            if productivity_components and weights:
                total_weight = sum(weights)
                weighted_sum = sum(score * weight for score, weight in zip(productivity_components, weights))
                overall_productivity = weighted_sum / total_weight
            else:
                overall_productivity = 0.0
            
            # Focus quality score
            focus_quality = self._calculate_focus_quality(attention_summary, keystroke_summary)
            
            # Distraction level
            distraction_level = self._calculate_distraction_level(window_summary, attention_summary)
            
            # Efficiency metrics
            efficiency_metrics = self._calculate_efficiency_metrics(
                keystroke_summary, window_summary, attention_summary
            )
            
            return {
                'overall_productivity_score': overall_productivity,
                'focus_quality_score': focus_quality,
                'distraction_level': distraction_level,
                'efficiency_metrics': efficiency_metrics,
                'productivity_components': {
                    'application_productivity': window_summary.get('productivity_ratio', 0),
                    'attention_productivity': attention_summary.get('avg_attention_score', 0) * 100,
                    'activity_productivity': keystroke_summary.get('activity_percentage', 0)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating productivity metrics: {e}")
            return {}
    
    def _calculate_focus_quality(self, attention_summary: Dict, keystroke_summary: Dict) -> float:
        """Calculate focus quality score"""
        try:
            score_components = []
            
            # Attention consistency
            if 'attention_variability' in attention_summary:
                consistency_score = max(0, 100 - (attention_summary['attention_variability'] * 100))
                score_components.append(consistency_score)
            
            # Number of focus sessions
            if 'focus_sessions' in attention_summary:
                focus_sessions_count = len(attention_summary['focus_sessions'])
                sessions_score = min(100, focus_sessions_count * 20)  # 20 points per session, max 100
                score_components.append(sessions_score)
            
            # Average attention level
            if 'avg_attention_score' in attention_summary:
                attention_score = attention_summary['avg_attention_score'] * 100
                score_components.append(attention_score)
            
            return sum(score_components) / len(score_components) if score_components else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating focus quality: {e}")
            return 0.0
    
    def _calculate_distraction_level(self, window_summary: Dict, attention_summary: Dict) -> float:
        """Calculate distraction level (0-100, higher = more distracted)"""
        try:
            distraction_components = []
            
            # Entertainment app usage
            if 'distraction_apps_time' in window_summary and 'total_time_minutes' in window_summary:
                total_time = window_summary['total_time_minutes']
                if total_time > 0:
                    distraction_ratio = (window_summary['distraction_apps_time'] / total_time) * 100
                    distraction_components.append(distraction_ratio)
            
            # Context switches (frequent app switching)
            if 'context_switches' in window_summary and 'total_time_minutes' in window_summary:
                total_time = window_summary['total_time_minutes']
                if total_time > 0:
                    switches_per_hour = (window_summary['context_switches'] / total_time) * 60
                    switch_distraction = min(100, switches_per_hour * 2)  # 2 points per switch per hour
                    distraction_components.append(switch_distraction)
            
            # Attention gaps (periods of low attention)
            if 'face_detection_rate' in attention_summary:
                attention_gaps = 100 - attention_summary['face_detection_rate']
                distraction_components.append(attention_gaps)
            
            return sum(distraction_components) / len(distraction_components) if distraction_components else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating distraction level: {e}")
            return 0.0
    
    def _calculate_efficiency_metrics(self, keystroke_summary: Dict, 
                                    window_summary: Dict, 
                                    attention_summary: Dict) -> Dict[str, Any]:
        """Calculate various efficiency metrics"""
        try:
            metrics = {}
            
            # Typing efficiency
            if 'avg_typing_speed' in keystroke_summary and 'activity_percentage' in keystroke_summary:
                typing_efficiency = (
                    keystroke_summary['avg_typing_speed'] * 
                    (keystroke_summary['activity_percentage'] / 100)
                )
                metrics['typing_efficiency'] = typing_efficiency
            
            # App usage efficiency (time in productive apps vs total time)
            if ('productivity_apps_time' in window_summary and 
                'total_time_minutes' in window_summary and 
                window_summary['total_time_minutes'] > 0):
                
                app_efficiency = (
                    window_summary['productivity_apps_time'] / 
                    window_summary['total_time_minutes']
                ) * 100
                metrics['app_usage_efficiency'] = app_efficiency
            
            # Attention efficiency (sustained attention periods)
            if 'focus_sessions' in attention_summary:
                total_focus_time = sum(
                    session['duration_minutes'] 
                    for session in attention_summary['focus_sessions']
                )
                metrics['total_focus_time_minutes'] = total_focus_time
                metrics['focus_sessions_count'] = len(attention_summary['focus_sessions'])
                
                if attention_summary['focus_sessions']:
                    avg_focus_duration = total_focus_time / len(attention_summary['focus_sessions'])
                    metrics['avg_focus_session_duration'] = avg_focus_duration
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating efficiency metrics: {e}")
            return {}
    
    def _generate_insights(self, keystroke_summary: Dict, 
                          window_summary: Dict, 
                          attention_summary: Dict, 
                          productivity_metrics: Dict) -> List[str]:
        """Generate actionable insights and recommendations"""
        try:
            insights = []
            
            # Productivity insights
            overall_score = productivity_metrics.get('overall_productivity_score', 0)
            if overall_score < 40:
                insights.append("⚠️ Low overall productivity detected. Consider reducing distractions and taking regular breaks.")
            elif overall_score > 80:
                insights.append("🎉 Excellent productivity today! You maintained strong focus and used productive applications effectively.")
            
            # Typing insights
            avg_typing_speed = keystroke_summary.get('avg_typing_speed', 0)
            if avg_typing_speed > 0:
                if avg_typing_speed < 30:
                    insights.append("💡 Your typing speed is below average. Consider practicing to improve efficiency.")
                elif avg_typing_speed > 60:
                    insights.append("⚡ Great typing speed! This contributes to your overall productivity.")
            
            # Activity insights
            activity_percentage = keystroke_summary.get('activity_percentage', 0)
            if activity_percentage < 50:
                insights.append("😴 Low activity detected. You might benefit from more frequent breaks or task switching.")
            
            # Application usage insights
            productivity_ratio = window_summary.get('productivity_ratio', 0)
            if productivity_ratio < 60:
                insights.append("📱 Consider reducing time spent on non-productive applications to boost overall productivity.")
            
            distraction_time = window_summary.get('distraction_apps_time', 0)
            if distraction_time > 60:  # More than 1 hour
                insights.append(f"🎮 You spent {distraction_time:.0f} minutes on entertainment apps. Consider setting time limits.")
            
            # Attention insights
            avg_attention = attention_summary.get('avg_attention_score', 0)
            if avg_attention < 0.4:
                insights.append("👀 Low attention levels detected. Try minimizing distractions in your environment.")
            
            face_detection_rate = attention_summary.get('face_detection_rate', 0)
            if face_detection_rate < 70:
                insights.append("📷 You were away from your screen frequently. Consider if this affects your work flow.")
            
            # Focus session insights
            focus_sessions = attention_summary.get('focus_sessions', [])
            if len(focus_sessions) == 0:
                insights.append("🎯 No sustained focus sessions detected. Try the Pomodoro technique for better focus.")
            elif len(focus_sessions) > 5:
                insights.append("🔥 Great job on maintaining multiple focus sessions throughout the day!")
            
            # Context switching insights
            context_switches = window_summary.get('context_switches', 0)
            total_time = window_summary.get('total_time_minutes', 1)
            if context_switches / (total_time / 60) > 10:  # More than 10 switches per hour
                insights.append("🔄 High app switching detected. Try batching similar tasks to reduce context switching.")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return ["Unable to generate insights due to data processing error."]
    
    def get_weekly_trends(self, end_date: datetime = None) -> Dict[str, Any]:
        """Generate weekly productivity trends"""
        try:
            if not end_date:
                end_date = datetime.now()
            
            start_date = end_date - timedelta(days=6)  # Last 7 days
            
            weekly_data = []
            for i in range(7):
                current_date = start_date + timedelta(days=i)
                daily_summary = self.get_daily_summary(current_date)
                weekly_data.append({
                    'date': current_date.date(),
                    'productivity_score': daily_summary.get('productivity_metrics', {}).get('overall_productivity_score', 0),
                    'total_keystrokes': daily_summary.get('keystroke_summary', {}).get('total_keystrokes', 0),
                    'active_time': daily_summary.get('keystroke_summary', {}).get('active_time_minutes', 0),
                    'avg_attention': daily_summary.get('attention_summary', {}).get('avg_attention_score', 0),
                    'focus_sessions': len(daily_summary.get('attention_summary', {}).get('focus_sessions', []))
                })
            
            # Calculate trends
            productivity_trend = self._calculate_trend([d['productivity_score'] for d in weekly_data])
            attention_trend = self._calculate_trend([d['avg_attention'] for d in weekly_data])
            activity_trend = self._calculate_trend([d['active_time'] for d in weekly_data])
            
            return {
                'weekly_data': weekly_data,
                'trends': {
                    'productivity': productivity_trend,
                    'attention': attention_trend,
                    'activity': activity_trend
                },
                'week_start': start_date.date(),
                'week_end': end_date.date()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating weekly trends: {e}")
            return {}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values"""
        try:
            if len(values) < 2:
                return "insufficient_data"
            
            # Remove zero values for trend calculation
            non_zero_values = [v for v in values if v > 0]
            if len(non_zero_values) < 2:
                return "insufficient_data"
            
            # Simple linear trend
            x = list(range(len(non_zero_values)))
            slope = np.polyfit(x, non_zero_values, 1)[0]
            
            if slope > 0.1:
                return "improving"
            elif slope < -0.1:
                return "declining"
            else:
                return "stable"
                
        except Exception as e:
            self.logger.error(f"Error calculating trend: {e}")
            return "unknown"

if __name__ == "__main__":
    # Test the data processor
    processor = DataProcessor()
    
    # Get today's summary
    summary = processor.get_daily_summary()
    print("Daily Summary Generated:")
    print(f"Productivity Score: {summary.get('productivity_metrics', {}).get('overall_productivity_score', 0):.1f}%")
    print(f"Insights: {len(summary.get('insights', []))} recommendations")
    
    # Get weekly trends
    trends = processor.get_weekly_trends()
    print(f"\nWeekly Trends: {trends.get('trends', {})}")
