# KU Leuven Study Tracker

Self-hosted pipeline that syncs KU Leuven library bookings (KURT/AGORA/RBIB) from Outlook 365, stores them in SQLite, and serves an interactive dashboard over Tailscale — running nightly on a Proxmox LXC container.

## Stack
`Python 3` · `SQLite` · `pandas` · `seaborn` · `calplot` · `Tailscale` · `Cron`

## Pipeline

```
fetch_kurt.py          → sync ICS calendar to SQLite
generate_heatmap.py    → annual contribution heatmap
generate_monthly.py    → per-month calendar grid images
generate_stats.py      → week-by-week stats
build_dashboard.py     → compile dashboard.html
run_pipeline.sh        → run all steps nightly via cron
```

## Setup

```bash
git clone https://github.com/<your-username>/ku-leuven-study-tracker
cd ku-leuven-study-tracker
cp .env.example .env   # add your ICS URL and paths
pip install requests icalendar python-dotenv pandas matplotlib seaborn calplot
bash run_pipeline.sh
```

Schedule via cron (`crontab -e`):
```
0 2 * * * cd /opt/study-tracker && bash run_pipeline.sh >> pipeline.log 2>&1
```

Serve the dashboard:
```bash
python3 -m http.server 8080
# open http://<tailscale-ip>:8080/dashboard.html
```

## Environment

Copy `.env.example` to `.env` and fill in your values. Never commit `.env` — it contains your personal calendar URL.
