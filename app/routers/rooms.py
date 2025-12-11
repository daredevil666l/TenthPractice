
import random
import string
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter()


def generate_room_code(length: int = 6) -> str:
    letters = string.ascii_uppercase + string.digits
    return "".join(random.choice(letters) for _ in range(length))


@router.post("/", response_model=schemas.Room, status_code=status.HTTP_201_CREATED)
def create_room(room: schemas.RoomCreate, owner_id: int, db: Session = Depends(get_db)):
    # generate unique code
    code = generate_room_code()
    while db.query(models.Room).filter(models.Room.code == code).first():
        code = generate_room_code()

    db_room = models.Room(name=room.name, code=code, owner_id=owner_id)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)

    # creator automatically joins the room
    user_room = models.UserRoom(user_id=owner_id, room_id=db_room.id, role="owner")
    db.add(user_room)
    db.commit()

    return db_room


@router.get("/", response_model=List[schemas.Room])
def list_rooms(db: Session = Depends(get_db)):
    return db.query(models.Room).all()


@router.get("/{room_id}", response_model=schemas.Room)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    # delete messages and links automatically due to foreign keys if configured, but we'll do simple cascade
    db.query(models.Message).filter(models.Message.room_id == room_id).delete()
    db.query(models.UserRoom).filter(models.UserRoom.room_id == room_id).delete()
    db.delete(room)
    db.commit()
    return None


@router.post("/join")
def join_room_by_code(code: str, user_id: int, db: Session = Depends(get_db)):
    room = db.query(models.Room).filter(models.Room.code == code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната с таким кодом не найдена")

    existing_link = (
        db.query(models.UserRoom)
        .filter(models.UserRoom.user_id == user_id, models.UserRoom.room_id == room.id)
        .first()
    )
    if existing_link:
        return {"message": "Вы уже участник комнаты", "room_id": room.id}

    link = models.UserRoom(user_id=user_id, room_id=room.id, role="member")
    db.add(link)
    db.commit()
    return {"message": "Подключение успешно", "room_id": room.id}


@router.get("/by-user/{user_id}", response_model=List[schemas.Room])
def get_rooms_for_user(user_id: int, db: Session = Depends(get_db)):
    links = db.query(models.UserRoom).filter(models.UserRoom.user_id == user_id).all()
    room_ids = [link.room_id for link in links]
    if not room_ids:
        return []
    rooms = db.query(models.Room).filter(models.Room.id.in_(room_ids)).all()
    return rooms
