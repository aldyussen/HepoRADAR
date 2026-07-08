# HepaRadar MVP — Архитектура, дерево проекта и план хакатона

<aside>
🩺

**HepaRadar** — движок, который прочёсывает существующую лабораторную базу и находит поимённый список пациентов с высоким риском фиброза/ХВГ, которых система «потеряла»: с объяснением по каждому (SHAP), готовым направлением (LLM) и мониторингом каскада ХВГ. Этот документ — единый рабочий план команды: архитектура → дерево проекта → лестница модулей × репозитории × почасовой график × критерии проверки.

</aside>

> Принцип сборки: 70% стека не пишем с нуля, а адаптируем из проверенных open-source репозиториев (хирургически — берём модуль/паттерн, а не тянем всю систему). Фундамент = case-finding; ML/LLM/каскад/FHIR — слои поверх, с фолбэками на моках, чтобы демо не падало.
> 

---

# 1. Обзор MVP

- **Одна фраза для жюри:** «Загрузите вашу базу — мы за 30 секунд покажем, кого вы потеряли».
- **Критический путь (не режется):** загрузка данных → расчёт FIB-4 по всей когорте → worklist «потерянных» → карточка пациента с объяснением.
- **Слои-усилители:** ML в серой зоне + SHAP, LLM-направление + reflex-флаг ХВГ, каскад-монитор, FHIR-выдача + CDS-Hooks.
- **Команда:** 4 вайбкодера — **BE** (backend), **ML** (модель+SHAP), **FE** (фронт+дашборд), **Lead/Integr** (данные, FHIR, демо, питч).

---

# 2. Полная архитектура

```
                     ┌─────────────────────────────┐
CSV / FHIR МИС  ─────▶│  ETL + LOINC-маппинг         │
(данные оргов)        │  (нормализация, качество)    │
                     └──────────────┬──────────────┘
                                    ▼
                     ┌─────────────────────────────┐
                     │  PostgreSQL (сырые + расчёт) │◀── FHIR store (Medplum/HAPI)
                     └──────────────┬──────────────┘
                                    ▼
         ┌──────────────────────────────────────────────┐
         │  СЛОЙ ПРАВИЛ: FIB-4 / APRI / De Ritis         │  (быстро, объяснимо)
         └──────────────┬───────────────────────────────┘
                        ▼
         ┌──────────────────────────────────────────────┐
         │  ML СЕРОЙ ЗОНЫ: XGBoost/LightGBM + SHAP       │  (там, где формула молчит)
         └──────────────┬───────────────────────────────┘
                        ▼
         ┌──────────────────────────────────────────────┐
         │  RANKING: приоритизация «потерянных»          │
         └──────────────┬───────────────────────────────┘
                        ▼
┌────────────────────────────────────────────────────────────────┐
│  FastAPI: REST + Auth(JWT/RBAC) + FHIR-выдача + CDS-Hooks        │
└───────────────┬───────────────────────────────┬────────────────┘
                ▼                               ▼
┌───────────────────────────┐     ┌───────────────────────────────┐
│  LLM (модель оргов) + RAG  │     │  React Dashboard (worklist,   │
│  направление / сводка      │     │  карточка, каскад, когорта)   │
└───────────────────────────┘     └───────────────────────────────┘
```

## Backend

- **Стек:** Python + **FastAPI** (тот же язык, что ML → нет второго рантайма), Uvicorn, SQLAlchemy, Pydantic.
- **Ответственность:** ETL-оркестрация, расчёт скоров, вызов ML и LLM, REST-API, авторизация, выдача FHIR-ресурсов, CDS-Hooks endpoint.
- **Почему так:** максимальная скорость вайбкодинга, вся ML-экосистема нативна, один процесс для демо.

## Frontend

- **Стек:** **React + Vite + TypeScript**, TailwindCSS, Recharts (графики), React Router, axios.
- **Ответственность:** экран сканирования с вау-счётчиком, worklist, карточка пациента (таймлайн + SHAP), каскад-воронка, обзор когорты, вход/роли.
- **Почему так:** быстрый HMR, чистый «Apple-like» UX (боль Reddit), готовые чарты.

## AI pipeline (ML)

