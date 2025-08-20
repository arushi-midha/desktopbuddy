# DeskBuddy Project Structure

## Overview
```
deskbuddy/
├── 📁 src/                              # Source code
│   ├── 📁 data_collection/              # Data collection modules
│   │   ├── 🐍 keystroke_logger.py       # Keystroke activity tracking
│   │   ├── 🐍 window_tracker.py         # Application usage monitoring
│   │   ├── 🐍 webcam_monitor.py         # Facial analysis & attention tracking
│   │   └── 🐍 data_collector.py         # Unified data collection orchestrator
│   ├── 📁 data_processing/              # Data processing & analysis
│   │   ├── 🐍 database_manager.py       # SQLite database operations
│   │   └── 🐍 data_processor.py         # Data analysis & insights generation
│   ├── 📁 models/                       # Machine learning models
│   │   └── 🐍 productivity_analyzer.py  # ML-based productivity prediction
│   └── 📁 dashboard/                    # Streamlit dashboard
│       ├── 🐍 app.py                    # Main dashboard application
│       ├── 📁 components/               # Dashboard components
│       └── 📁 utils/                    # Utility functions
│           └── 🐍 chart_helpers.py      # Visualization helpers
├── 📁 config/                           # Configuration
│   └── 🐍 settings.py                   # Application settings
├── 📁 data/                             # Data storage
│   └── 🗄️ deskbuddy.db                  # SQLite database (auto-created)
├── 📁 logs/                             # Application logs
│   └── 📄 app.log                       # Log files (auto-created)
├── 📁 models/                           # Trained ML models
│   └── 📄 *.pkl                         # Saved model files (auto-created)
├── 📄 requirements.txt                  # Python dependencies
├── 📄 setup.py                          # Package installation
├── 📄 README.md                         # Project documentation
├── 📄 INSTALL.md                        # Installation guide
├── 🐍 run_deskbuddy.py                  # Main startup script
└── 🐍 test_deskbuddy.py                 # System test script
```

## Component Description

### 🔄 Data Collection (`src/data_collection/`)
- **keystroke_logger.py**: Monitors typing activity, speed, and patterns
- **window_tracker.py**: Tracks application usage and context switching
- **webcam_monitor.py**: Analyzes facial expressions and attention levels
- **data_collector.py**: Orchestrates all data collection in unified manner

### 🔬 Data Processing (`src/data_processing/`)
- **database_manager.py**: Handles all database operations (SQLite)
- **data_processor.py**: Processes raw data into insights and metrics

### 🤖 Machine Learning (`src/models/`)
- **productivity_analyzer.py**: Trains and uses ML models for productivity prediction

### 📊 Dashboard (`src/dashboard/`)
- **app.py**: Main Streamlit application with multiple pages
- **utils/chart_helpers.py**: Visualization utilities and chart creation

### ⚙️ Configuration (`config/`)
- **settings.py**: All application settings and configurations

## Key Features Implemented

### ✅ Objective 1: Basic Cognitive Load Indicators
- [x] Keystroke logging with typing speed analysis
- [x] Window/application usage tracking with categorization
- [x] Webcam-based facial analysis using MediaPipe
- [x] Blink rate and eye movement tracking
- [x] Secure multimodal data storage in SQLite

### ✅ Objective 2: Streamlit Prototype Dashboard
- [x] Real-time dashboard with auto-refresh
- [x] Daily typing activity visualization
- [x] Application usage time tracking and pie charts
- [x] Webcam attention summary with attention scores
- [x] Interactive data visualizations using Plotly
- [x] Daily and weekly analysis pages

### ✅ Objective 3: Backend Data Pipeline
- [x] Continuous logging of keystrokes, windows, and webcam data
- [x] Unified SQLite storage with proper schema
- [x] Modular architecture for easy feature additions
- [x] Data processing pipeline with insights generation
- [x] ML-based productivity analysis and prediction

## Additional Features Included

### 🔒 Privacy & Security
- Local data storage only (no external transmission)
- Configurable data retention policies
- Optional anonymization features
- User consent for webcam access

### 🎯 Advanced Analytics
- Productivity score calculation using multiple metrics
- Focus session detection and analysis
- Application categorization (productivity, entertainment, etc.)
- Trend analysis and weekly reports
- Personalized insights and recommendations

### 🛠️ Usability Features
- Easy startup script (`run_deskbuddy.py`)
- Comprehensive installation guide
- System test script for troubleshooting
- Configurable collection intervals and thresholds
- Export functionality for data analysis

### 📈 Machine Learning
- Random Forest models for productivity prediction
- Feature importance analysis
- Automatic model retraining with new data
- Prediction of productivity and focus quality

## Data Flow

```
Input Sources → Data Collection → Database → Processing → Dashboard
     ↓              ↓               ↓          ↓          ↓
🎥 Webcam      → webcam_monitor → SQLite → data_processor → Streamlit
⌨️ Keyboard    → keystroke_logger →   ↓         ↓            ↓
🖱️ Mouse       → window_tracker   →   ↓         ↓       📊 Charts
🪟 Windows     →      ↓          →   ↓         ↓       📈 Insights
                     ↓          →   ↓    → ML Models → 🎯 Predictions
                data_collector →   ↓         ↓
                     ↓          → Database → Export
```

## Quick Start Commands

```bash
# 1. Check dependencies
python run_deskbuddy.py --check

# 2. Set up environment
python run_deskbuddy.py --setup

# 3. Test system
python test_deskbuddy.py

# 4. Start application
python run_deskbuddy.py --start

# 5. Open dashboard
# Browser: http://localhost:8501
```

## Extensibility

The modular architecture allows easy addition of:
- New data collectors (posture, sentiment, etc.)
- Additional ML models
- More dashboard visualizations
- External integrations
- Advanced productivity features

## Technology Stack

- **Backend**: Python 3.8+
- **Database**: SQLite
- **ML**: scikit-learn, Random Forest
- **Computer Vision**: OpenCV, MediaPipe
- **Dashboard**: Streamlit, Plotly
- **Data Processing**: Pandas, NumPy
- **System Monitoring**: psutil, pynput
