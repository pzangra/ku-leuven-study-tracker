import os
from dotenv import load_dotenv
load_dotenv()
import sqlite3
import pandas as pd
import json

# 1. Connect to SQLite and fetch data
DB_PATH = os.getenv("DB_PATH", "/opt/study-tracker/study_data.db")
DASHBOARD_PATH = os.getenv("DASHBOARD_PATH", "/opt/study-tracker/dashboard.html")
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT session_date, duration_hrs, location, subject FROM study_sessions", conn)
conn.close()

if df.empty:
    print("No data found to build the dashboard!")
    exit()

# 2. Process DateTime elements
df['session_date'] = pd.to_datetime(df['session_date'])
df['date_str'] = df['session_date'].dt.strftime('%Y-%m-%d')
df['year'] = df['session_date'].dt.year
df['month_name'] = df['session_date'].dt.strftime('%B')
df['week_num'] = df['session_date'].dt.isocalendar().week

# Aggregate daily records
daily_summary = df.groupby('date_str')['duration_hrs'].sum().to_dict()

# Aggregate weekly statistics
weekly_stats = df.groupby(['year', 'month_name', 'week_num']).agg(
    total_hours=('duration_hrs', 'sum'),
    sessions=('duration_hrs', 'count')
).reset_index()
weekly_stats['avg_hours'] = (weekly_stats['total_hours'] / weekly_stats['sessions']).round(1)
weekly_stats_list = weekly_stats.to_dict(orient='records')