1. **Признаки:** возраст, пол, AST, ALT, тромбоциты, (опц.) диабет, BMI, тренды показателей.
2. **Слой правил:** FIB-4 = (Возраст×AST)/(Тромбоциты×√ALT); APRI; De Ritis (AST/ALT). Разбивка на зоны low/grey/high.
3. **Модель серой зоны:** XGBoost/LightGBM, обучение на исходах в ретро-данных + перенос с открытых наборов (UCI HCV, ILPD).
4. **Объяснимость:** SHAP по каждому пациенту (топ-факторы риска).
5. **Выход:** risk-score + зона + объяснение + флаги качества данных.

## LLM pipeline

1. **Модель:** предоставленная организаторами (через их API-обёртку).
2. **RAG:** гайдлайны EASL/AASLD/WHO нарезаются → векторный индекс (Chroma/FAISS) → релевантные фрагменты в промпт.
3. **Задачи:** (а) текст направления к гепатологу; (б) краткая сводка «почему этот пациент в риске»; (в) обоснование со ссылкой на гайдлайн.
4. **Защита:** строгий шаблон-вывод, без свободного чата; при недоступности LLM — шаблон-фолбэк на правилах.

## Database

- **PostgreSQL** — основное хранилище: `patients`, `labs`, `scores`, `referrals`, `cascade_events`, `users`.
- **FHIR store** — **Medplum** (Apache 2.0) или HAPI: хранит/выдаёт данные как FHIR-ресурсы (Patient, Observation, DiagnosticReport, ServiceRequest).
- **Vector store** — Chroma для RAG-гайдлайнов.
- **Стратегия MVP:** расчёты и worklist читаем из Postgres (быстро); FHIR-слой — для интеграционной витрины и балла за зрелость.

## API (основные эндпоинты)

| Метод | Путь | Назначение |
| --- | --- | --- |
| POST | /auth/login | вход, выдача JWT |
| POST | /ingest | загрузка CSV/FHIR + запуск ETL |
| POST | /cohort/scan | прогон скоринга по всей базе (вау-момент) |
| GET | /cohort/worklist | ранжированный список «потерянных» + фильтры |
| GET | /patients/{id} | карточка: тренды, скоры, флаги |
| GET | /patients/{id}/explain | SHAP-объяснение |
| POST | /patients/{id}/referral | генерация направления (LLM) |
| GET | /cascade/hcv | данные каскада ХВГ + reflex-флаги |
| GET | /fhir/{ResourceType}/{id} | выдача FHIR-ресурса |
| POST | /cds-services/liver-risk | CDS-Hooks endpoint (карточка риска) |

## FHIR

- **Ресурсы:** Patient, Observation (лабы с LOINC), DiagnosticReport, RiskAssessment (наш скор), ServiceRequest (направление).
- **CDS-Hooks:** сервис `liver-risk` на хук `patient-view` — при открытии карты возвращает карточку «высокий риск фиброза + кнопка направления».
- **Смысл для жюри:** «встраивается в любую МИС без замены системы».

## Dashboard

1. **Scan screen** — большая кнопка + анимированный **счётчик найденных** (WOW).
2. **Worklist** — таблица приоритетных пациентов, бейджи зон, фильтры.
3. **Patient card** — таймлайн ALT/AST/тромбоцитов/FIB-4 + SHAP + кнопка «Направление».
4. **Cascade funnel** — воронка ХВГ скрининг→RNA→лечение→SVR с подсветкой потерь.
5. **Cohort overview** — распределение популяции по зонам риска.

## Авторизация

- **JWT** (access + refresh), пароли — bcrypt.
- **RBAC** — проверка роли на уровне зависимостей FastAPI.
- **MVP-упрощение:** сид-пользователи (без регистрации); OAuth/SMART-on-FHIR — в roadmap.

## Пользовательские роли

| Роль | Права |
| --- | --- |
| Врач (doctor) | worklist, карточка, SHAP, генерация направления |
| Координатор/медсестра (coordinator) | каскад ХВГ, reflex-флаги, возврат потерянных |
| Администратор (admin) | загрузка данных, пользователи, настройки порогов |
| Наблюдатель (viewer) | только чтение когорты и метрик (для жюри/менеджмента) |

## Поток данных (end-to-end)

```
1. Admin загружает CSV/FHIR → /ingest
2. ETL нормализует, маппит лаб-коды на LOINC, пишет в Postgres + FHIR store
3. /cohort/scan: слой правил считает FIB-4/APRI по всем → зоны low/grey/high
4. Для grey-зоны вызывается ML → уточнённый risk-score + SHAP
5. Ranking помечает «потерянных» (высокий риск, нет направления/диагноза)
6. Врач открывает worklist → карточку → видит объяснение
7. Жмёт «Направление» → LLM+RAG формирует текст → сохраняется как ServiceRequest (FHIR)
8. Координатор в каскаде видит anti-HCV+ без RNA → reflex-флаг → возврат пациента
```

