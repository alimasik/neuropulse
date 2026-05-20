# frontend/ — Vite + React + TypeScript + Tailwind

> Перед любой работой здесь — **обязательно прочитай `docs/ux-guidelines.md`**. Это медицинский продукт для людей с сенсорной чувствительностью; UX-правила не обсуждаются.

---

## Стек этого слоя

- **Vite** — dev-сервер и сборка.
- **React 18 + TypeScript** — UI.
- **Tailwind CSS** — стили. Никаких CSS-in-JS, никаких UI-китов кроме самописных примитивов.
- **React Router** — маршрутизация SPA.
- **Recharts** — графики (волновой индикатор HRV, история).
- **Lucide React** — иконки (outline, единый стиль).
- **Zustand** (опционально) — стейт-менеджмент, если глобальный стейт начнёт расти. Не Redux.

**Запрещено:** MUI, Ant Design, Chakra, styled-components, emotion, framer-motion (анимации делать на CSS — проще контролировать `prefers-reduced-motion`).

---

## Структура папки

```text
frontend/
├── public/
│   ├── sensory-map.json     # Статические данные карты
│   └── aac-cards.json       # AAC-карточки
├── src/
│   ├── main.tsx
│   ├── App.tsx              # Маршруты
│   ├── routes/
│   │   ├── HomeScreen.tsx       # Главный экран
│   │   ├── InterventionScreen.tsx
│   │   ├── SensoryMap.tsx
│   │   ├── AACScreen.tsx
│   │   └── DoctorDashboard.tsx
│   ├── components/
│   │   ├── ui/              # Кнопки, карточки — собственные примитивы
│   │   ├── BiometryWave.tsx # Волновой индикатор
│   │   ├── BreathingCircle.tsx
│   │   └── AACCard.tsx
│   ├── lib/
│   │   ├── api.ts           # Клиент к FastAPI
│   │   └── theme.ts         # Палитра из ux-guidelines
│   └── styles/
│       └── index.css        # Tailwind + кастомные переменные
├── tailwind.config.ts
├── vite.config.ts
└── package.json
```

---

## Ключевые экраны (что должно быть к питчу)

| Экран | Маршрут | Что показывает |
| --- | --- | --- |
| Главный | `/` | Волновой индикатор HRV, текущий пульс, статус "Стабильно", кнопка SOS |
| Интервенция | `/intervention` | Дыхательный круг 4-7-8, кнопки "Тихий маршрут", "Эмбиент", "Я в порядке" |
| Sensory Map | `/map` | Стилизованная карта (SVG-моки на MVP, читает `public/sensory-map.json`), зелёные/красные зоны, кнопка «Построить тихий маршрут» — пока выводит заранее заготовленный маршрут из json |
| AAC-режим | `/aac` | 4 крупные карточки из `public/aac-cards.json`, toggle языка RU/EN, кнопка "Вызвать близкого" |
| Доктор | `/doctor` | Графики недели, список эпизодов, кнопка "Экспорт PDF" |

### SOS-flow (нажатие кнопки SOS)
1. Пользователь нажимает SOS на любом экране.
2. Frontend вызывает `POST /predict` с пометкой `manual_sos=true` (создаст эпизод `severity=3`).
3. Автоматически переход на `/aac`.
4. Опционально (`tel:` ссылка) — кнопка «Вызвать близкого» открывает диалер.

### Live-обновления состояния
WebSocket в MVP **не используется**. Frontend каждые 10 секунд опрашивает `/predict` с последним окном (хранится в стейте). При `label >= 1` показывает баннер «Сделать перерыв», при `label == 2` — автопереход на `/intervention`.

### Обратная связь («Я в порядке»)
На экране интервенции кнопка «Я в порядке» вызывает `POST /feedback` с `helpful=true, user_state="ok"` для последнего `prediction_id`. Используется для закрытия эпизодов в БД.

---

## Цвета через Tailwind

Расширь `tailwind.config.ts` цветами из `docs/ux-guidelines.md`:

```text
theme.extend.colors = {
  bg: '#F5F7F4',
  surface: '#FFFFFF',
  ink: '#2F3A36',
  muted: '#6B7770',
  calm: '#A8C8B8',
  warn: '#E8C58F',
  alert: '#D9888F',
  border: '#E0E5E2'
}
```

**Не использовать** дефолтные `red-500`, `green-500` и т.д. — только токены выше.

---

## Правила компонентов

1. **Один компонент — один файл.** PascalCase.
2. **Props типизированы интерфейсом.** Никаких `any`.
3. **Никаких inline-стилей** кроме случаев, когда без них никак (динамические значения для анимаций).
4. **Анимации** — через CSS-классы Tailwind или собственные `@keyframes` в `index.css`. Не через библиотеки.
5. **Доступность:** все интерактивные элементы имеют `aria-label`, фокусные стили видимы.
6. **Респект `prefers-reduced-motion`:** оборачивай анимации в `@media (prefers-reduced-motion: no-preference)`.

---

## API-клиент

`src/lib/api.ts` — тонкая обёртка над `fetch`. Базовый URL читается из `import.meta.env.VITE_API_URL` (по умолчанию `http://localhost:8000`).

**Запрещено:** axios (зачем тащить, когда есть fetch), swr/react-query (overkill для MVP с 5 эндпоинтами).

Поллинг `/predict` реализуй простым `setInterval` в hook'е `usePredictPolling()` с очисткой через `clearInterval` в `useEffect` cleanup. Никаких отдельных library для polling.

---

## Чек-лист перед коммитом

- [ ] `npm run build` проходит без ошибок и без warning.
- [ ] `npm run typecheck` чистый.
- [ ] Нет дефолтных tailwind-цветов (`red-*`, `blue-*`).
- [ ] Все экраны открываются на 360px шириной (мобильный) без горизонтального скролла.
- [ ] `prefers-reduced-motion` отключает анимации.
