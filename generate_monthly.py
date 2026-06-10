import os
from dotenv import load_dotenv
load_dotenv()

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import calendar

print("Connecting to database...")
DB_PATH = os.getenv("DB_PATH", "/opt/study-tracker/study_data.db")
TRACKER_DIR = os.getenv("TRACKER_DIR", "/opt/study-tracker")
conn = sqlite3.connect(DB_PATH)
query = "SELECT session_date, duration_hrs FROM study_sessions"
df = pd.read_sql_query(query, conn)
conn.close()

if df.empty:
    print("No data found in the database!")
    exit()

print("Processing data...")
# Convert dates and sum up hours per day
df['session_date'] = pd.to_datetime(df['session_date'])
daily_hours = df.groupby('session_date')['duration_hrs'].sum().reset_index()

# Find unique Year-Month combinations that actually have study data
daily_hours['year_month'] = daily_hours['session_date'].dt.to_period('M')
active_months = daily_hours['year_month'].unique()

print(f"Found study data in {len(active_months)} different months. Generating heatmaps...\n")

# Loop through each active month and generate a separate image
for ym in active_months:
    year = ym.year
    month = ym.month
    month_name = calendar.month_name[month]

    # Create a complete blank calendar grid for this specific month
    num_days = calendar.monthrange(year, month)[1]
    dates = pd.date_range(start=f'{year}-{month}-01', end=f'{year}-{month}-{num_days}')
    month_df = pd.DataFrame({'session_date': dates})

    # Merge our actual study data into the blank month grid
    month_df = pd.merge(month_df, daily_hours, on='session_date', how='left').fillna({'duration_hrs': 0})

    # Calculate row (week of month) and column (day of week) for the matrix
    month_df['weekday'] = month_df['session_date'].dt.weekday  # 0=Mon, 6=Sun
    first_day_weekday = month_df['session_date'].dt.weekday.iloc[0]
    month_df['week_of_month'] = (month_df['session_date'].dt.day - 1 + first_day_weekday) // 7

    # Pivot the data into a grid shape (Weeks vs Days)
    pivot_table = month_df.pivot(index='week_of_month', columns='weekday', values='duration_hrs')
    
    # Ensure all 7 days of the week exist in the columns, even if blank
    for day in range(7):
        if day not in pivot_table.columns:
            pivot_table[day] = 0
    pivot_table = pivot_table.reindex(columns=range(7))
    pivot_table.columns = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # --- PLOTTING ---
    plt.figure(figsize=(10, 6))
    
    # Draw the heatmap (annot=True puts the hours text inside the boxes)
    ax = sns.heatmap(pivot_table, cmap='Greens', annot=True, fmt=".1f", 
                     linewidths=2, cbar_kws={'label': 'Hours Studied'})

    plt.title(f'KU Leuven Library Tracker - {month_name} {year}', fontsize=16, pad=20)
    
    # Hide the y-axis week numbers (they aren't useful visually)
    ax.set_yticks([])
    ax.set_ylabel('')
    ax.set_xlabel('')

    # Save the file
    output_file = f'{TRACKER_DIR}/study_heatmap_{year}_{month:02d}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved: {output_file}")

print("\nAll monthly heatmaps generated successfully!")