---

# 3. Дерево проекта (каждая папка и файл)

```
hepa-radar/
├── docker-compose.yml            # postgres + medplum + backend + frontend одной командой
├── .env.example                 # шаблон переменных окружения
├── README.md                    # запуск проекта, ссылки на docs
│
├── backend/
│   ├── Dockerfile               # образ FastAPI
│   ├── requirements.txt         # зависимости backend
│   └── app/
│       ├── main.py              # точка входа FastAPI, CORS, монтаж роутеров
│       ├── config.py            # настройки из env: пороги FIB-4, пути к модели, URL LLM
│       ├── deps.py              # общие зависимости: сессия БД, текущий пользователь
│       ├── auth/
│       │   ├── router.py        # /auth/login, /auth/refresh
│       │   ├── jwt.py           # выпуск и проверка JWT
│       │   └── roles.py         # enum ролей + RBAC-проверки
│       ├── api/
│       │   ├── ingest.py        # приём CSV/FHIR, запуск ETL
│       │   ├── cohort.py        # /cohort/scan и /cohort/worklist + фильтры
│       │   ├── patients.py      # карточка пациента, тренды
│       │   ├── explain.py       # SHAP-объяснение по пациенту
│       │   ├── referral.py      # генерация направления через LLM
│       │   ├── cascade.py       # данные каскада ХВГ + reflex-флаги
│       │   └── fhir.py          # выдача FHIR-ресурсов + CDS-Hooks сервис
│       ├── services/
│       │   ├── etl.py           # загрузка/валидация/нормализация входных данных
│       │   ├── loinc_map.py     # словарь маппинга лаб-кодов МИС → LOINC
│       │   ├── scoring.py       # формулы FIB-4, APRI, De Ritis + зоны
│       │   ├── ranking.py       # логика приоритизации «потерянных»
│       │   ├── ml_infer.py      # загрузка модели, инференс, вызов SHAP
│       │   ├── llm_client.py    # обёртка над моделью организаторов
│       │   ├── rag.py           # ретрив фрагментов гайдлайнов для промпта
│       │   └── cascade_logic.py # этапы ХВГ, reflex-правила, потери
│       ├── models/              # ORM-модели (SQLAlchemy)
│       │   ├── patient.py       # таблица пациентов
│       │   ├── lab.py           # лабораторные показатели
│       │   ├── score.py         # рассчитанные скоры и зоны
│       │   ├── referral.py      # сформированные направления
│       │   └── user.py          # пользователи и роли
│       ├── schemas/             # Pydantic-схемы запросов/ответов
│       │   ├── patient.py
│       │   ├── cohort.py
│       │   ├── referral.py
│       │   └── fhir.py
│       └── db/
│           ├── session.py       # engine и сессия БД
│           ├── base.py          # базовый класс моделей, метаданные
│           └── seed.py          # сид пользователей и демо-данных
│   └── tests/
│       ├── test_scoring.py      # FIB-4/APRI = ручной расчёт на 10 примерах
│       ├── test_cohort.py       # санити: worklist не пустой и не вся база
│       ├── test_ranking.py      # «потерянные» помечаются корректно
│       └── test_cascade.py      # anti-HCV+ без RNA попадает во флаг
│
├── ml/
│   ├── README.md                # как обучить и экспортировать модель
│   ├── notebooks/
│   │   ├── eda.ipynb            # разведка данных, распределение зон FIB-4
│   │   └── train_greyzone.ipynb# эксперименты по обучению модели серой зоны
│   ├── src/
│   │   ├── features.py         # построение признаков из сырых лабов
│   │   ├── train.py            # обучение XGBoost/LightGBM
│   │   ├── evaluate.py         # метрики: AUC модели vs baseline FIB-4
│   │   ├── explain.py          # построение SHAP-эксплейнера
│   │   └── export.py           # сохранение модели и эксплейнера
│   └── models/
│       ├── greyzone_model.pkl  # обученная модель (артефакт)
│       └── shap_explainer.pkl  # сохранённый SHAP-эксплейнер
│
├── frontend/
│   ├── Dockerfile               # сборка статики фронта
│   ├── package.json             # зависимости фронта
│   ├── vite.config.ts           # конфиг Vite
│   ├── tailwind.config.js       # тема оформления
│   ├── index.html               # HTML-точка входа
│   └── src/
│       ├── main.tsx            # bootstrap React
│       ├── App.tsx             # маршрутизация страниц
│       ├── api/
│       │   ├── client.ts       # axios-инстанс + токен
│       │   ├── cohort.ts       # запросы worklist/scan
│       │   ├── patients.ts     # запросы карточки/тренды/SHAP
│       │   ├── referral.ts     # запрос генерации направления
│       │   └── cascade.ts      # запросы каскада ХВГ
│       ├── auth/
│       │   ├── AuthContext.tsx # состояние сессии, токены
│       │   ├── Login.tsx       # экран входа
│       │   └── RequireRole.tsx # guard доступа по роли
│       ├── pages/
│       │   ├── ScanPage.tsx    # кнопка сканирования + вау-счётчик
│       │   ├── WorklistPage.tsx# таблица «потерянных» + фильтры
│       │   ├── PatientPage.tsx # карточка: таймлайн + SHAP + направление
│       │   ├── CascadePage.tsx # воронка каскада ХВГ
│       │   └── CohortPage.tsx  # распределение популяции по зонам
│       ├── components/
│       │   ├── FoundCounter.tsx    # анимированный счётчик найденных (WOW)
│       │   ├── ScanButton.tsx      # кнопка запуска скана
│       │   ├── PatientTable.tsx    # таблица пациентов
│       │   ├── FilterBar.tsx       # фильтры по зоне/возрасту/маркерам
│       │   ├── RiskBadge.tsx       # цветной бейдж зоны риска
│       │   ├── LabTrendChart.tsx   # график динамики ALT/AST/тромбоцитов/FIB-4
│       │   ├── ShapExplanation.tsx # визуализация вклада факторов
│       │   ├── ReferralModal.tsx   # окно с текстом направления
│       │   └── CascadeFunnel.tsx   # воронка этапов ХВГ
│       ├── lib/
│       │   ├── fib4.ts         # клиентский пересчёт FIB-4 для наглядности
│       │   └── format.ts       # форматирование дат/чисел
│       └── styles/
│           └── index.css       # базовые стили Tailwind
│
├── data/
│   ├── synthea/                 # синтетические FHIR-пациенты для демо (без PHI)
│   └── guidelines/              # PDF EASL/AASLD/WHO для RAG-индекса
│
├── infra/
│   ├── medplum/                 # конфиг FHIR-хранилища
│   └── init.sql                 # инициализация схемы Postgres
│
└── docs/
    ├── architecture.md          # эта архитектура (копия для репо)
    ├── demo-script.md           # сценарий демо по шагам
    └── jury-qa.md               # вопросы жюри и ответы
```

