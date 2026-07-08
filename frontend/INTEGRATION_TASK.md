# HepaRadar — задача интеграции фронтенда в бэкенд

## Контекст
Репозиторий монорепо: `backend/` (FastAPI, Python) + `ml/` + `docs/`. Фронт (Vite + React 18 + TS strict + Tailwind + shadcn/Tremor) сейчас лежит в `frontend/` и работает на моках (`src/mocks`). Задача: **встроить `frontend/` в репозиторий как папку монорепо и переписать API-слой под реальный бэкенд**. Убрать моки, auth и фичи, которых нет на бэке.

Работать ТОЛЬКО в `frontend/`. Python-код не трогать.

---

## Реальный контракт бэкенда (истина в последней инстанции)

Base URL: `http://localhost:8000`. Префикса `/api` НЕТ. Auth НЕТ.

| Метод | Путь | Тело/Query | Ответ |
|---|---|---|---|
| GET | `/health` | — | `{ "status": "ok" }` |
| POST | `/ingest` | multipart `file` (CSV) | `IngestReport` |
| POST | `/cohort/scan` | — | `ScanSummary` |
| GET | `/cohort/worklist` | `zone?, age_min?, marker?, page=1, page_size=20` | `WorklistResponse` |
| GET | `/patients/{id}` | `id: int` | `PatientCard` |

### Схемы ответов (точные поля)

```ts
// ScanSummary
{ total: number; low: number; grey: number; high: number; lost_count: number }

// WorklistResponse
{ items: WorklistItem[]; total: number; page: number; page_size: number }

// WorklistItem
{
  patient_id: number;
  mrn: string;
  age: number | null;
  sex: number | null;          // 0/1, НЕ строка
  fib4: number | null;
  apri: number | null;
  zone: "low" | "grey" | "high" | null;
  ml_risk: number | null;
  is_lost: boolean;
  last_lab_date: string | null; // ISO date "YYYY-MM-DD"
}

// PatientCard
{
  id: number;
  mrn: string;
  age: number | null;
  sex: number | null;
  labs: LabEntry[];            // LONG-формат: одна строка на аналит
  scores: ScoreEntry[];
}

// LabEntry (длинный формат!)
{ analyte: string; value: number | null; unit: string | null; date: string; quality_flag: string | null }

// ScoreEntry
{
  lab_date: string;
  fib4: number | null;
  apri: number | null;
  de_ritis: number | null;
  zone: "low" | "grey" | "high" | null;
  ml_risk: number | null;
  is_lost: boolean;
  quality_flags: string | null;
  computed_at: string;         // ISO datetime
}

// IngestReport
{
  rows_processed: number;
  patients_ingested: number;
  labs_ingested: number;
  rows_rejected: number;
  rejected_rows: { row_index: number; reason: string }[];
  quality_flags: Record<string, number>;
}
```

### Критично про поток данных
- `/cohort/worklist` возвращает **только пациентов с `is_lost = true`** и **только после запуска `POST /cohort/scan`**. До первого скана таблица Score пуста → worklist пустой. UI обязан это учитывать (кнопка «Сканировать когорту» + пустое состояние).
- Порядок в `items` уже отранжирован бэком (risk desc → recency → completeness). Клиентскую сортировку по риску НЕ делать.
- `labs` в `/patients/{id}` — ДЛИННЫЙ формат (по строке на AST/ALT/PLT/…). Для графиков/таблицы нужна свёртка long→wide по `date`.

---

## Чего на бэке НЕТ — убрать/скрыть на фронте
- **Auth / login** — роутер не подключён. Удалить `Login.tsx`, `auth.tsx`, `AuthProvider`, заголовок `Authorization`, роль/logout из `Topbar/Sidebar`. Корень редиректит сразу на `/worklist`.
- **Reflex** (`ReflexBanner`), **Referral** (`ReferralModal`), **top_reasons / «причины»** (`ReasonList`), **hcv_reflex**, **name пациента** — эндпоинтов нет. Точки вызова закомментировать/скрыть, сами файлы компонентов ОСТАВИТЬ в репо под будущий бэк. Не удалять их код.

---

## Пошаговый план (по одному шагу, коммит после каждого)

### Шаг 1 — размещение в монорепо
- Переместить содержимое так, чтобы фронт стал `frontend/` в корне репозитория бэка (если ещё не так).
- Убедиться, что у фронта нет собственного `.git` внутри `frontend/` — использовать общий git репозитория.
- В корневой `.gitignore` добавить `frontend/node_modules`, `frontend/dist`.
- Ветку создать отдельную: `feat/frontend-integration`. НЕ коммитить в main напрямую.

### Шаг 2 — env и удаление моков
- Создать `frontend/.env`:
  ```
  VITE_API_BASE_URL=http://localhost:8000
  ```
- Создать `frontend/.env.example` с тем же ключом.
- В `src/api.ts` убрать всю логику `VITE_USE_MOCKS` и импорты из `./mocks`. Удалить папку `src/mocks` (после того как все экраны переведены на реальный API).

