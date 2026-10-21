from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel,Field
from database import get_session
from models import Widget, WidgetType, User
from auth import get_current_user

router= APIRouter(prefix="/widgets", tags=["widgets"])

class WidgetCreate(BaseModel):
    type: WidgetType
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    fields:dict
    button_text: str =Field(min_length=1, max_length=40)
    display_options: dict ={}

@router.post("",status_code=201)
def create_widget(
    data: WidgetCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    widget = Widget(
        type=data.type,
        title=data.title,
        description=data.description,
        fields=data.fields,
        button_text=data.button_text,
        display_options=data.display_options,
        tenant_id=user.tenant_id,
    )
    session.add(widget)
    session.commit()
    session.refresh(widget)
    return widget

@router.get("")
def list_widgets(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    widgets= session.exec(select(Widget).where(Widget.tenant_id == user.tenant_id)).all()
    return widgets