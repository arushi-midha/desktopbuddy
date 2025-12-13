import sqlite3
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())
from config.settings import DATABASE_PATH

def check_data():
    print(f"Checking database at: {DATABASE_PATH}")
    
    if not os.path.exists(DATABASE_PATH):
        print("❌ Database file not found!")
        return

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        tables = ['keystroke_activity', 'window_activity', 'attention_data']
        
        for table in tables:
            print(f"\n--- {table} ---")
            
            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Total rows: {count}")
            
            if count > 0:
                # Get date range
                cursor.execute(f"SELECT MIN(timestamp), MAX(timestamp) FROM {table}")
                min_ts, max_ts = cursor.fetchone()
                print(f"Date range: {min_ts} to {max_ts}")
                
                # Check if any data from today
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE date(timestamp) = date('now', 'localtime')")
                today_count = cursor.fetchone()[0]
                print(f"Rows from today ({today}): {today_count}")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")

if __name__ == "__main__":
    check_data()
