# backend/ — FastAPI + SQLite

> API-контракты — в `docs/data-model.md`. Архитектурные потоки — в `docs/architecture.md`. **Не выдумывай новые эндпоинты, не сверившись с этими документами.**

---

## Стек

- **Python 3.10+** — единый по проекту.
- **FastAPI** (≥0.110) + **Uvicorn**.
- **Pydantic v2** для схем (приходит с FastAPI 0.100+).
- **SQLAlchemy 2.x** + **aiosqlite** — асинхронный доступ к SQLite.
- **Alembic** — миграции. На MVP можно начать с `Base.metadata.create_all`, миграции — позже.
- **reportlab** + **matplotlib** — для PDF-экспорта в `services/pdf_exporter.py` (графики рендерятся в PNG и embed-ятся).
- **pandas** — для CSV-экспорта.
- **httpx** — если нужен исходящий HTTP. Не requests.

**Запрещено:** Django (overkill), Flask (нет встроенной валидации), MongoDB, отдельный сервер БД.

---

## Структура папки

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Создание FastAPI app, регистрация роутеров
│   ├── api/
│   │   ├── __init__.py
│   │   ├── ingest.py        # POST /ingest
│   │   ├── predict.py       # POST /predict
│   │   ├── history.py       # GET /history
│   │   └── export.py        # GET /export
│   ├── core/
│   │   ├── config.py        # Pydantic Settings (BASE_DIR, DB_URL, ML_MODEL_PATH)
│   │   └── db.py            # SQLAlchemy engine, session factory
│   ├── models/              # ORM-модели (users, sessions, biometry_samples, ...)
│   │   └── __init__.py
│   ├── schemas/             # Pydantic-схемы для запросов/ответов
│   │   └── __init__.py
│   └── services/
│       ├── ml_client.py     # Тонкий клиент к ml_core (импорт + вызов)
│       └── pdf_exporter.py  # Генерация PDF-отчёта для врача (reportlab)
├── tests/                   # Только smoke-тесты на критичные эндпоинты
├── requirements.txt
└── .env.example
```

---

## Конвенции

1. **Каждый эндпоинт — async.** Даже если внутри синхронный код. Так не блокируем event loop при росте.
2. **Pydantic-схемы — в `schemas/`,** ORM-модели — в `models/`. Никогда не возвращай ORM-объект напрямую — только через схему.
3. **БД-сессия — через Depends.** Не создавай движок в каждом обработчике.
4. **Никаких голых SQL-строк.** SQLAlchemy ORM или Core, не raw.
5. **Логирование** через стандартный `logging`, формат настраивается в `core/config.py`. **Не print.**
6. **Ошибки** — через `HTTPException` с понятным `detail`. Не возвращай 500 без логирования.

---

## Интеграция с ml_core

`services/ml_client.py` — тонкий слой, импортирует `ml_core.model_predict` и вызывает синхронно. На MVP инференс быстрый (<50ms), поэтому отдельный процесс не нужен.

`UserBaseline` (см. `docs/data-model.md`) собирается из таблицы `users` по `user_id` и передаётся в `extract_features`. Если у пользователя ещё нет baseline — используются дефолтные значения, описанные в data-model.md.

```text
# Псевдо-API клиента
def predict(window: list[BiometrySample], baseline: UserBaseline) -> PredictionResult:
    features = ml_core.extract_features(window, baseline)
    label, conf = ml_core.predict(features)
    return PredictionResult(label=label, confidence=conf, ...)
```

---

## Env-переменные (`.env.example`)

```text
DATABASE_URL=sqlite+aiosqlite:///./data.db
ML_MODEL_PATH=../ml_core/models/baseline.joblib
LOG_LEVEL=INFO
```

**Не коммитить `.env`** — только `.env.example`.

---

## Что НЕ делать

- ❌ Не добавлять авторизацию (JWT, OAuth) — на MVP `user_id` прокидывается явно.
- ❌ Не делать middleware для rate-limit, CORS-only-prod и т.п.
- ❌ Не уносить ML в отдельный сервис (Celery/Ray) — синхронный вызов из FastAPI достаточно.
- ❌ Не использовать Alembic, пока схема не стабилизировалась — `create_all` на старте.

---

## Smoke-тесты (минимум)

В `tests/test_smoke.py`:

- `POST /predict` с валидным окном → 200, корректная схема ответа.
- `POST /ingest` сохраняет в БД.
- `GET /history` возвращает непустой ответ после ingest.

Pytest + httpx AsyncClient. Без mock'ов БД — поднимаем in-memory SQLite.
