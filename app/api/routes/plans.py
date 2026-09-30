from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.plan import Plan
from pydantic import BaseModel

router = APIRouter(prefix="/plans", tags=["Plans"])


class PlanResponse(BaseModel):
    id: int
    name: str
    duration_days: int
    price: float
    is_addon: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=list[PlanResponse])
def get_all_plans(db: Session = Depends(get_db)):
    """Retrieve all plans (base + addons)."""
    return db.query(Plan).all()
