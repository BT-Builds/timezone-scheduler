# Timezone Aware Scheduler API

Solves timezone conversion and business hour validation for appointment scheduling, shift planning, and meeting coordination.

## Endpoints

### `GET /health`
Health check (no auth required)

### `POST /convert`
Convert datetime between timezones with DST handling.

```bash
curl -X POST https://timezone-scheduler.vercel.app/convert \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-change-in-production" \
  -d '{"datetime": "2024-06-15T14:30:00", "from_timezone": "America/New_York", "to_timezone": "Europe/London"}'
```

### `POST /business-hours-validate`
Check if current time is within business hours.

```bash
curl -X POST https://timezone-scheduler.vercel.app/business-hours-validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-change-in-production" \
  -d '{"timezone": "America/New_York", "start_time": "09:00", "end_time": "17:00"}'
```

### `POST /schedule-meeting`
Convert meeting time for all attendees.

```bash
curl -X POST https://timezone-scheduler.vercel.app/schedule-meeting \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-change-in-production" \
  -d '{"start_datetime": "2024-06-15T14:30:00Z", "attendee_timezones": ["America/New_York", "Europe/London", "Asia/Tokyo"]}'
```

### `GET /timezone-info`
Get current timezone info with DST status.

```bash
curl "https://timezone-scheduler.vercel.app/timezone-info?timezone=America/New_York" \
  -H "X-API-Key: demo-key-change-in-production"
```

### `POST /next-business-time`
Get next available business time.

```bash
curl -X POST https://timezone-scheduler.vercel.app/next-business-time \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-change-in-production" \
  -d '{"timezone": "America/New_York", "start_time": "09:00", "end_time": "17:00"}'
```

## Pricing
$29/month for 1000 API calls - ideal for SaaS scheduling tools, appointment apps, and shift schedulers.

## Postman
[![Run in Postman](https://run.pstmn.io/button.svg)](https://raw.githubusercontent.com/BT-Builds/timezone-scheduler/main/postman_collection.json)
