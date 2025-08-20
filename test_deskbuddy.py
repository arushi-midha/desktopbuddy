#!/usr/bin/env python3
"""
DeskBuddy Test Script
Simple test to verify all components are working
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        # Core modules
        import streamlit
        import cv2
        import mediapipe
        import pandas
        import numpy
        import plotly
        import psutil
        import sklearn
        print("✅ All core modules imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    try:
        # Project modules
        from config.settings import DATABASE_PATH
        from src.data_processing.database_manager import DatabaseManager
        from src.data_collection.keystroke_logger import KeystrokeLogger
        from src.data_collection.window_tracker import WindowTracker
        from src.data_processing.data_processor import DataProcessor
        print("✅ All project modules imported successfully")
    except ImportError as e:
        print(f"❌ Project import error: {e}")
        return False
    
    return True

def test_database():
    """Test database functionality"""
    print("\n🗄️ Testing database...")
    
    try:
        from src.data_processing.database_manager import DatabaseManager
        
        db = DatabaseManager()
        
        # Test data insertion
        from datetime import datetime
        test_data = {
            'timestamp': datetime.now(),
            'typing_speed': 45.0,
            'key_count': 10,
            'active_window': 'Test Window',
            'is_active': True
        }
        
        db.insert_keystroke_data(test_data)
        
        # Test data retrieval
        data = db.get_keystroke_data()
        
        print(f"✅ Database test passed - {len(data)} records found")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_data_collection():
    """Test data collection components (without actually starting them)"""
    print("\n📊 Testing data collection components...")
    
    try:
        from src.data_collection.keystroke_logger import KeystrokeLogger
        from src.data_collection.window_tracker import WindowTracker
        from src.data_collection.webcam_monitor import WebcamMonitor
        
        # Just test initialization
        keystroke_logger = KeystrokeLogger()
        window_tracker = WindowTracker()
        
        # Don't start webcam for testing
        print("✅ Keystroke logger initialized")
        print("✅ Window tracker initialized")
        print("⚠️ Webcam monitor not tested (requires camera)")
        
        return True
        
    except Exception as e:
        print(f"❌ Data collection test failed: {e}")
        return False

def test_data_processing():
    """Test data processing functionality"""
    print("\n🔬 Testing data processing...")
    
    try:
        from src.data_processing.data_processor import DataProcessor
        
        processor = DataProcessor()
        
        # Test with minimal data
        summary = processor.get_daily_summary()
        
        print("✅ Data processor initialized")
        print(f"✅ Daily summary generated: {type(summary)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data processing test failed: {e}")
        return False

def test_ml_models():
    """Test ML model functionality"""
    print("\n🤖 Testing ML models...")
    
    try:
        from src.models.productivity_analyzer import ProductivityAnalyzer
        
        analyzer = ProductivityAnalyzer()
        
        # Test feature preparation (may not have data)
        features, targets = analyzer.prepare_training_data(days_back=1)
        
        print("✅ Productivity analyzer initialized")
        print(f"✅ Feature preparation works: {len(features)} samples")
        
        return True
        
    except Exception as e:
        print(f"❌ ML model test failed: {e}")
        return False

def test_dashboard_components():
    """Test dashboard components"""
    print("\n📊 Testing dashboard components...")
    
    try:
        from src.dashboard.utils.chart_helpers import create_productivity_gauge
        
        # Test chart creation
        fig = create_productivity_gauge(75.0)
        
        print("✅ Chart helpers work")
        print("✅ Dashboard components initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🖥️  DeskBuddy System Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database,
        test_data_collection,
        test_data_processing,
        test_ml_models,
        test_dashboard_components
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! DeskBuddy is ready to use.")
        print("\nNext steps:")
        print("1. python run_deskbuddy.py --start")
        print("2. Open http://localhost:8501 in your browser")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")
        print("\nTroubleshooting:")
        print("1. Run: python run_deskbuddy.py --check")
        print("2. Run: python run_deskbuddy.py --setup")
        print("3. Check INSTALL.md for detailed instructions")

if __name__ == "__main__":
    main()
