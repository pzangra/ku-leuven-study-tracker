import os
import sqlite3
import pandas as pd
import calplot
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_PATH = os.getenv("DB_PATH", "/opt/study-tracker/study_data.db")
HEATMAP_PATH = os.getenv("HEATMAP_PATH", "/opt/study-tracker/study_heatmap.png")

print("Connecting to database...")
conn = sqlite3.connect(DB_PATH)

# Query the dates and study durations from SQLite
query = "SELECT session_date, duration_hrs FROM study_sessions"
df = pd.read_sql_query(query, conn)
conn.close()

if df.empty:
    print("No data found in the database! Go book some KURT sessions.")
    exit()

print("Processing data...")
df['session_date'] = pd.to_datetime(df['session_date'])

# Group by date and sum hours
daily_hours = df.groupby('session_date')['duration_hrs'].sum()

# Reindex to fill empty days with 0s
all_days = pd.date_range(start=daily_hours.index.min(), end=daily_hours.index.max())
daily_hours = daily_hours.reindex(all_days, fill_value=0)

print("Generating GitHub-style heatmap...")
fig, axes = calplot.calplot(
    daily_hours,
    cmap='Greens',
    edgecolor='white',
    linewidth=1,
    yearlabels=True,
    suptitle='KU Leuven Study Tracker (Hours)',
    figsize=(12, 4)
)

# Save the image using path from environment
plt.savefig(HEATMAP_PATH, dpi=300, bbox_inches='tight')
print(f"Success! Heatmap saved to: {HEATMAP_PATH}")
