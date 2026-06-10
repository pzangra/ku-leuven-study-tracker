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

## Quickstart (run your own copy)

**1. Clone the repo**

```bash
git clone https://github.com/<your-username>/ku-leuven-study-tracker
cd ku-leuven-study-tracker
```

**2. Install dependencies**

```bash
pip install -r requirements.txt --break-system-packages
```

**3. Create your `.env` file**

```bash
cp .env.example .env
nano .env
```

Fill in at minimum:
- `ICS_URL` — your personal Outlook 365 calendar `.ics` link (Outlook → Calendar → Settings → Shared Calendars → Publish a Calendar)
- `USER_AGENT`, `HTTP_ACCEPT`, `HTTP_ACCEPT_ENCODING`, `HTTP_CONNECTION` — browser headers (defaults in `.env.example` work fine)
- `TAILSCALE_IP` — your machine's Tailscale IP (run `tailscale ip -4`)

All paths (`DB_PATH`, `TRACKER_DIR`, `DASHBOARD_PATH`, `HEATMAP_PATH`) default to the repo's working directory if left unset, but it's recommended to set them to absolute paths.

> The `ICS_URL` contains a personal access token. Never commit `.env` or share this link.

**4. Run the pipeline**

```bash
bash run_pipeline.sh
```

This populates `study_data.db`, generates heatmap images, and compiles `dashboard.html`.

To keep it updated automatically, add a cron job (`crontab -e`):
```
0 2 * * * cd /path/to/ku-leuven-study-tracker && bash run_pipeline.sh >> pipeline.log 2>&1
```

**5. Host the dashboard via Tailscale**

Install [Tailscale](https://tailscale.com/download) on your machine and sign in. Then start the server:

```bash
python3 server.py
```

For persistence across reboots, run it as a systemd service:
```ini
# /etc/systemd/system/study-tracker.service
[Unit]
Description=KU Leuven Study Tracker
After=network.target

[Service]
WorkingDirectory=/path/to/ku-leuven-study-tracker
ExecStart=/usr/bin/python3 /path/to/ku-leuven-study-tracker/server.py
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
systemctl enable --now study-tracker
```

Open `http://<your-tailscale-ip>:8080/dashboard.html` from any device on your tailnet.

## Features

- GitHub-style annual contribution heatmap
- Interactive monthly calendar grid with green color scale
- Week-by-week statistics (total hours, sessions, avg pace)
- Manual session logging via the dashboard UI

## Environment

Copy `.env.example` to `.env` and fill in your values. Never commit `.env` — it contains your personal calendar URL.
