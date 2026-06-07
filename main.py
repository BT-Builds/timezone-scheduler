import os
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import mangum
import pytz

app = FastAPI(title="Timezone Aware Scheduler API")
# === BT Builds Standard Middleware (auto-injected) ===
from fastapi.middleware.cors import CORSMiddleware as _BTCors
app.add_middleware(_BTCors, allow_origins=["*"], allow_methods=["*"],
    allow_headers=["*"], expose_headers=["X-RateLimit-Limit","X-RateLimit-Remaining","X-RateLimit-Reset"])

@app.middleware("http")
async def _bt_add_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Powered-By"] = "btbuilds"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


API_KEY = os.getenv("API_KEY", "demo-key-change-in-production")

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

class TimezoneConvertRequest(BaseModel):
    datetime: str
    from_timezone: str
    to_timezone: str

class BusinessHoursRequest(BaseModel):
    timezone: str
    start_time: str
    end_time: str
    working_days: Optional[List[str]] = ["monday", "tuesday", "wednesday", "thursday", "friday"]

class ScheduleMeetingRequest(BaseModel):
    start_datetime: str
    duration_hours: int = 1
    attendee_timezones: List[str]
    business_hours: Optional[BusinessHoursRequest] = None

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/convert")
def convert_timezone(
    request: TimezoneConvertRequest,
    api_key: str = Depends(verify_api_key)
):
    try:
        dt = datetime.fromisoformat(request.datetime.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO format.")
    
    try:
        tz_from = pytz.timezone(request.from_timezone)
        tz_to = pytz.timezone(request.to_timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        raise HTTPException(status_code=400, detail="Unknown timezone")
    
    localized_dt = tz_from.localize(dt) if dt.tzinfo is None else dt
    converted_dt = localized_dt.astimezone(tz_to)
    
    return {
        "input": request.datetime,
        "input_timezone": request.from_timezone,
        "output": converted_dt.isoformat(),
        "output_timezone": request.to_timezone,
        "utc_offset": str(converted_dt.tzinfo.utcoffset(converted_dt))
    }

@app.post("/business-hours-validate")
def validate_business_hours(
    request: BusinessHoursRequest,
    api_key: str = Depends(verify_api_key)
):
    try:
        tz = pytz.timezone(request.timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        raise HTTPException(status_code=400, detail="Unknown timezone")
    
    now = datetime.now(tz)
    
    try:
        start_h, start_m = map(int, request.start_time.split(':'))
        end_h, end_m = map(int, request.end_time.split(':'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")
    
    day_name = now.strftime('%A').lower()
    is_working_day = day_name in request.working_days
    
    current_minutes = now.hour * 60 + now.minute
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m
    
    in_business_hours = start_minutes <= current_minutes <= end_minutes
    
    return {
        "datetime": now.isoformat(),
        "timezone": request.timezone,
        "is_working_day": is_working_day,
        "is_business_hours": in_business_hours and is_working_day,
        "day": day_name,
        "business_hours": {"start": request.start_time, "end": request.end_time}
    }

@app.post("/schedule-meeting")
def schedule_meeting(
    request: ScheduleMeetingRequest,
    api_key: str = Depends(verify_api_key)
):
    try:
        start_dt = datetime.fromisoformat(request.start_datetime.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")
    
    attendee_times = []
    for tz_name in request.attendee_timezones:
        try:
            tz = pytz.timezone(tz_name)
            localized = start_dt.astimezone(tz)
            attendee_times.append({
                "timezone": tz_name,
                "local_time": localized.strftime("%Y-%m-%d %H:%M"),
                "utc_offset": str(tz.utcoffset(localized))
            })
        except pytz.exceptions.UnknownTimeZoneError:
            raise HTTPException(status_code=400, detail=f"Unknown timezone: {tz_name}")
    
    return {
        "utc_time": start_dt.isoformat(),
        "attendee_times": attendee_times,
        "duration_hours": request.duration_hours
    }

@app.get("/timezone-info")
def get_timezone_info(
    timezone: str,
    api_key: str = Depends(verify_api_key)
):
    try:
        tz = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        raise HTTPException(status_code=400, detail="Unknown timezone")
    
    now = datetime.now(tz)
    info = tz.localize(now)
    
    return {
        "timezone": timezone,
        "abbreviation": now.strftime('%Z'),
        "utc_offset": str(info.utcoffset()),
        "dst": bool(info.dst()),
        "current_time": now.isoformat()
    }

@app.post("/next-business-time")
def get_next_business_time(
    timezone: str = "America/New_York",
    start_time: str = "09:00",
    end_time: str = "17:00",
    working_days: Optional[List[str]] = ["monday", "tuesday", "wednesday", "thursday", "friday"],
    api_key: str = Depends(verify_api_key)
):
    try:
        tz = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        raise HTTPException(status_code=400, detail="Unknown timezone")
    
    try:
        start_h, start_m = map(int, start_time.split(':'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format")
    
    now = datetime.now(tz)
    day_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
    }
    
    working_day_nums = [day_map[d] for d in working_days if d in day_map]
    
    check_date = now.date() + timedelta(days=1)
    while check_date.weekday() not in working_day_nums:
        check_date = check_date + timedelta(days=1)
    
    next_business = tz.localize(
        datetime.combine(check_date, datetime.min.time()).replace(hour=start_h, minute=start_m)
    )
    
    return {
        "next_business_time": next_business.isoformat(),
        "timezone": timezone,
        "hours": {"start": start_time, "end": end_time},
        "days": working_days
    }

handler = mangum.Mangum(app)