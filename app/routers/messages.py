
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter()


@router.post("/", response_model=schemas.Message, status_code=status.HTTP_201_CREATED)
def create_message(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    # Check that user is in room
    link = (
        db.query(models.UserRoom)
        .filter(models.UserRoom.user_id == message.user_id, models.UserRoom.room_id == message.room_id)
        .first()
    )
    if not link:
        raise HTTPException(status_code=403, detail="Пользователь не состоит в комнате")

    db_message = models.Message(
        content=message.content,
        user_id=message.user_id,
        room_id=message.room_id,
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


@router.get("/", response_model=List[schemas.Message])
def list_messages(db: Session = Depends(get_db)):
    return db.query(models.Message).order_by(models.Message.created_at).all()


@router.get("/room/{room_id}", response_model=List[schemas.Message])
def list_messages_for_room(room_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Message)
        .filter(models.Message.room_id == room_id)
        .order_by(models.Message.created_at)
        .all()
    )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: int, db: Session = Depends(get_db)):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    db.delete(message)
    db.commit()
    return None
