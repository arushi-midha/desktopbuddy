# DeskBuddy Installation Guide

## Quick Setup (Recommended)

1. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment**
   ```bash
   python run_deskbuddy.py --setup
   ```

3. **Start DeskBuddy**
   ```bash
   python run_deskbuddy.py --start
   ```

4. **Open Dashboard**
   - Open your browser to: http://localhost:8501

## Manual Installation

### Prerequisites
- Python 3.8 or higher
- Webcam (optional, for attention tracking)
- Windows/Mac/Linux

### Step 1: Install Dependencies

```bash
pip install streamlit opencv-python mediapipe pandas numpy matplotlib seaborn plotly psutil pynput Pillow scipy scikit-learn pyautogui joblib
```

**For Windows users, also install:**
```bash
pip install pywin32
```

### Step 2: Initialize Database

```bash
python src/data_processing/database_manager.py
```

### Step 3: Start Components

**Option A: Start Everything Together**
```bash
python run_deskbuddy.py --start
```

**Option B: Start Components Separately**

Terminal 1 (Data Collection):
```bash
python src/data_collection/data_collector.py
```

Terminal 2 (Dashboard):
```bash
streamlit run src/dashboard/app.py
```

## Configuration

### Privacy Settings
- Edit `config/settings.py` to adjust privacy settings
- Set `STORE_FACIAL_IMAGES = False` to only store metadata
- Adjust `DATA_RETENTION_DAYS` for automatic cleanup

### Data Collection Settings
- Modify collection intervals in `config/settings.py`
- Disable specific collectors with command-line flags:
  ```bash
  python src/data_collection/data_collector.py --no-webcam --no-keystroke
  ```

## Troubleshooting

### Common Issues

**1. ModuleNotFoundError**
```bash
python run_deskbuddy.py --check
```
This will tell you which packages are missing.

**2. Webcam Access Issues**
- Check if other applications are using the webcam
- Grant camera permissions to Python/Terminal
- Try running without webcam: `--no-webcam`

**3. Permission Errors (macOS/Linux)**
- You may need to grant accessibility permissions
- Go to System Preferences > Security & Privacy > Privacy > Accessibility
- Add Terminal or Python to the list

**4. Database Errors**
```bash
python run_deskbuddy.py --setup
```
This will reinitialize the database.

**5. Port Already in Use**
```bash
streamlit run src/dashboard/app.py --server.port 8502
```
Change the port number if 8501 is busy.

### Performance Optimization

**For better performance:**
- Close unnecessary applications
- Ensure good lighting for webcam tracking
- Use an external webcam for better face detection

**For privacy:**
- Set `ANONYMIZE_DATA = True` in config
- Disable webcam monitoring if not needed
- Adjust data retention period

## Development Setup

**For development and testing:**

1. **Install development dependencies**
   ```bash
   pip install pytest pytest-cov black flake8 mypy
   ```

2. **Run tests** (when available)
   ```bash
   pytest tests/
   ```

3. **Code formatting**
   ```bash
   black src/
   ```

## System Requirements

### Minimum:
- RAM: 4GB
- Storage: 1GB free space
- CPU: Dual-core 2GHz+
- Python 3.8+

### Recommended:
- RAM: 8GB+
- Storage: 2GB+ free space
- CPU: Quad-core 2.5GHz+
- Webcam: 720p or higher
- Python 3.9+

## Security Considerations

- All data is stored locally in SQLite database
- No external data transmission by default
- Facial analysis uses MediaPipe (runs locally)
- Keystroke data is aggregated (not individual keys)
- Application usage tracking for productivity analysis only

## Uninstallation

To remove DeskBuddy:

1. **Stop all processes**
   ```bash
   python run_deskbuddy.py --status
   ```
   Then stop any running processes.

2. **Remove data** (optional)
   ```bash
   rm -rf data/ logs/ models/
   ```

3. **Uninstall Python packages** (optional)
   ```bash
   pip uninstall streamlit opencv-python mediapipe pandas numpy matplotlib seaborn plotly psutil pynput Pillow scipy scikit-learn pyautogui joblib
   ```

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review logs in the `logs/` directory
3. Check the dashboard status page
4. Submit issues on GitHub (if applicable)

## License

MIT License - See LICENSE file for details.
