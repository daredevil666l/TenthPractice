
from typing import Optional

from fastapi import FastAPI, Depends, Request, Form, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models
from .database import engine, get_db
from .auth import verify_password, get_password_hash
from .routers import users, rooms, messages

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Онлайн-чаты по комнатам")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Подключаем CRUD-роутеры (Swagger)
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(rooms.router, prefix="/api/rooms", tags=["Rooms"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])


def get_current_user(request: Request, db: Session) -> Optional[models.User]:
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    return user


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing = db.query(models.User).filter(
        (models.User.username == username) | (models.User.email == email)
    ).first()
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Пользователь с таким логином или email уже существует",
            },
            status_code=400,
        )

    user = models.User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return response


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль"},
            status_code=400,
        )

    response = RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("user_id")
    return response


@app.get("/rooms", response_class=HTMLResponse)
def rooms_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    # Получаем комнаты пользователя
    links = db.query(models.UserRoom).filter(models.UserRoom.user_id == user.id).all()
    room_ids = [link.room_id for link in links]
    rooms = []
    if room_ids:
        rooms = db.query(models.Room).filter(models.Room.id.in_(room_ids)).all()

    return templates.TemplateResponse(
        "rooms.html",
        {
            "request": request,
            "user": user,
            "rooms": rooms,
        },
    )


@app.post("/rooms/create")
def create_room_page(
    request: Request,
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    # Use routers.rooms.generate_room_code
    from .routers.rooms import generate_room_code

    code = generate_room_code()
    while db.query(models.Room).filter(models.Room.code == code).first():
        code = generate_room_code()

    room = models.Room(name=name, code=code, owner_id=user.id)
    db.add(room)
    db.commit()
    db.refresh(room)

    link = models.UserRoom(user_id=user.id, room_id=room.id, role="owner")
    db.add(link)
    db.commit()

    return RedirectResponse(url=f"/rooms/{room.id}", status_code=status.HTTP_302_FOUND)


@app.post("/rooms/join")
def join_room_page(
    request: Request,
    code: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    room = db.query(models.Room).filter(models.Room.code == code.strip().upper()).first()
    if not room:
        # Вернём страницу с ошибкой
        links = db.query(models.UserRoom).filter(models.UserRoom.user_id == user.id).all()
        room_ids = [link.room_id for link in links]
        rooms = []
        if room_ids:
            rooms = db.query(models.Room).filter(models.Room.id.in_(room_ids)).all()
        return templates.TemplateResponse(
            "rooms.html",
            {
                "request": request,
                "user": user,
                "rooms": rooms,
                "error": "Комната с таким кодом не найдена",
            },
            status_code=404,
        )

    existing_link = (
        db.query(models.UserRoom)
        .filter(models.UserRoom.user_id == user.id, models.UserRoom.room_id == room.id)
        .first()
    )
    if not existing_link:
        link = models.UserRoom(user_id=user.id, room_id=room.id, role="member")
        db.add(link)
        db.commit()

    return RedirectResponse(url=f"/rooms/{room.id}", status_code=status.HTTP_302_FOUND)


@app.get("/rooms/{room_id}", response_class=HTMLResponse)
def room_detail(room_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        return RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)

    # Проверим, что пользователь в комнате
    link = (
        db.query(models.UserRoom)
        .filter(models.UserRoom.user_id == user.id, models.UserRoom.room_id == room.id)
        .first()
    )
    if not link:
        return RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)

    messages_qs = (
        db.query(models.Message)
        .filter(models.Message.room_id == room.id)
        .order_by(models.Message.created_at)
        .all()
    )

    return templates.TemplateResponse(
        "room_detail.html",
        {
            "request": request,
            "user": user,
            "room": room,
            "messages": messages_qs,
        },
    )


@app.post("/rooms/{room_id}/send")
def send_message(
    room_id: int,
    request: Request,
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    # проверяем что пользователь в комнате
    link = (
        db.query(models.UserRoom)
        .filter(models.UserRoom.user_id == user.id, models.UserRoom.room_id == room_id)
        .first()
    )
    if not link:
        return RedirectResponse(url="/rooms", status_code=status.HTTP_302_FOUND)

    message = models.Message(content=content, user_id=user.id, room_id=room_id)
    db.add(message)
    db.commit()

    return RedirectResponse(url=f"/rooms/{room_id}", status_code=status.HTTP_302_FOUND)
