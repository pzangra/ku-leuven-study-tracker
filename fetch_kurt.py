import os
import requests
from icalendar import Calendar
import sqlite3
import datetime
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Retrieve variables from environment
ICS_URL = os.getenv("ICS_URL")
USER_AGENT = os.getenv("USER_AGENT")
HTTP_ACCEPT = os.getenv("HTTP_ACCEPT")
HTTP_ACCEPT_ENCODING = os.getenv("HTTP_ACCEPT_ENCODING")
HTTP_CONNECTION = os.getenv("HTTP_CONNECTION")
DB_PATH = os.getenv("DB_PATH", "/opt/study-tracker/study_data.db")

# Fail early if critical configurations are missing
if not ICS_URL:
    print("Error: ICS_URL missing from environment variables.")
    exit(1)

if ICS_URL.startswith('webcal://'):
    # Fix webcal scheme if present
    ICS_URL = ICS_URL.replace('webcal://', 'https://')

print("Downloading calendar data...")

# Reconstruct headers dynamically from your .env variables
headers = {
    'User-Agent': USER_AGENT,
    'Accept': HTTP_ACCEPT,
    'Accept-Encoding': HTTP_ACCEPT_ENCODING,
    'Connection': HTTP_CONNECTION
}

try:
    response = requests.get(ICS_URL, headers=headers, allow_redirects=True)
    response.raise_for_status()
except Exception as e:
    print(f"Error downloading calendar: {e}")
    exit(1)

# Parse the downloaded calendar
cal = Calendar.from_ical(response.content)

# Connect to SQLite using the path from environment
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check existence of table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS study_sessions (
        event_id TEXT PRIMARY KEY,
        session_date TEXT,
        start_time TEXT,
        end_time TEXT,
        duration_hrs REAL,
        location TEXT,
        subject TEXT
    )
''')

inserted_count = 0

# Parse and extract bookings
for component in cal.walk('vevent'):
    subject = component.get('summary')
    subject_str = str(subject).upper() if subject else ""
    
    # 1. Check if it's a library booking
    is_booking = any(keyword in subject_str for keyword in ['SEAT', 'AGORA', 'RBIB', 'KURT', 'RESERVATION'])
    
    # 2. Check if it was cancelled
    is_cancelled = 'CANCELLED' in subject_str
    
    if is_booking and not is_cancelled:
        start = component.get('dtstart').dt
        end = component.get('dtend').dt
        raw_loc = component.get('location', '')
        location = str(raw_loc).strip() if str(raw_loc).strip() else 'Unknown Library'
        event_id = str(component.get('uid'))
        
        if isinstance(start, datetime.datetime) and isinstance(end, datetime.datetime):
            duration_delta = end - start
            duration_hours = round(duration_delta.total_seconds() / 3600, 2)
            
            cursor.execute('''
                INSERT OR REPLACE INTO study_sessions 
                (event_id, session_date, start_time, end_time, duration_hrs, location, subject)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_id, str(start.date()), str(start.time()), str(end.time()), duration_hours, location, str(subject)
            ))
            inserted_count += 1

conn.commit()

# Clean up accidental entries
cursor.execute("DELETE FROM study_sessions WHERE subject LIKE '%CANCELLED%'")
conn.commit()
conn.close()

print(f"Successfully synced {inserted_count} valid study sessions to the SQLite database!")
