from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from database import get_session
from models import Widget, Submission
from validation import validate_submission_data

router = APIRouter(tags=["submissions"])

class SubmissionCreate(BaseModel):
    widget_id: str = Field(min_length=1, max_length=64)
    data: dict = Field(max_length=50)   

@router.post("/submissions", status_code=201)
def create_submission(body: SubmissionCreate, request: Request, session: Session = Depends(get_session)):
    widget = session.exec(select(Widget).where(Widget.public_id == body.widget_id)).first()
    if not widget:
        raise HTTPException(status_code = 404, detail="Widget not found")
    try:
        cleaned = validate_submission_data(widget.fields, body.data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if request.client:
        ip = request.client.host
    else: 
        ip = "unknown"
    submission = Submission(tenant_id=widget.tenant_id, widget_id=widget.id,data=cleaned,ip_address=ip)
    session.add(submission)
    session.commit()
    session.refresh(submission)
    return {"id": submission.id, "status": submission.status}
    