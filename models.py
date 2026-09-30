from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
from enum import Enum

class Tenant(SQLModel, table=True):
    id:Optional[int]= Field(default=None, primary_key=True)
    name:str
    created_at:datetime = Field(default_factory=datetime.utcnow)

class User(SQLModel, table=True):
    id:Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int=Field(foreign_key="tenant.id", index=True)
    email: str=Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WidgetType(str, Enum):
    SignUp_Form = "sign up form"
    CTA = "cta"
    Popup = "popup"


class Widget(SQLModel, table = True):
    id: Optional[int] = Field(primary_key=True, default=None)
    tenant_id: int = Field(foreign_key="tenant.id",index= True)
    type: WidgetType
    title: str
    description: str
    fields: dict = Field(sa_column=Column(JSON))
    button_text: str
    display_options:dict = Field(sa_column=Column(JSON))
    version : int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SubmissionStatus(str,Enum):
    Stored = "stored"
    Rejected = "rejected"
    
class Submission(SQLModel, table= True):
    id: Optional[int]= Field(primary_key = True, default= None)
    widget_id: int = Field(foreign_key="widget.id", index= True)
    tenant_id: int = Field(foreign_key="tenant.id", index= True)
    data: dict = Field(sa_column= Column(JSON))
    ip_address: str
    country:Optional[str] = Field(default=None)
    city: Optional[str]= Field(default=None)
    status: SubmissionStatus = Field(default=SubmissionStatus.Stored)
    created_at: datetime = Field(default_factory=datetime.utcnow)