# 3. Create the HTML + JavaScript Dashboard String
html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>KU Leuven Study Tracker Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; background: #f6f8fa; color: #24292f; margin: 30px; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{ border-bottom: 1px solid #d0d7de; padding-bottom: 10px; }}
        .card {{ background: white; border: 1px solid #d0d7de; border-radius: 6px; padding: 20px; margin-bottom: 25px; }}
        .card h2 {{ margin-top: 0; font-size: 18px; }}
        
        /* 1. Year Grid Styles */
        .year-grid {{ display: grid; grid-template-flow: column; grid-template-columns: repeat(53, 12px); grid-template-rows: repeat(7, 12px); gap: 2px; overflow-x: auto; padding: 10px 0; }}
        .day-cell {{ width: 12px; height: 12px; border-radius: 2px; background-color: #ebedf0; }}
        .level-1 {{ background-color: #9be9a8; }}
        .level-2 {{ background-color: #40c463; }}
        .level-3 {{ background-color: #30a14e; }}
        .level-4 {{ background-color: #216e39; }}

        /* 2. Month Calendar Styles */
        .month-selector {{ margin-bottom: 15px; padding: 6px; border-radius: 6px; }}
        .calendar-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; text-align: center; }}
        .calendar-header {{ font-weight: bold; padding: 5px; background: #eaeef2; border-radius: 4px; }}
        .calendar-day {{ border: 1px solid #d0d7de; border-radius: 4px; padding: 15px 5px; background: #fff; position: relative; }}
        .calendar-day.level-1 {{ background-color: #9be9a8; }}
        .calendar-day.level-2 {{ background-color: #40c463; }}
        .calendar-day.level-3 {{ background-color: #30a14e; color: white; }}
        .calendar-day.level-4 {{ background-color: #216e39; color: white; }}
        .calendar-day .day-num {{ font-size: 12px; color: #57606a; position: absolute; top: 2px; left: 4px; }}
        .calendar-day .day-hours {{ font-size: 14px; font-weight: bold; margin-top: 5px; }}

        /* 3. Weekly Stats Styles */
        .stat-row {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f0f2f5; padding: 10px 0; }}
        .stat-row:last-child {{ border: none; }}
        .badge {{ background: #ddf4ff; color: #0969da; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>KU Leuven Study Analytics</h1>
        
        <div class="card">
            <h2>1. Annual Study Contribution Calendar</h2>
            <div class="year-grid" id="yearGrid"></div>
        </div>

        <div class="card">
            <h2>2. Monthly Grid View</h2>
            <select class="month-selector" id="monthSelect" onchange="renderMonth()"></select>
            <div class="calendar-grid" id="monthGrid"></div>
        </div>

        <div class="card">
            <h2>3. Weekly Metric Calculator & Logs</h2>
            <div id="weeklyStats"></div>
        </div>
    </div>

    <script>
        const dailyData = {json.dumps(daily_summary)};
        const weeklyData = {json.dumps(weekly_stats_list)};

        // Helper to determine GitHub color level
        function getColorClass(hours) {{
            if (!hours || hours === 0) return '';
            if (hours < 2) return 'level-1';
            if (hours < 4) return 'level-2';
            if (hours < 7) return 'level-3';
            return 'level-4';
        }}

        // 1. Render Annual Grid
        const yearGrid = document.getElementById('yearGrid');
        const startDate = new Date(2026, 0, 1); // January 1st, 2026
        for (let i = 0; i < 365; i++) {{
            const currentDate = new Date(startDate);
            currentDate.setDate(startDate.getDate() + i);
            const dateStr = currentDate.toISOString().split('T')[0];
            const hours = dailyData[dateStr] || 0;
            
            const cell = document.createElement('div');
            cell.className = 'day-cell ' + getColorClass(hours);
            cell.title = `${{dateStr}}: ${{hours}} hours`;
            yearGrid.appendChild(cell);
        }}

        // 2. Populate Month Selector & Render
        const uniqueMonths = [...new Set(weeklyData.map(item => item.month_name))];
        const select = document.getElementById('monthSelect');
        uniqueMonths.forEach(m => {{
            const opt = document.createElement('option');
            opt.value = m;
            opt.innerText = m + " 2026";
            select.appendChild(opt);
        }});

        function renderMonth() {{
            const targetMonthName = select.value || uniqueMonths[0];
            const monthGrid = document.getElementById('monthGrid');
            monthGrid.innerHTML = '';

            const headers = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            headers.forEach(h => {{
                const div = document.createElement('div');
                div.className = 'calendar-header';
                div.innerText = h;
                monthGrid.appendChild(div);
            }});

            const monthMap = {{ 'January':0, 'February':1, 'March':2, 'April':3, 'May':4, 'June':5, 'July':6, 'August':7, 'September':8, 'October':9, 'November':10, 'December':11 }};
            const monthIdx = monthMap[targetMonthName];
            
            const firstDay = new Date(2026, monthIdx, 1);
            const lastDay = new Date(2026, monthIdx + 1, 0);
            
            let startDayOfWeek = firstDay.getDay() - 1; // Adjust to Monday start
            if (startDayOfWeek === -1) startDayOfWeek = 6;

            for (let i = 0; i < startDayOfWeek; i++) {{
                const blank = document.createElement('div');
                monthGrid.appendChild(blank);
            }}

            for (let day = 1; day <= lastDay.getDate(); day++) {{
                const current = new Date(2026, monthIdx, day);
                const offsetDate = new Date(current.getTime() - (current.getTimezoneOffset() * 60000));
                const dateStr = offsetDate.toISOString().split('T')[0];
                const hours = dailyData[dateStr] || 0;

                const dayCell = document.createElement('div');
                dayCell.className = 'calendar-day';
                if (hours > 0) dayCell.classList.add(getColorClass(hours));
                
                dayCell.innerHTML = `<span class="day-num">${{day}}</span>
                                     <div class="day-hours">${{hours > 0 ? hours + 'h' : '-'}}</div>`;
                monthGrid.appendChild(dayCell);
            }}
        }}
        if(uniqueMonths.length > 0) renderMonth();

        // 3. Render Weekly Stats
        const statsContainer = document.getElementById('weeklyStats');
        weeklyData.forEach(row => {{
            const item = document.createElement('div');
            item.className = 'stat-row';
            item.innerHTML = `
                <div>
                    <strong>${{row.month_name}} - Week ${{row.week_num}}</strong><br>
                    <small>${{row.sessions}} library visits • Pace: ${{row.avg_hours}}h per visit</small>
                </div>
                <div class="badge">${{row.total_hours}} Total Hours</div>
            `;
            statsContainer.appendChild(item);
        }});
    </script>
</body>
</html>
"""

# 4. Save file out to directory
with open(DASHBOARD_PATH, 'w') as f:
    f.write(html_template)

print("Successfully compiled unified HTML Dashboard! View it via your python web server.")
