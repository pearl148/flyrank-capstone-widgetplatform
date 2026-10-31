from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from database import get_session
from models import Widget, Submission
from validation import validate_submission_data
from ratelimit import ip_limiter, widget_limiter   
import os 
from geo import enrich   

router = APIRouter(tags=["submissions"])

class SubmissionCreate(BaseModel):
    widget_id: str = Field(min_length=1, max_length=64)
    data: dict = Field(max_length=50)
    website: str | None = None                          # new: honeypot field

@router.post("/submissions", status_code=201)
def create_submission(body: SubmissionCreate, request: Request, session: Session = Depends(get_session)):
    ip = request.client.host if request.client else "unknown"
  

    # 1. IP rate limit, before any DB work
    wait = ip_limiter.check(ip)
    if wait:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(wait)},
        )

    # 2. honeypot: if body.website is non-empty, return a fake success and stop
    #    (same shape as the real response, store nothing)
    if(body.website != None):
        return {"id":0, "status":"Successfully Stored"}

    # 3. widget lookup -> 404 (your existing code)
    widget = session.exec(select(Widget).where(Widget.public_id == body.widget_id)).first()
    if not widget:
        raise HTTPException(status_code = 404, detail="Widget not found")
    
    


    # 4. widget rate limit, keyed on str(widget.id)
    #    same pattern as step 1, using widget_limiter
    widget_wait = widget_limiter.check(str(widget.id))
    if widget_wait:
        raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(wait)},
            )


    # 5. validate and store (your existing code, minus the `ip = ...` lines
    #    since you now compute ip at the top)
    try:
        cleaned = validate_submission_data(widget.fields, body.data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    geo_ip = os.getenv("GEO_DEV_IP_OVERRIDE") or ip
    geo = enrich(geo_ip)
    submission = Submission(tenant_id=widget.tenant_id, widget_id=widget.id,data=cleaned,ip_address=ip,country=geo.country, city=geo.city)
    
    session.add(submission)
    session.commit()
    session.refresh(submission)
    return {"id": submission.id, "status": submission.status}