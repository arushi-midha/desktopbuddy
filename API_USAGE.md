# DeskBuddy API Usage Manual

This document provides instructions for frontend developers on how to interact with the DeskBuddy FastAPI backend.

## Base URL

The backend server runs on:
`http://localhost:8000`

## Authentication

Currently, the API does not require authentication.

## Endpoints

### 1. Activity Data

#### Get Keystroke Logs
Fetch raw keystroke activity logs.

- **Endpoint**: `/api/activity/keystrokes`
- **Method**: `GET`
- **Parameters**:
    - `start_date` (optional): ISO 8601 datetime string (e.g., `2023-10-27T00:00:00`)
    - `end_date` (optional): ISO 8601 datetime string
- **Response**: Array of `KeystrokeLog` objects
    ```json
    [
        {
            "id": 1,
            "timestamp": "2023-10-27T10:00:00",
            "typing_speed": 45.5,
            "key_count": 120,
            "active_window": "Visual Studio Code",
            "is_active": true
        }
    ]
    ```

#### Get Window Activity
Fetch window usage logs.

- **Endpoint**: `/api/activity/windows`
- **Method**: `GET`
- **Parameters**:
    - `start_date` (optional)
    - `end_date` (optional)
- **Response**: Array of `WindowActivity` objects
    ```json
    [
        {
            "id": 1,
            "timestamp": "2023-10-27T10:05:00",
            "window_title": "main.py - DeskBuddy",
            "application_name": "Code",
            "category": "productivity",
            "duration_seconds": 300.0
        }
    ]
    ```

#### Get Application Usage Stats
Get aggregated usage statistics per application.

- **Endpoint**: `/api/activity/app-usage`
- **Method**: `GET`
- **Parameters**:
    - `start_date` (optional)
    - `end_date` (optional)
- **Response**: Array of `AppUsageStats` objects
    ```json
    [
        {
            "application_name": "Code",
            "category": "productivity",
            "total_duration": 3600.0,
            "session_count": 12
        }
    ]
    ```

### 2. Attention Data

#### Get Attention Logs
Fetch raw webcam attention data.

- **Endpoint**: `/api/attention/logs`
- **Method**: `GET`
- **Parameters**:
    - `start_date` (optional)
    - `end_date` (optional)
- **Response**: Array of `AttentionData` objects
    ```json
    [
        {
            "id": 1,
            "timestamp": "2023-10-27T10:00:00",
            "face_detected": true,
            "attention_score": 0.85,
            "blink_rate": 12.5,
            "looking_at_screen": true
        }
    ]
    ```

### 3. Analytics

#### Get Daily Analysis
Get a detailed summary for a specific day.

- **Endpoint**: `/api/analytics/daily/{date}`
- **Method**: `GET`
- **Path Parameters**:
    - `date`: ISO 8601 datetime string (e.g., `2023-10-27T00:00:00`)
- **Response**: `DailySummary` object containing nested summaries for keystrokes, windows, and attention.
    ```json
    {
        "date": "2025-12-14",
        "keystroke_summary": {
            "total_keystrokes": 185,
            "avg_typing_speed": 5.168,
            "active_time_minutes": 4.16,
            "activity_percentage": 100.0,
            "avg_error_rate": 12.43,
            "rhythm_variability": 0.60,
            "avg_pause_duration": 51.55,
            "long_pauses_count": 1,
            "stress_score": 0.72,
            "productivity_score": 0.60
        },
        "window_summary": {
            "total_applications": 1,
            "total_time_minutes": 4.38,
            "app_usage": {
                "Unknown": 4.38
            },
            "category_breakdown": {
                "productivity": 4.17,
                "other": 0.20
            },
            "most_used_app": "Unknown",
            "productivity_apps_time": 4.17,
            "distraction_apps_time": 0.0,
            "context_switches": 9,
            "switch_rate_per_hour": 123.0,
            "avg_dwell_time_minutes": 0.43,
            "productivity_ratio": 95.23
        },
        "attention_summary": {},
        "mouse_summary": {
            "total_clicks": 41,
            "total_scrolls": 0,
            "total_distance_px": 34817.46,
            "avg_velocity_px_s": 269.57,
            "idle_ratio_percent": 60.82,
            "doomscrolling_detected": false
        },
        "productivity_metrics": {
            "overall_productivity_score": 85.78,
            "stress_metrics": {
                "stress_level": "High",
                "error_rate": 12.43
            },
            "productivity_components": {
                "application_productivity": 95.23,
                "activity_productivity": 100.0
            }
        },
        "insights": [
            "🎉 Excellent productivity today!",
            "💡 Your typing speed is below average.",
            "🔄 High app switching detected."
        ],
        "generated_at": "2025-12-14T04:00:34.857060"
    }
    ```

#### Get Weekly Trends
Get trend analysis for the week ending on the specified date.

- **Endpoint**: `/api/analytics/weekly`
- **Method**: `GET`
- **Parameters**:
    - `end_date` (optional): Defaults to current time if not provided.
- **Response**: Object containing weekly trend data and charts.
    ```json
    {
        "weekly_data": [
            {
                "date": "2025-12-08",
                "productivity_score": 0.0,
                "total_keystrokes": 0
            },
            {
                "date": "2025-12-14",
                "productivity_score": 85.78,
                "total_keystrokes": 185
            }
        ],
        "trends": {
            "productivity": "improving",
            "attention": "insufficient_data",
            "activity": "improving"
        },
        "week_start": "2025-12-08",
        "week_end": "2025-12-14"
    }
    ```

#### Get Productivity Stats
Get high-level productivity metrics for a specific date.

- **Endpoint**: `/api/analytics/productivity/stats`
- **Method**: `GET`
- **Parameters**:
    - `date` (optional)
- **Response**: Object with aggregated stats (total keystrokes, avg attention, etc.).
    ```json
    {
        "date": "2023-10-27",
        "total_keystrokes": 5432,
        "avg_typing_speed": 62.1,
        "active_periods": 45,
        "avg_attention": 0.78,
        "avg_blink_rate": 14.2,
        "face_detection_rate": 0.95
    }
    ```

### 4. System

#### Check Status
Check if the backend and data collection services are running.

- **Endpoint**: `/api/system/status`
- **Method**: `GET`
- **Response**:
    ```json
    {
        "status": "online",
        "processes": {
            "data_collector": true,
            "keystroke_logger": true,
            "window_tracker": true,
            "webcam_monitor": true
        }
    }
    ```

## Interactive Documentation

For interactive testing and detailed schema information, visit the Swagger UI at:
`http://localhost:8000/docs`
