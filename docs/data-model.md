# Data Model и API-контракты

> Этот документ — контракт между frontend, backend и ml_core. Менять структуры только согласованно — либо обновляя все три слоя одновременно, либо через явное обсуждение с пользователем.

---

## Сырые данные с wearable (вход системы)

Одно измерение (`BiometrySample`) — то, что приходит с устройства каждую секунду. `user_id` и `session_id` хранятся **только на уровне обёртки запроса**, чтобы не дублировать в каждой записи.

```text
{
  "ts": "2026-01-15T14:30:00Z",   // ISO8601, UTC
  "hr": 78,                        // bpm, целое
  "hrv_sdnn_ms": 42.3,             // SDNN в миллисекундах, float
  "accel_mag": 0.18,               // магнитуда акселерометра, float (g)
  "gsr_us": 5.4                    // микросименсы, float (опционально, null если устройство не поддерживает)
}
```

В реальности wearable обычно отдаёт пачкой за окно (60 секунд = 60 сэмплов). На MVP считаем, что батч = одно окно для инференса.

### UserBaseline (контракт между БД и ML)

Из таблицы `users` собирается dataclass, который backend передаёт в `ml_core.extract_features`:

```text
@dataclass
class UserBaseline:
    user_id: int
    baseline_hr: float       # средняя ЧСС в покое
    baseline_hrv: float      # средний SDNN (мс)
```

Если baseline ещё не накоплен (новый пользователь) — используются значения по умолчанию: `baseline_hr=72`, `baseline_hrv=45`. ML-модель должна работать и в этом случае (фичи `*_delta` и `*_drop_pct` просто дадут менее точный сигнал).

---

## Фичи для ML (производные от окна)

Из окна сэмплов (60 сек) feature_extractor считает:

| Фича | Формула | Что значит |
| --- | --- | --- |
| `hr_mean` | mean(hr) | Средний пульс |
| `hr_delta` | hr_mean - baseline_hr | Отклонение от базового пульса (baseline = средний за последние 24ч) |
| `hrv_sdnn` | mean(hrv_sdnn_ms) | Усреднённый SDNN |
| `hrv_drop_pct` | (baseline_hrv - hrv_sdnn) / baseline_hrv | % падения HRV |
| `accel_var` | variance(accel_mag) | Вариация движения (стимминг → растёт) |
| `accel_spikes` | count(accel_mag > 0.5) | Число "тиковых" всплесков |
| `gsr_mean` | mean(gsr_us) | Кожно-гальваническая активность |
| `gsr_slope` | linregress(gsr).slope | Тренд GSR (нарастает → стресс) |

Все эти фичи — на вход модели. Никаких сырых временных рядов в модель не подаём (на MVP).

---

## Метки классов (target)

```text
0 = "calm"        — спокойное состояние
1 = "rising"      — нарастающий стресс (предиктивная зона, 5–15 мин до возможного срыва)
2 = "critical"    — высокий риск, нужна интервенция сейчас
```

Для синтетики правила меток:
- `hrv_drop_pct > 0.3 AND hr_delta > 12` → `rising`
- `hrv_drop_pct > 0.5 AND hr_delta > 20 AND accel_spikes > 5` → `critical`
- иначе → `calm`

(в реальности — обучили бы на размеченных данных от клиницистов)

---

## Схема SQLite

```text
TABLE users
  id              INTEGER PK
  name            TEXT
  baseline_hr     REAL          -- средний пульс пользователя в покое
  baseline_hrv    REAL          -- средний SDNN
  created_at      TEXT

TABLE sessions
  id              INTEGER PK
  user_id         INTEGER FK → users.id
  started_at      TEXT
  ended_at        TEXT
  context         TEXT          -- "metro", "school", "home", "free"

TABLE biometry_samples
  id              INTEGER PK
  session_id      INTEGER FK
  ts              TEXT
  hr              INTEGER
  hrv_sdnn_ms     REAL
  accel_mag       REAL
  gsr_us          REAL

TABLE predictions
  id                  INTEGER PK
  session_id          INTEGER FK
  ts                  TEXT
  label               INTEGER       -- 0/1/2
  confidence          REAL          -- 0..1
  recommended_action  TEXT          -- "breathing" | "quiet_route" | "aac" | null
                                    -- ИМЯ ПОЛЯ совпадает с API-ответом (см. ниже), чтобы не было маппинга

TABLE feedback                     -- подтверждение/опровержение предсказания пользователем
  id              INTEGER PK
  prediction_id   INTEGER FK
  ts              TEXT
  helpful         INTEGER       -- 1 если пользователь подтвердил, 0 если нет
  user_state      TEXT          -- "ok" | "stressed" | "recovered"

TABLE episodes              -- зафиксированные срывы (для аналитики врача)
  id              INTEGER PK
  user_id         INTEGER FK
  started_at      TEXT
  ended_at        TEXT
  severity        INTEGER       -- 1..3
  trigger_guess   TEXT          -- "noise", "crowd", "light", "unknown" (заполняется по контексту сессии или вручную)
  notes           TEXT
```

