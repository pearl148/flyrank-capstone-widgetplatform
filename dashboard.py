from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from auth import get_current_user
from database import get_session
from models import Submission, User, Widget

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class SubmissionOut(BaseModel):
    id: int
    widget_public_id: str
    widget_title: str
    data: dict
    country: str | None
    city: str | None
    created_at: datetime


class SubmissionPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SubmissionOut]


@router.get("/submissions", response_model=SubmissionPage)
def list_submissions(
    widget: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    conditions = [Submission.tenant_id == user.tenant_id]

    
    if widget is not None:
        found_widget = session.exec(
            select(Widget).where(Widget.public_id == widget, Widget.tenant_id == user.tenant_id)
        ).first()
        if not found_widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        conditions.append(Submission.widget_id == found_widget.id)
    total = session.exec(select(func.count()).select_from(Submission).where(*conditions)).one()
    rows = session.exec(select(Submission,Widget).join(Widget, Submission.widget_id == Widget.id).where(*conditions).order_by(Submission.id.desc()).offset(offset).limit(limit)).all()

    items = [SubmissionOut(id=s.id, widget_public_id=w.public_id, widget_title=w.title,data=s.data, country=s.country, city=s.city, created_at=s.created_at,)for s, w in rows]
    return SubmissionPage(total=total, limit=limit, offset=offset, items=items)
    


@router.get("/stats")
def stats(
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    since = datetime.utcnow() - timedelta(days=days)
    base = [Submission.tenant_id == user.tenant_id, Submission.created_at >= since]

    # worked example: counts over time
    day_rows = session.exec(
        select(func.date(Submission.created_at).label("day"), func.count().label("total"))
        .where(*base)
        .group_by("day")
        .order_by("day")
    ).all()
    by_day = [{"day": str(r.day), "count": r.total} for r in day_rows]

    
    widget_rows = session.exec(
    select(Widget.public_id, Widget.title, func.count(Submission.id).label("total"))
    .select_from(Submission)
    .join(Widget, Submission.widget_id == Widget.id)
    .where(*base)
    .group_by(Widget.public_id, Widget.title)
    .order_by(func.count(Submission.id).desc())).all()
    by_widget = [{"widget_public_id": r.public_id, "title": r.title, "count": r.total}for r in widget_rows]

    # YOU WRITE: geo breakdown
    #   group by func.coalesce(Submission.country, "Unknown")
    #   -> list of {"country", "count"}, biggest first
    geo_rows = session.exec(select(func.coalesce(Submission.country, "Unknown").label("country"), func.count(Submission.id).label("total")).where(*base).group_by("country").order_by(func.count(Submission.id).desc())).all()
    by_country = [{"country": r.country, "count": r.total} for r in geo_rows]

    return {
        "days": days,
        "total": sum(d["count"] for d in by_day),
        "by_day": by_day,
        "by_widget": by_widget,
        "by_country": by_country,
    }