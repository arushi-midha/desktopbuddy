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

#### Get Weekly Trends
Get trend analysis for the week ending on the specified date.

- **Endpoint**: `/api/analytics/weekly`
- **Method**: `GET`
- **Parameters**:
    - `end_date` (optional): Defaults to current time if not provided.
- **Response**: Object containing weekly trend data and charts.

#### Get Productivity Stats
Get high-level productivity metrics for a specific date.

- **Endpoint**: `/api/analytics/productivity/stats`
- **Method**: `GET`
- **Parameters**:
    - `date` (optional)
- **Response**: Object with aggregated stats (total keystrokes, avg attention, etc.).

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
