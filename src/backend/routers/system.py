from fastapi import APIRouter
import psutil

router = APIRouter(
    prefix="/api/system",
    tags=["system"]
)

@router.get("/status")
async def get_system_status():
    """Check system status and running processes"""
    # Check if data collection processes are running
    # This is a basic check looking for python processes with specific names
    processes = {
        "data_collector": False,
        "keystroke_logger": False,
        "window_tracker": False,
        "webcam_monitor": False
    }
    
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and 'python' in cmdline[0]:
                cmd_str = ' '.join(cmdline)
                if 'data_collector.py' in cmd_str:
                    processes['data_collector'] = True
                elif 'keystroke_logger.py' in cmd_str:
                    processes['keystroke_logger'] = True
                elif 'window_tracker.py' in cmd_str:
                    processes['window_tracker'] = True
                elif 'webcam_monitor.py' in cmd_str:
                    processes['webcam_monitor'] = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    return {
        "status": "online",
        "processes": processes
    }
