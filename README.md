# KU Leuven Study Tracker

Automated pipeline that syncs KU Leuven library bookings (KURT/AGORA/RBIB) from Outlook 365, stores them in SQLite, and serves an interactive analytics dashboard over Tailscale — running nightly on a Proxmox LXC container.

## Stack
`Python 3` · `Flask` · `SQLite` · `pandas` · `seaborn` · `calplot` · `Tailscale` · `Cron`

## Pipeline

```
fetch_kurt.py          → sync ICS calendar to SQLite
generate_heatmap.py    → annual contribution heatmap
generate_monthly.py    → per-month calendar grid images
generate_stats.py      → week-by-week stats
build_dashboard.py     → compile dashboard.html
run_pipeline.sh        → run all steps nightly via cron
server.py              → Flask server (static files + manual session API)
```

## Setup

```bash
git clone https://github.com/<your-username>/ku-leuven-study-tracker
cd ku-leuven-study-tracker
cp .env.example .env   # fill in your ICS URL and paths
pip install requests icalendar python-dotenv pandas matplotlib seaborn calplot flask
bash run_pipeline.sh
```

Schedule via cron (`crontab -e`):
```
0 2 * * * cd /opt/study-tracker && bash run_pipeline.sh >> pipeline.log 2>&1
```

Run the Flask server as a persistent systemd service:
```bash
# /etc/systemd/system/study-tracker.service
[Unit]
Description=KU Leuven Study Tracker
After=network.target

[Service]
WorkingDirectory=/opt/study-tracker
ExecStart=/usr/bin/python3 /opt/study-tracker/server.py
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
systemctl enable study-tracker
systemctl start study-tracker
```

Access the dashboard at `http://<tailscale-ip>:8080/dashboard.html`.

## Features

- GitHub-style annual contribution heatmap
- Interactive monthly calendar grid with green color scale
- Week-by-week statistics (total hours, sessions, avg pace)
- Manual session logging via the dashboard UI

## Environment

Copy `.env.example` to `.env` and fill in your values. Never commit `.env` — it contains your personal calendar URL.