### Правила создания эпизода (важно)

Запись в `episodes` создаётся автоматически, когда выполняется **любое** из условий:

1. Backend получает три подряд предсказания с `label == 2` (critical) в течение 3 минут — `started_at` фиксируется на первое из них.
2. Пользователь явно нажимает SOS — `severity=3`, `started_at` = сейчас.

Эпизод считается завершённым (`ended_at`), когда:
- два подряд предсказания вернулись к `label == 0`, **или**
- пользователь нажал «Я в порядке» в feedback.

`severity` вычисляется по максимальной `confidence` за время эпизода: `<0.6 → 1`, `0.6–0.85 → 2`, `>0.85 → 3`. `trigger_guess` берётся из `sessions.context` (metro/school/home/free).

---

## API-контракты (FastAPI)

### `POST /ingest`
Принимает окно биометрии. `user_id` / `session_id` — **только в обёртке**, не дублируются в каждом сэмпле.

**Тело запроса:**
```text
{
  "user_id": 1,
  "session_id": 17,
  "samples": [ {BiometrySample без user_id/session_id}, ... ]   // 30-60 элементов
}
```

**Ответ:** `202 Accepted`, `{"received": <int>}`.

### `POST /predict`
Синхронный инференс на окне.

**Тело запроса:** идентично `/ingest`. Backend подтянет `UserBaseline` из БД по `user_id`.

**Ответ:**
```text
{
  "prediction_id": 42,
  "label": 1,
  "label_name": "rising",
  "confidence": 0.78,
  "recommended_action": "breathing",   // имя совпадает с колонкой БД
  "features": { ... }                  // для дашборда, опционально
}
```

### `GET /history?user_id=1&limit=50`
Последние эпизоды + последние предсказания.

**Ответ:**
```text
{
  "episodes": [ {...} ],
  "recent_predictions": [ {...} ],
  "stats_7d": {
    "total_episodes": 4,
    "avg_severity": 1.8,
    "top_trigger": "noise"
  }
}
```

### `POST /feedback`
Пользователь подтверждает корректность последнего предсказания.

**Тело запроса:**
```text
{
  "prediction_id": 42,
  "helpful": true,
  "user_state": "ok"     // "ok" | "stressed" | "recovered"
}
```
**Ответ:** `200 OK`, `{"saved": true}`. Используется для закрытия эпизодов и для будущего ретренинга модели.

### `GET /export?user_id=1&format=pdf|csv`
Отчёт для врача.

- **PDF** (формируется `services/pdf_exporter.py` через reportlab): титул, период (последние 7 дней), сводка эпизодов (таблица), график пульса и HRV (matplotlib → PNG → embed), топ-3 триггера.
- **CSV** (формируется через `pandas.DataFrame.to_csv`): плоская выгрузка `episodes JOIN predictions` для импорта в Excel.

Возвращает файл с корректным `Content-Disposition: attachment; filename=...`.

---

## Sensory Map (упрощённая модель данных)

На MVP — статический GeoJSON в `frontend/public/sensory-map.json`:

```text
{
  "quiet_zones": [
    { "name": "Парк им. Горького", "coords": [...], "type": "park" },
    ...
  ],
  "noise_hotspots": [
    { "name": "Метро Площадь Революции", "coords": [...], "noise_level": "high" },
    ...
  ]
}
```

Никакого реального стриминга. Краудсорсинг — задача после хакатона.

---

## AAC-карточки (статика)

`frontend/public/aac-cards.json`:

```text
[
  { "id": "autism", "icon": "user-circle", "text_ru": "У меня аутизм...", "text_en": "I have autism..." },
  ...
]
```
