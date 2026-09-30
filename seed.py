"""
Run once after first deploy:
    python seed.py

Creates the owner account and default membership plans.
"""
from app.db.session import SessionLocal, engine, Base
from app.models import user, member, plan, membership, checkin  # noqa — register all models
from app.models.user import User, UserRole
from app.models.plan import Plan
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ── Owner account ──────────────────────────────────────────────
owner_email = "owner@ironedgegym.com"
if not db.query(User).filter(User.email == owner_email).first():
    db.add(User(
        name="Gym Owner",
        email=owner_email,
        hashed_password=hash_password("changeme123"),
        role=UserRole.owner,
    ))
    print(f"Owner created: {owner_email} / changeme123")

# ── Reception account ──────────────────────────────────────────
reception_email = "reception@ironedgegym.com"
if not db.query(User).filter(User.email == reception_email).first():
    db.add(User(
        name="Reception Desk",
        email=reception_email,
        hashed_password=hash_password("reception123"),
        role=UserRole.reception,
    ))
    print(f"Reception created: {reception_email} / reception123")

# ── Default plans ──────────────────────────────────────────────
default_plans = [
    {"name": "Monthly",     "duration_days": 30,  "price": 1500.00},
    {"name": "Quarterly",   "duration_days": 90,  "price": 3500.00},
    {"name": "Half-Yearly", "duration_days": 180, "price": 6500.00},
    {"name": "Annual",      "duration_days": 365, "price": 11000.00},
]
addon_plans = [
    {"name": "Personal Training", "duration_days": 30, "price": 800.00, "is_addon": True},
    {"name": "Locker",            "duration_days": 30, "price": 300.00, "is_addon": True},
]

for p in default_plans + addon_plans:
    if not db.query(Plan).filter(Plan.name == p["name"]).first():
        db.add(Plan(**p))
        print(f"Plan created: {p['name']} — ₹{p['price']}")

db.commit()
db.close()
print("\nSeed complete. Change passwords before going to production.")