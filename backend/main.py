from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
import requests
import os
from typing import Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import io
import csv

from clickhouse_client import get_user_report

app = FastAPI()
security = HTTPBearer(auto_error=False)
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "reports-realm")

class ReportResponse(BaseModel):
    user_id: str
    period_start: str
    period_end: str
    total_sessions: int
    total_duration_minutes: float
    average_daily_usage: float
    movements_count: int
    error_count: int
    battery_usage_avg: float

async def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    userinfo = requests.get(
        f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/userinfo",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    
    if not userinfo.get("email"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {"email": userinfo["email"]}

@app.get("/reports")
async def get_report(
    format: str = "json",
    user: dict = Depends(verify_token)
):
    user_id = user["email"].replace("@", "_").replace(".", "_")
    end_dt = date.today()
    start_dt = end_dt - timedelta(days=30)
    
    report_data = get_user_report(user_id, start_dt, end_dt)
    if not report_data:
        raise HTTPException(status_code=404, detail="No data available")
    
    report = ReportResponse(
        user_id=user_id,
        period_start=str(start_dt),
        period_end=str(end_dt),
        **report_data
    )
    
    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=report.dict().keys())
        writer.writeheader()
        writer.writerow(report.dict())
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=report.csv"}
        )
    
    return report
