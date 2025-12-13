"""
DeskBuddy Startup Script
This script helps you start DeskBuddy components easily.
"""

import argparse
import subprocess
import sys
import os
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'streamlit', 'cv2', 'mediapipe', 'pandas', 
        'numpy', 'plotly', 'psutil', 'pynput', 'sklearn'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install missing packages with:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def start_dashboard():
    """Start the Streamlit dashboard"""
    print("🚀 Starting DeskBuddy Dashboard...")
    dashboard_path = project_root / "src" / "dashboard" / "app.py"
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_path), 
            "--server.port", "8501",
            "--server.headless", "false"
        ], cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

def start_data_collection():
    """Start data collection in background"""
    print("📊 Starting Data Collection...")
    collector_path = project_root / "src" / "data_collection" / "data_collector.py"
    
    try:
        subprocess.run([sys.executable, str(collector_path)], cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 Data collection stopped")
    except Exception as e:
        print(f"❌ Error starting data collection: {e}")

def start_both():
    """Start both dashboard and data collection"""
    import threading
    
    print("🎯 Starting DeskBuddy (Dashboard + Data Collection)...")
    
    # Start data collection in background thread
    collection_thread = threading.Thread(target=start_data_collection, daemon=True)
    collection_thread.start()
    
    # Give data collection a moment to start
    time.sleep(2)
    
    # Start dashboard in main thread
    start_dashboard()

def show_status():
    """Show current status of DeskBuddy components"""
    print("📈 DeskBuddy Status")
    print("=" * 50)
    
    # Check database
    try:
        from src.data_processing.database_manager import DatabaseManager
        db = DatabaseManager()
        stats = db.get_productivity_stats()
        print(f"✅ Database: Connected ({len(stats)} records today)")
    except Exception as e:
        print(f"❌ Database: Error - {e}")
    
    # Check if data collection is running (simplified check)
    import psutil
    python_processes = [p for p in psutil.process_iter(['pid', 'name', 'cmdline']) 
                       if p.info['name'] and 'python' in p.info['name'].lower()]
    
    data_collection_running = False
    dashboard_running = False
    
    for proc in python_processes:
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'data_collector.py' in cmdline:
                data_collection_running = True
            if 'streamlit' in cmdline and 'app.py' in cmdline:
                dashboard_running = True
        except:
            continue
    
    print(f"{'✅' if data_collection_running else '❌'} Data Collection: {'Running' if data_collection_running else 'Stopped'}")
    print(f"{'✅' if dashboard_running else '❌'} Dashboard: {'Running' if dashboard_running else 'Stopped'}")
    
    if not data_collection_running and not dashboard_running:
        print("\n💡 Start DeskBuddy with: python run_deskbuddy.py --start")

def setup_environment():
    """Set up the DeskBuddy environment"""
    print("🔧 Setting up DeskBuddy environment...")
    
    # Create necessary directories
    directories = [
        project_root / "data",
        project_root / "logs", 
        project_root / "models"
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Initialize database
    try:
        from src.data_processing.database_manager import DatabaseManager
        db = DatabaseManager()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    print("🎉 Environment setup complete!")
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="DeskBuddy - AI-Powered Productivity Companion")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dashboard", action="store_true", help="Start only the dashboard")
    group.add_argument("--collect", action="store_true", help="Start only data collection")
    group.add_argument("--start", action="store_true", help="Start both dashboard and data collection")
    group.add_argument("--status", action="store_true", help="Show current status")
    group.add_argument("--setup", action="store_true", help="Set up environment")
    group.add_argument("--check", action="store_true", help="Check dependencies")
    
    args = parser.parse_args()
    
    print("🖥️  DeskBuddy - AI-Powered Productivity Companion")
    print("=" * 50)
    
    if args.check:
        check_dependencies()
    elif args.setup:
        if check_dependencies():
            setup_environment()
    elif args.status:
        show_status()
    elif args.dashboard:
        if check_dependencies():
            start_dashboard()
    elif args.collect:
        if check_dependencies():
            start_data_collection()
    elif args.start:
        if check_dependencies():
            start_both()
    else:
        print("Welcome to DeskBuddy! 🎯")
        print()
        print("Available commands:")
        print("  --check      Check if all dependencies are installed")
        print("  --setup      Set up the DeskBuddy environment")
        print("  --start      Start both dashboard and data collection")
        print("  --dashboard  Start only the Streamlit dashboard")
        print("  --collect    Start only data collection")
        print("  --status     Show current status")
        print()
        print("Quick start:")
        print("  1. python run_deskbuddy.py --check")
        print("  2. python run_deskbuddy.py --setup")
        print("  3. python run_deskbuddy.py --start")
        print()
        print("Then open your browser to: http://localhost:8501")

if __name__ == "__main__":
    main()
