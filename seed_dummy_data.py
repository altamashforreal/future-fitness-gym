import random
from datetime import date, timedelta, datetime, timezone
from app.db.session import SessionLocal, engine, Base
from app.models import user, member, plan, membership, checkin, payment
from app.models.member import Member, Gender
from app.models.plan import Plan
from app.models.membership import Membership, MembershipAddon, MembershipStatus
from app.models.checkin import CheckIn, CheckInStatus
from app.models.payment import Payment

db = SessionLocal()

# ── Get Plans ──────────────────────────────────────────────
monthly = db.query(Plan).filter(Plan.name == "Monthly").first()
quarterly = db.query(Plan).filter(Plan.name == "Quarterly").first()
annual = db.query(Plan).filter(Plan.name == "Annual").first()
pt_addon = db.query(Plan).filter(Plan.name == "Personal Training").first()

if not monthly:
    print("Run `python seed.py` first to create plans.")
    exit(1)

plans = [monthly, quarterly, annual]

# ── Dummy Data ──────────────────────────────────────────────
dummy_members = [
    {"first": "Rahul", "last": "Sharma", "phone": "9820011111", "gender": Gender.male},
    {"first": "Priya", "last": "Patel", "phone": "9820011112", "gender": Gender.female},
    {"first": "Amit", "last": "Singh", "phone": "9820011113", "gender": Gender.male},
    {"first": "Neha", "last": "Gupta", "phone": "9820011114", "gender": Gender.female},
    {"first": "Vikram", "last": "Malhotra", "phone": "9820011115", "gender": Gender.male},
    {"first": "Anjali", "last": "Desai", "phone": "9820011116", "gender": Gender.female},
    {"first": "Rohit", "last": "Kumar", "phone": "9820011117", "gender": Gender.male},
    {"first": "Sneha", "last": "Joshi", "phone": "9820011118", "gender": Gender.female},
    {"first": "Karan", "last": "Mehta", "phone": "9820011119", "gender": Gender.male},
    {"first": "Pooja", "last": "Shah", "phone": "9820011120", "gender": Gender.female},
]

today = date.today()
now = datetime.now(timezone.utc)

def add_days(d, days):
    return d + timedelta(days=days)

print("Seeding dummy members, memberships, payments, and check-ins...")

total_members = db.query(Member).count()

for i, data in enumerate(dummy_members):
    member_id_str = f"GF{total_members + i + 1:04d}"
    
    # Check if already exists
    m = db.query(Member).filter(Member.phone == data["phone"]).first()
    if not m:
        m = Member(
            member_id=member_id_str,
            first_name=data["first"],
            last_name=data["last"],
            phone=data["phone"],
            gender=data["gender"],
            email=f"{data['first'].lower()}@example.com",
            address="123 Main St, Mumbai"
        )
        db.add(m)
        db.flush()
        
        # Assign Membership
        selected_plan = random.choice(plans)
        
        # 1. Active (Future expiry) - 60%
        # 2. Expiring soon (Within 7 days) - 20%
        # 3. Expired - 20%
        rand = random.random()
        
        if rand < 0.6:
            # Active (ends in 15 to 300 days)
            days_remaining = random.randint(15, 300)
            end_date = add_days(today, days_remaining)
            start_date = add_days(end_date, -selected_plan.duration_days)
            m.is_active = True
        elif rand < 0.8:
            # Expiring (ends in 1 to 6 days)
            days_remaining = random.randint(1, 6)
            end_date = add_days(today, days_remaining)
            start_date = add_days(end_date, -selected_plan.duration_days)
            m.is_active = True
        else:
            # Expired (ended 2 to 30 days ago)
            days_expired = random.randint(2, 30)
            end_date = add_days(today, -days_expired)
            start_date = add_days(end_date, -selected_plan.duration_days)
            m.is_active = False # Depending on logic, it might still be true but membership expired
            
        mem = Membership(
            member_id=m.id,
            plan_id=selected_plan.id,
            start_date=start_date,
            end_date=end_date,
            is_renewal=False
        )
        db.add(mem)
        db.flush()
        
        # Payment
        pay = Payment(
            member_id=m.id,
            membership_id=mem.id,
            amount=selected_plan.price,
            payment_method=random.choice(["cash", "card", "upi"]),
            created_at=datetime.combine(start_date, datetime.min.time())
        )
        db.add(pay)
        
        # Generate some check-ins for the last 5 days
        for days_ago in range(5, -1, -1):
            checkin_date = add_days(today, -days_ago)
            # Only check in if the membership was active on that day (approximate)
            if checkin_date >= start_date:
                # Determine status at time of checkin
                days_left = (end_date - checkin_date).days
                
                if days_left < 0:
                    status = CheckInStatus.denied
                elif days_left <= 7:
                    status = CheckInStatus.expiring
                else:
                    status = CheckInStatus.allowed
                    
                # Skip some days randomly
                if random.random() < 0.7:
                    ci_time = datetime(checkin_date.year, checkin_date.month, checkin_date.day, 
                                      random.randint(6, 20), random.randint(0, 59))
                    ci = CheckIn(
                        member_id=m.id,
                        status=status,
                        checked_in_at=ci_time,
                        checked_in_by=1, # Owner/system
                        method=random.choice(["member_id", "biometric"])
                    )
                    db.add(ci)

db.commit()
db.close()
print("Dummy data generated successfully!")
