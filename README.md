# DeskBuddy - AI-Powered Personal Productivity Companion

DeskBuddy is an AI-powered personal productivity companion designed to help individuals maintain focus, monitor work patterns, and improve digital well-being while working at their computers.

## Features

- **Multimodal Data Collection**: Keystroke dynamics, facial engagement cues, and application usage patterns
- **Real-time Dashboard**: Streamlit-based interface for productivity visualization
- **Cognitive Load Monitoring**: Track typing activity, application usage, and attention patterns
- **Privacy-First Design**: All data stored locally with secure handling

## Project Structure

```
deskbuddy/
├── src/
│   ├── data_collection/
│   │   ├── keystroke_logger.py      # Keystroke tracking
│   │   ├── window_tracker.py        # Application usage monitoring
│   │   ├── webcam_monitor.py        # Facial analysis and attention tracking
│   │   └── data_collector.py        # Unified data collection orchestrator
│   ├── data_processing/
│   │   ├── data_processor.py        # Data preprocessing and analysis
│   │   └── database_manager.py      # SQLite database management
│   ├── models/
│   │   └── productivity_analyzer.py # ML models for productivity insights
│   └── dashboard/
│       ├── app.py                   # Main Streamlit application
│       ├── components/
│       │   ├── activity_charts.py   # Activity visualization components
│       │   ├── attention_charts.py  # Attention tracking visualizations
│       │   └── productivity_metrics.py # Productivity metrics display
│       └── utils/
│           └── chart_helpers.py     # Utility functions for charts
├── data/
│   └── deskbuddy.db                # SQLite database (created automatically)
├── logs/
│   └── app.log                     # Application logs
├── config/
│   └── settings.py                 # Configuration settings
├── requirements.txt
├── setup.py
└── README.md
```

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   streamlit run src/dashboard/app.py
   ```

3. **Start Data Collection**:
   ```bash
   python src/data_collection/data_collector.py
   ```

## Current Objectives

### 1. Basic Cognitive Load Indicators
- [x] Keystroke logging for typing activity tracking
- [x] Window/application usage tracking
- [x] Webcam-based facial analysis for attention monitoring
- [x] Blink rate and eye movement tracking
- [x] Secure multimodal data storage

### 2. Streamlit Prototype Dashboard
- [x] Daily typing activity visualization
- [x] Application usage time tracking
- [x] Webcam attention summary
- [x] Interactive data visualizations

### 3. Backend Data Pipeline
- [x] Continuous logging system
- [x] Unified SQLite storage
- [x] Modular architecture for future expansion

## Privacy & Security

- All data is stored locally on your machine
- No external data transmission
- User consent required for webcam access
- Configurable data retention policies

## Future Enhancements

- Sentiment detection
- Posture monitoring
- Advanced productivity analytics
- Personalized recommendations
- Break reminders and wellness features

## License

MIT License - See LICENSE file for details