---

# 4. Финальный план: лестница × репозитории × график × критерии

Лестница приоритетов: режем **снизу вверх** при нехватке времени. Фундамент (L1) не режется никогда. Каждый слой L3–L6 имеет мок-фолбэк.

| Слой | Модуль | Откуда «подсматриваем» (open-source) | Окно (часы) | Критерий проверки (verify) |
| --- | --- | --- | --- | --- |
| L0 | Час 0: проверка данных + каркас репо + docker-compose | [FastAPI](https://github.com/fastapi/fastapi)  • [Vite](https://github.com/vitejs/vite), docker-compose | 0–3 | compose поднимается; в данных есть AST/ALT/тромбоциты/возраст |
| 🟢 L1 | ETL + LOINC + FIB-4 + worklist «потерянных» | [fhir-server-dashboard](https://github.com/smart-on-fhir/fhir-server-dashboard) (идеи), свой ETL | 3–14 | на 10 пациентах FIB-4 = ручной расчёт; worklist не пуст и ≠ вся база |
| 🟢 L2 | ML серой зоны + SHAP | baseline [ILPD](https://archive.ics.uci.edu/dataset/225/ilpd+indian+liver+patient+dataset)/[HCV](https://archive.ics.uci.edu/dataset/571/hcv+data), [shap](https://github.com/shap/shap) | 10–22 | SHAP-топ-3 клинически осмысленны; (бонус) AUC &gt; baseline FIB-4 |
| 🟢 L1/L2 UI | Scan-счётчик + worklist + карточка + таймлайн | [charts-on-fhir](https://github.com/elimuinformatics/charts-on-fhir) (графики), [Recharts](https://github.com/recharts/recharts) | 14–30 | полный клик scan→worklist→карточка работает; счётчик анимируется |
| 🟡 L3 | LLM-направление + RAG на гайдлайнах | [the-momentum/fhir-mcp-server](https://github.com/the-momentum/fhir-mcp-server) (паттерн NL→FHIR) | 26–36 | кнопка выдаёт текст со всеми полями; фолбэк-шаблон при сбое LLM |
| 🟡 L4 | Reflex-флаг + каскад-воронка ХВГ | своя логика (≈20 строк) + [charts-on-fhir](https://github.com/elimuinformatics/charts-on-fhir) | 32–40 | тестовый anti-HCV+ без RNA попадает во флаг; воронка рисуется |
| 🔵 L5 | FHIR-выдача + CDS-Hooks endpoint | [medplum](https://github.com/medplum/medplum), [HL7/cds-hooks](https://github.com/HL7/cds-hooks), [srdc/smart-on-fhir-cds](https://github.com/srdc/smart-on-fhir-cds) | 36–42 | GET FHIR-ресурса валиден; CDS-сервис возвращает карточку |
| 🔵 L6 | Auth + роли (сид-пользователи) | [fastapi-users](https://github.com/fastapi-users/fastapi-users) паттерн, свой JWT | 18–24 (параллельно) | врач/координатор/админ видят разное; guard работает |
| ⚫ L7 (опц.) | Прогноз траектории FIB-4 | [vanderschaarlab/temporai](https://github.com/vanderschaarlab/temporai) | только если L1–L5 зелёные | прогноз рисуется на пациенте с ≥3 точками |
| 🏁 Финал | Полировка демо + питч + Q&amp;A | — | 42–48 | полный сценарий отрабатывает 3 раза подряд без падений |

## Почасовой график по ролям

| Часы | Lead/Integr | BE | ML | FE |
| --- | --- | --- | --- | --- |
| 0–3 | анализ данных, схема, риски | каркас FastAPI + БД | EDA данных | каркас Vite + роутинг |
| 3–14 | LOINC-маппинг, docker | ETL + FIB-4 + worklist API | признаки + обучение | Scan + worklist UI |
| 14–24 | Auth/роли + FHIR-заготовка | карточка/тренды API | SHAP + экспорт модели | карточка + графики |
| 24–36 | RAG-индекс + CDS-Hooks | referral API + интеграция ML | интеграция инференса | SHAP-виджет + модал направления |
| 36–42 | FHIR-выдача, каскад-данные | reflex + каскад API | валидация метрик | каскад-воронка + когорта |
| 42–48 | сборка демо, питч, репетиция | стабилизация, моки-фолбэки | слайд с метрикой | полировка UI, 3 прогона |

---

# 5. Правила, которые не отменяют ни вайбкодинг, ни open-source

- **Час 0 — данные, потом код.** Если нет признака «направлен ли пациент» → «потерянный» = высокий FIB-4 без последующего диагноза/визита. Решить до сборки.
- **Хирургия, не свалка.** Берём модуль/паттерн из репо, а не весь репо с зависимостями. Каждая строка ведёт к «найти забытых».
- **Понимай, что взял.** Любой заимствованный кусок объясним на вопрос жюри — иначе выкидываем.
- **Демо не падает.** Модули L3–L7 имеют мок-фолбэк; критерий финала — 3 прогона подряд.
- **Нарратив один:** «находим забытых и доводим до врача». ML — усилитель, не фундамент: если модель не обгонит FIB-4, L1 всё равно живёт.

---

# 6. Репозитории (прямые ссылки)

Всё проверено — ссылки рабочие. Правило то же: берём **модуль/паттерн точечно**, не тянем весь репозиторий с зависимостями.

## Код

| Репозиторий | Лицензия | Где в проекте | Что берём точечно / что НЕ тянем |
| --- | --- | --- | --- |
| [fastapi/fastapi](https://github.com/fastapi/fastapi) | MIT | backend/app/[main.py](http://main.py) | каркас REST; без лишних middleware |
| [fastapi-users/fastapi-users](https://github.com/fastapi-users/fastapi-users) | MIT | backend/app/auth/ | паттерн JWT + current_user; берём подход, не всю либу с регистрацией/OAuth |
| [canvas-medical/fhirstarter](https://github.com/canvas-medical/fhirstarter) | MIT | backend/app/api/[fhir.py](http://fhir.py) | паттерн FHIR-роутов на FastAPI + fhir.resources; не весь framework |
| [medplum/medplum](https://github.com/medplum/medplum) | Apache 2.0 | infra/medplum (FHIR store) | self-host FHIR + Auth; запускаем как сервис, не форкаем монорепо |
| [hapifhir/hapi-fhir-jpaserver-starter](https://github.com/hapifhir/hapi-fhir-jpaserver-starter) | Apache 2.0 | альтернатива FHIR store | если medplum тяжёл — Java FHIR-сервер из коробки (Docker) |
| [HL7/cds-hooks](https://github.com/HL7/cds-hooks) | Apache 2.0 | api/[fhir.py](http://fhir.py) (CDS-Hooks) | формат карточек и discovery-ответа; берём спецификацию, не код |
| [srdc/smart-on-fhir-cds](https://github.com/srdc/smart-on-fhir-cds) | уточнить | api/[fhir.py](http://fhir.py) (CDS-Hooks) | рабочий пример CDS-Hooks сервиса как референс; не копируем целиком |
| [the-momentum/fhir-mcp-server](https://github.com/the-momentum/fhir-mcp-server) | уточнить | services/llm_[client.py](http://client.py), [rag.py](http://rag.py) | паттерн LLM↔FHIR + валидация LOINC; берём подход, не MCP-слой |
| [elimuinformatics/charts-on-fhir](https://github.com/elimuinformatics/charts-on-fhir) | Apache 2.0 | LabTrendChart, CascadeFunnel | паттерн графиков по FHIR Observation |
| [smart-on-fhir/fhir-server-dashboard](https://github.com/smart-on-fhir/fhir-server-dashboard) | уточнить | CohortPage | идея обзора когорты и распределений |
| [shap/shap](https://github.com/shap/shap) | MIT | ml/src/[explain.py](http://explain.py) | объяснимость из коробки (TreeExplainer) |
| [dmlc/xgboost](https://github.com/dmlc/xgboost) · [microsoft/LightGBM](https://github.com/microsoft/LightGBM) | Apache 2.0 · MIT | ml/src/[train.py](http://train.py) | модель серой зоны |
| [vanderschaarlab/temporai](https://github.com/vanderschaarlab/temporai) | Apache 2.0 | L7 (опц.) прогноз траектории | survival/forecast медицинских рядов; только при ≥3 точках |
| [chroma-core/chroma](https://github.com/chroma-core/chroma) | Apache 2.0 | services/[rag.py](http://rag.py) | вектор-стор для гайдлайнов |
| [synthetichealth/synthea](https://github.com/synthetichealth/synthea) | Apache 2.0 | data/synthea/ | синтетические FHIR-пациенты для демо без PHI |

## Датасеты для обучения

| Датасет | Объём | Назначение |
| --- | --- | --- |
| [UCI ILPD](https://archive.ics.uci.edu/dataset/225/ilpd+indian+liver+patient+dataset) | 583 записи | baseline печёночной модели (AST/ALT/билирубин/альбумин) |
| [UCI HCV data](https://archive.ics.uci.edu/dataset/571/hcv+data) | 615 записей | маркеры HCV, стадии фиброза |
| [Kaggle: Indian Liver Patient Records](https://www.kaggle.com/datasets/uciml/indian-liver-patient-records) | 583 записи | тот же ILPD, удобный CSV для быстрого старта |
| [Kaggle: Hepatitis C Prediction](https://www.kaggle.com/datasets/fedesoriano/hepatitis-c-dataset) | 615 записей | HCV в CSV, готов к обучению |

## Чёткий разбор (чтобы не запутаться)

<aside>
🎯

**Критический путь = только 4 репо:** FastAPI + xgboost/LightGBM + shap + charts-on-fhir/Recharts. Без них продукта нет.

**FHIR-слой (medplum / hapi / cds-hooks / srdc) — НЕ на критическом пути.** Он даёт «балл за зрелость» и фразу «встраивается в любую МИС», но включаем его только когда L1–L2 уже зелёные. Если времени нет — режется без потери ядра.

**Лицензии:** всё ключевое — Apache 2.0 или MIT, свободно для хакатона и продакшена. Три репо помечены «уточнить» (srdc, fhir-mcp-server, fhir-server-dashboard) — их берём **как референс-паттерн**, а не копируем код целиком, поэтому лицензионный риск нулевой.

**Против «свалки зависимостей»:** medplum и hapi запускаем как готовый Docker-сервис (не форкаем исходники); из fhir-mcp-server и srdc берём только схему запроса/ответа. Каждая заимствованная строка должна быть объяснима на вопрос жюри.

</aside>