
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- User ----------

class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class User(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Room ----------

class RoomBase(BaseModel):
    name: str


class RoomCreate(RoomBase):
    pass


class Room(RoomBase):
    id: int
    code: str
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Message ----------

class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    room_id: int
    user_id: int


class Message(MessageBase):
    id: int
    created_at: datetime
    user_id: int
    room_id: int

    model_config = ConfigDict(from_attributes=True)