### Шаг 3 — `src/types.ts`
- Заменить типы на схемы из раздела «Реальный контракт» выше: `WorklistItem`, `WorklistResponse`, `PatientCard`, `LabEntry`, `ScoreEntry`, `ScanSummary`, `IngestReport`.
- Тип зоны: `export type Zone = "low" | "grey" | "high"`.
- Удалить `PatientWorklist`, `PatientDetail` (старый), `ReferralResponse`, `LoginResponse`, `PatientReflex`, `Role`, `RiskLevel`.
- Хелпер: `export const sexLabel = (s: number | null) => s === 1 ? "М" : s === 0 ? "Ж" : "—"`.

### Шаг 4 — `src/api.ts`
- Один `request<T>(path, options)` с `API_BASE = import.meta.env.VITE_API_BASE_URL`. Без `Authorization`.
- Методы:
  - `health()` → `GET /health`
  - `scanCohort()` → `POST /cohort/scan` : `ScanSummary`
  - `getWorklist(params: { zone?: Zone; age_min?: number; marker?: string; page?: number; page_size?: number })` → `GET /cohort/worklist?<query>` : `WorklistResponse`
  - `getPatient(id: number)` → `GET /patients/${id}` : `PatientCard`
  - `ingestCsv(file: File)` → `POST /ingest` с `FormData` (поле `file`) : `IngestReport`
- Удалить `login`, `getPatientReflex`, `createReferral`.
- Обработка ошибок: при `!res.ok` кидать `Error` с `res.status` + телом (для тостов).

### Шаг 5 — `src/pages/Worklist.tsx`
- Грузить `getWorklist({ page, page_size, zone, age_min })`, рендерить `data.items`.
- Добавить кнопку **«Сканировать когорту»** → `api.scanCohort()` → затем refetch worklist. Показать сводку `ScanSummary` (total/low/grey/high/lost_count) после скана.
- Пустое состояние: если `items.length === 0` — текст «Запустите скан когорты, чтобы найти потерянных пациентов».
- Пагинация по `total / page / page_size`.
- Фильтры: селект `zone` (low/grey/high), числовой `age_min`.
- Колонки: MRN (вместо name), возраст, пол (`sexLabel`), FIB-4, APRI, зона (`RiskBadge` по `zone`), `last_lab_date`, флаг «потерян» (`is_lost`).
- Клик по строке → `/patients/${patient_id}`.
- Убрать клиентскую сортировку по риску.

### Шаг 6 — `src/pages/PatientDetail.tsx`
- Роут-параметр `id` привести к `number`, вызвать `getPatient(id)`.
- Свёртка labs long→wide: сгруппировать `labs` по `date`, собрать `{ date, ast, alt, plt, ... }` (analyte → поле, lowercase). Хелпер `pivotLabs(labs: LabEntry[])`.
- `TrendChart` кормить из `scores[]` (`fib4`/`apri` по `lab_date`) — это готовый временной ряд, надёжнее свёртки labs.
- Показать `mrn` (не name), возраст, пол. Последний `ScoreEntry` → зона, `de_ritis`, `is_lost`, `ml_risk`.
- `ReflexBanner`, `ReferralModal`, `ReasonList` — скрыть (закомментировать рендер), компоненты не удалять.

### Шаг 7 — auth и layout
- Удалить `src/pages/Login.tsx` и `src/auth.tsx` из роутинга (`App.tsx`), убрать `AuthProvider`.
- Корень (`/`) → редирект на `/worklist`.
- `Topbar`/`Sidebar`: убрать роль/logout/пользователя.
- `RiskBadge`: принимать `zone: Zone | null`, цвета: high=красный, grey=янтарный, low=зелёный, null=серый.

### Шаг 8 — (опционально) экран загрузки CSV
- Страница `/ingest`: `<input type=file>` → `api.ingestCsv(file)` → показать `IngestReport` (принято/отклонено/quality_flags). Полезно для демо end-to-end.

### Шаг 9 — проверка
- Поднять бэк: `docker-compose up` в корне репо. Проверить `GET http://localhost:8000/health`.
- `cd frontend && npm install && npm run dev`.
- Прогнать поток: (ingest CSV →) `scan` → worklist → карточка пациента. Проверить консоль браузера и вкладку Network — контракт должен совпадать 1:1.
- `npm run build` — должен пройти при TS strict без ошибок. `npm run lint` (oxlint) — чисто.

### Шаг 10 — коммит и PR
- Коммиты атомарные по шагам. Финально — PR из `feat/frontend-integration` в main с описанием: что интегрировано, какие фичи (auth/reflex/referral/top_reasons) отложены до реализации бэка.

---

## Definition of Done
- Нет импортов из `src/mocks`, папка удалена.
- Нет обращений к `/api/...`, `/auth/login`, `/reflex`, `/referral`.
- Worklist и карточка пациента работают на живом бэке; scan-кнопка наполняет список.
- `npm run build` и `npm run lint` проходят.
- Отложенные фичи скрыты, но их компоненты сохранены в кодовой базе.
