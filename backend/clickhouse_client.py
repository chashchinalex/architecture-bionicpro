import os
import requests
from typing import Optional, Dict
from datetime import date

HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
PORT = os.getenv("CLICKHOUSE_PORT", "8123")
DB = os.getenv("CLICKHOUSE_DATABASE", "reports_warehouse")
USER = os.getenv("CLICKHOUSE_USER", "default")
PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "password")

def get_user_report(user_id: str, start_date: date, end_date: date) -> Optional[Dict]:
    query = f"SELECT total_sessions, total_duration_minutes, average_daily_usage, movements_count, error_count, battery_usage_avg FROM {DB}.user_reports_mart WHERE user_id = '{user_id}' AND period_start >= '{start_date}' AND period_end <= '{end_date}' ORDER BY period_start DESC LIMIT 1"
    response = requests.get(f"http://{HOST}:{PORT}/", params={"database": DB, "query": query, "default_format": "JSON", "user": USER, "password": PASSWORD})
    data = response.json().get("data", [])
    if not data:
        return None
    r = data[0]
    return {
        "total_sessions": int(r["total_sessions"]),
        "total_duration_minutes": float(r["total_duration_minutes"]),
        "average_daily_usage": float(r["average_daily_usage"]),
        "movements_count": int(r["movements_count"]),
        "error_count": int(r["error_count"]),
        "battery_usage_avg": float(r["battery_usage_avg"])
    }
