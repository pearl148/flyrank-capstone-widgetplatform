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

def get_owned_widget(widget_id: int, user: User, session: Session) -> Widget:
    widget = session.exec(
        select(Widget).where(Widget.id == widget_id, Widget.tenant_id == user.tenant_id)
    ).first()
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget

class WidgetUpdate(BaseModel):
    title:str | None = Field(default=None,min_length=1,max_length=100)
    description: str|None = Field(default=None,max_length=500)
    fields: dict | None = Field(default=None)
    button_text: str | None = Field(default=None,min_length=1,max_length=40)
    display_options: dict | None = Field(default=None)  

@router.get("/{widget_id}")
def get_widget(widget_id:int, user:User=Depends(get_current_user),session: Session= Depends(get_session)):
    widget = get_owned_widget(widget_id,user,session)
    return widget   

@router.put("/{widget_id}")
def update_widget(widget_id:int, data:WidgetUpdate, user:User=Depends(get_current_user),session:Session=Depends(get_session)):
    widget = get_owned_widget(widget_id,user,session)
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for key,value in update_data.items():
        setattr(widget,key,value)
    widget.version += 1
    session.add(widget)
    session.commit()
    session.refresh(widget)
    return widget

@router.delete("/{widget_id}", status_code = 204)
def delete_widget(widget_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    widget = get_owned_widget(widget_id,user,session)
    session.delete(widget)
    session.commit()

