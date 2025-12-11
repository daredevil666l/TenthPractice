
# Онлайн-чаты по комнатам (FastAPI)

Простой учебный проект на основе FastAPI и CRUD-операций. 
Поддерживаются пользователи, комнаты и сообщения. Интерфейс 
для работы через браузер + Swagger-документация.

## Запуск

1. Создайте и активируйте виртуальное окружение (по желанию):

```bash
python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\\Scripts\\activate  # Windows
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Запустите сервер:

```bash
uvicorn app.main:app --reload
```

4. Откройте в браузере:

- Главная страница: http://127.0.0.1:8000
- Swagger (CRUD): http://127.0.0.1:8000/docs

## Структура

- `app/main.py` — точка входа FastAPI, HTML-маршруты.
- `app/models.py` — SQLAlchemy-модели (User, Room, UserRoom, Message).
- `app/schemas.py` — Pydantic-схемы для API.
- `app/routers/` — CRUD-роутеры для пользователей, комнат и сообщений.
- `templates/` — Jinja2-шаблоны.
- `static/` — стили и скрипты.
