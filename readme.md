# GymFlow API

End-to-end gym management backend — FastAPI + PostgreSQL.

## Stack
- **FastAPI** — API framework
- **SQLAlchemy 2.0** — ORM
- **PostgreSQL** — database
- **passlib / bcrypt** — password hashing
- **python-jose** — JWT tokens
- **APScheduler** — daily WhatsApp reminders
- **Twilio** — WhatsApp delivery

---

## Setup

```bash
# 1. Clone and create virtualenv
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env from template
cp .env.example .env
# → edit DATABASE_URL, SECRET_KEY, Twilio credentials

# 4. Create PostgreSQL database
createdb gymflow_db

# 5. Seed owner account + default plans
python seed.py

# 6. Run
uvicorn app.main:app --reload
```

API docs at: http://localhost:8000/docs

---

## API Reference

### Auth
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login` | None | Login → JWT token |
| POST | `/api/auth/register` | Owner | Create staff account |
| GET | `/api/auth/me` | Any | Current user info |

### Members
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/members` | Staff | List all (search, filter by status) |
| POST | `/api/members` | Staff | Add new member |
| GET | `/api/members/{id}` | Staff | Member detail + status |
| PATCH | `/api/members/{id}` | Staff | Update member info |
| DELETE | `/api/members/{id}` | Owner | Deactivate member |

### Check-in
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/checkins` | Staff | Process check-in (member_id or phone) |
| GET | `/api/checkins/today` | Staff | Today's check-in log |
| GET | `/api/checkins/member/{id}` | Staff | Member check-in history |

### Memberships
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/memberships` | Staff | Create/renew membership + record payment |
| POST | `/api/memberships/{id}/freeze` | Staff | Freeze (extend end date) |
| GET | `/api/memberships/expiring` | Staff | Members expiring within N days |

### Payments
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/payments` | Staff | Record standalone payment |
| GET | `/api/payments` | Staff | Recent payment history |

### Plans
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/plans` | Staff | List active plans |
| POST | `/api/plans` | Owner | Create plan |
| PATCH | `/api/plans/{id}` | Owner | Update plan |

### Dashboard
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/dashboard` | Staff | All stats in one call |

---

## Roles
- **owner** — full access including user management and plan changes
- **reception** — everything except deleting members and managing plans

## Check-in Flow
```
POST /api/checkins
{ "query": "GF0001" }   ← member_id
{ "query": "9820011111" }  ← phone number

Response:
{
  "status": "allowed" | "denied" | "expiring",
  "full_name": "Rahul Sharma",
  "plan_name": "Monthly",
  "expires_on": "2026-10-01",
  "days_remaining": 3,
  "message": "..."
}
```

## WhatsApp Alerts (Twilio)
- Runs daily at 8:00 AM via APScheduler
- Sends to members expiring within 7 days
- Also triggers at check-in when member is expired or expiring
- Members can opt out (`whatsapp_alerts: false`)
- In dev mode (`ENV=development`), messages are only logged, not sent