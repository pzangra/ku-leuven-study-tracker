import os
from dotenv import load_dotenv
load_dotenv()
import sqlite3
import pandas as pd

print("Connecting to database...")
DB_PATH = os.getenv("DB_PATH", "/opt/study-tracker/study_data.db")
conn = sqlite3.connect(DB_PATH)
# Query raw logs
query = "SELECT session_date, duration_hrs, location FROM study_sessions"
df = pd.read_sql_query(query, conn)
conn.close()

if df.empty:
    print("No data found in the database!")
    exit()

# Process datetime dimensions
df['session_date'] = pd.to_datetime(df['session_date'])
df['Year'] = df['session_date'].dt.year
df['Month_Num'] = df['session_date'].dt.month
df['Month_Name'] = df['session_date'].dt.strftime('%B')

# ISO calendar week handles year transitions perfectly
df['Week_Number'] = df['session_date'].dt.isocalendar().week

# Group data by Month and Week
weekly_grouped = df.groupby(['Year', 'Month_Num', 'Month_Name', 'Week_Number']).agg(
    Total_Hours=('duration_hrs', 'sum'),
    Total_Sessions=('duration_hrs', 'count'),
    Avg_Hours_Per_Session=('duration_hrs', 'mean')
).reset_index().sort_values(by=['Year', 'Month_Num', 'Week_Number'])

# Display the dashboard
print("\n=============================================")
print("        WEEK-BY-WEEK STUDY STATISTICS        ")
print("=============================================\n")

current_month = ""
for _, row in weekly_grouped.iterrows():
    if current_month != row['Month_Name']:
        current_month = row['Month_Name']
        print(f"\n{current_month.upper()} {int(row['Year'])}")
        print("-" * 45)
        
    print(f"  Week {int(row['Week_Number'])}:")
    print(f"    • Total Time Spent : {row['Total_Hours']:.1f} hours")
    print(f"    • Active Sessions  : {int(row['Total_Sessions'])} library visits")
    print(f"    • Average Pace     : {row['Avg_Hours_Per_Session']:.1f} hours/visit")
    print()
