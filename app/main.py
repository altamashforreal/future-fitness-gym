from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import engine, Base

# import all models so SQLAlchemy registers them before create_all
from app.models import user, member, plan, membership, checkin  # noqa

from app.api.routes import auth, members, checkins, memberships, payments, plans, dashboard
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    # shutdown
    stop_scheduler()


app = FastAPI(
    title="GymFlow API",
    description="End-to-end gym management — members, check-in, billing, alerts",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routes
app.include_router(auth.router, prefix="/api")
app.include_router(members.router, prefix="/api")
app.include_router(checkins.router, prefix="/api")
app.include_router(memberships.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(plans.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

@app.get("/")
def root():
    return RedirectResponse(url="/frontend/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

# Mount frontend so it's served by the backend directly
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")