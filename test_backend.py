import requests
import sys
import time
import subprocess
import os

def test_backend():
    print("Starting backend server for testing...")
    # Start the server in a subprocess
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd()
    )
    
    try:
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(5)
        
        # Test root endpoint
        print("\nTesting root endpoint...")
        try:
            response = requests.get("http://127.0.0.1:8000/")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            if response.status_code == 200:
                print("✅ Root endpoint working")
            else:
                print("❌ Root endpoint failed")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            
        # Test system status
        print("\nTesting system status endpoint...")
        try:
            response = requests.get("http://127.0.0.1:8000/api/system/status")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            if response.status_code == 200:
                print("✅ System status endpoint working")
            else:
                print("❌ System status endpoint failed")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")

    finally:
        print("\nStopping server...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_backend()
