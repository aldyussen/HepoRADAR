# Задача: починить пустую БД (сайт «не работает»)

## Корень проблемы
Бэкенд подключён к `sqlite:///./dev.db` (env `HEPARADAR_DATABASE_URL`). При старте выполняется `python -m app.db.seed`, но `seed.main()` вызывает **только `seed_users()`** — в базе появляются 4 пользователя, а таблицы `patient/lab/score` остаются **пустыми**.

Из-за этого:
- `POST /cohort/scan` → `{total:0,...}`
- `GET /cohort/worklist` → `items: []`
- `GET /patients/{id}` → `404 Patient not found`
- на фронте: пустой worklist / «база не отсканирована» / карточка не открывается.

Пациенты попадают в базу только через `POST /ingest` (CSV), и этот шаг никто не делает. Каждый раз при пересоздании `dev.db` данные снова обнуляются.

## Цель
Сделать так, чтобы **свежая база всегда содержала демо-пациентов** — без ручного `/ingest`. Плюс расширить демо-набор, чтобы worklist и графики выглядели убедительно.

---

## Шаг 1 — положить демо-CSV в бэкенд
Сейчас файл лежит не в том месте: `frontend/scratch/patients.csv`. Перенести в бэкенд, чтобы сид его находил:
- Создать папку `backend/app/db/seed_data/`
- Переместить туда файл как `backend/app/db/seed_data/patients.csv`
- Удалить `frontend/scratch/` (не место для данных).

## Шаг 2 — расширить демо-CSV (~15–20 пациентов)
Формат (уже поддерживается ETL, колонки матчатся fuzzy):
```
mrn,age,sex,date,ast,alt,plt
```
Требования к набору, чтобы демо было живым:
- Разброс по зонам FIB-4: часть **low** (молодые, нормальные AST/ALT, PLT>200), часть **grey** (пограничные), часть **high** (возраст 55+, AST 100–200, PLT 60–110).
- У части «high» дата анализа **старше 6 месяцев** от текущей даты (сейчас ~2026-07) — это делает их `is_lost=true` и наполняет worklist.
- У 2–3 пациентов **несколько строк с разными датами** (несколько заборов), чтобы график динамики (TrendChart) показывал тренд.
- `sex`: `male`/`female` (ETL сам маппит в 0/1).
- Значения клинически правдоподобные: AST/ALT в U/L, PLT в 10^9/L.

## Шаг 3 — автосид пациентов в `seed.py`
В `backend/app/db/seed.py`:
- Добавить функцию `seed_patients(db)`, которая **только если таблица `patient` пуста** вызывает `ingest_csv` демо-файлом:
  ```python
  from pathlib import Path
  from app.models.patient import Patient
  from app.services.etl import ingest_csv

  SEED_CSV = Path(__file__).parent / "seed_data" / "patients.csv"

  def seed_patients(db: Session) -> None:
      if db.query(Patient).count() > 0:
          return
      if not SEED_CSV.exists():
          return
      with open(SEED_CSV) as f:
          ingest_csv(f, db)
  ```
- В `main()` вызвать после `seed_users(db)`:
  ```python
  seed_users(db)
  seed_patients(db)
  ```
- Идемпотентность: гард `count() > 0` не даёт задваивать данные при повторных стартах.

## Шаг 4 — (опционально, но желательно) авто-scan после сида
Скоринг (`/cohort/scan`) наполняет таблицу `score` и вычисляет `is_lost`. Без него worklist пуст даже при наличии пациентов. Варианты:
- **A (рекомендую):** после `seed_patients` вызвать сервис скоринга напрямую (ту же логику, что в `api/cohort.py::scan`) в `seed.py`, чтобы `score` заполнялся при старте.
- **B:** оставить скан ручным (кнопка «Сканировать когорту» на фронте) — тогда просто задокументировать, что после старта надо нажать её один раз.
Если выбираешь A — вынеси тело функции `scan` из `api/cohort.py` в переиспользуемую функцию сервиса (`services/cohort_scan.py`), чтобы не дублировать код между API и сидом.

## Шаг 5 — не терять данные фронтового флоу
На фронте Worklist/CohortPage сейчас гейтятся по `localStorage.heparadar_scan_summary`. Даже при полной БД, если localStorage пуст, покажется «база не отсканирована». Исправить:
- Worklist должен **всегда** вызывать `getWorklist()` и показывать пустое состояние по фактическому `total===0`, а не по localStorage.
- localStorage-сводку использовать только как кэш для счётчика на ScanPage, не как условие показа данных.

## Шаг 6 — верификация (обязательно прогнать)
```
# из корня репо, бэк уже на :8000
curl -s -X POST http://localhost:8000/cohort/scan
curl -s "http://localhost:8000/cohort/worklist?page=1&page_size=5"
curl -s http://localhost:8000/patients/1
curl -s http://localhost:8000/patients/1/explain
```
Ожидаемо: scan → total ≈ 15–20, lost_count > 0; worklist непустой; карточка отдаёт labs+scores; explain для grey-пациента отдаёт `factors` (не 404).

Затем в браузере `http://localhost:5173`:
- ScanPage: счётчик показывает найденных;
- Worklist: список не пуст, фильтры/пагинация работают;
- Карточка: график динамики рисуется, SHAP-факторы реальные (не mock) для grey-зоны.

## Шаг 7 — пересоздать текущую dev.db и проверить с нуля
Так как проблема воспроизводится именно на свежей базе:
```
rm backend/dev.db
# перезапустить бэкенд (python -m app.db.seed выполнится и засеет юзеров + пациентов)
```
После рестарта БД должна сразу содержать пациентов **без** ручного ingest.

## Definition of Done
- Удаление `dev.db` + рестарт бэка → в базе автоматически есть демо-пациенты (patient/lab > 0).
- `/cohort/worklist` непустой без ручного `/ingest`.
- На фронте worklist показывает данные независимо от состояния localStorage.
- `npm run build` и `pytest` проходят.
- Демо-CSV лежит в `backend/app/db/seed_data/patients.csv`, `frontend/scratch/` удалён.
