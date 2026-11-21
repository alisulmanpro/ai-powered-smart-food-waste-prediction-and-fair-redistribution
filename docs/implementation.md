# Implementation Guide — AI-Powered Smart Food Waste Prediction and Fair Redistribution

Based on SRS v2.0 (November 2026). Stack: React Native (Expo) + React admin + FastAPI + PostgreSQL + scikit-learn + OR-Tools + OSM routing.

---

## 1. Assumed Defaults (to confirm with supervisor)

These close the open issues enough to start building. Change them later in one place (config), not across the code.

| Open issue | Assumed default |
|---|---|
| OI-02 Data | Start with **synthetic data** (clearly labelled, BR-07). Swap in real CSVs if a business agrees. |
| OI-03 Fairness | Report **Gini coefficient** of received quantity across verified recipients + **demand fulfilment ratio** per recipient. |
| OI-04 Weights | need 0.30, capacity_fit 0.15, urgency 0.20, distance 0.15, fairness (past share) 0.20. Admin can edit. |
| OI-07 Notifications | Push (FCM) + in-app list only. Recipient response window: **60 minutes**. |
| OI-09 Platform | React Native + Expo, **Android only** (iOS if time permits). |
| OI-10 Collection | **Recipient organisation collects.** No separate collector role. |
| OI-11 Language | English only. |
| OI-13 Status | Fully rejected donation stays **Offered** with flag `needs_manual_allocation = true` (no new status). |

---

## 2. MVP vs Later

**MVP (Must):** auth + roles, recipient verification, donation CRUD + validation + statuses, CSV upload + cleaning, baseline + 3 ML models with MAE/RMSE, model versioning, donor sees estimate, eligibility filter, scored allocation with reasons, admin approve/override + audit log, nearest-match baseline, collection order + infeasible flag, mark Collected/Missed, core dashboards + fairness metric, experiment comparison (proposed vs nearest).

**Should:** profile edit, activate/deactivate users, push notifications + inbox, accept/decline with timeout and auto-reassign, model-version "current" flag, configurable weights/categories, demand dashboard, token timeout.

**Could (cut first if late):** feature-importance explanation (FR-PR-10), manual route reorder (FR-CP-06), CSV report export (FR-DB-07), notification toggle (FR-NT-03).

---

## 3. Architecture

```
 Expo Mobile App (donor / recipient)      React Admin Panel (admin)
              \                                  /
               \------ REST + JSON over HTTPS ---/
                              |
                        FastAPI backend
        +---------+-----------+------------+-------------+
        | auth/   | donations | prediction | allocation  |  <- separate modules (NFR-MT-01)
        | users   |           | (sklearn)  | (rules +    |
        |         |           |            |  OR-Tools)  |
        +---------+-----------+------------+-------------+
                |             |                |
           PostgreSQL     joblib model     OSRM routing (OSM)
                          files on disk    FCM push
```

Rules:
- `prediction` and `allocation` never import each other. Allocation only reads confirmed donations.
- Eligibility is a plain Python function with unit tests. It runs **before** any scoring and cannot be bypassed (BR-02, BR-03).

---

## 4. Repository Structure

Monorepo. Everything below already exists in the repo; items marked *(todo)* are built during the project.

```
.
├── docker-compose.yml        # db + backend (hot reload) + optional admin
├── .env.example              # copy to .env (npm run setup does it)
├── package.json              # convenience scripts: npm run up / test / migrate ...
├── scripts/setup.mjs         # one-command local setup
├── backend/                  # FastAPI
│   ├── Dockerfile            # targets: dev (reload + tests) and prod
│   ├── app/
│   │   ├── main.py
│   │   ├── core/             # config.py, security.py (JWT, argon2)
│   │   ├── db/               # session.py, base.py
│   │   ├── models/           # all SQLAlchemy models (section 5 schema)
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── api/              # deps.py (auth + role checks), v1/{auth,users,admin,health}.py
│   │   ├── audit.py
│   │   └── services/
│   │       ├── prediction/   # (todo) ingest, features, train, predict
│   │       ├── allocation/   # (todo) eligibility, scoring, assign, nearest
│   │       └── planning/     # (todo) routing, order
│   ├── alembic/              # migrations (initial schema included)
│   ├── scripts/              # seed.py, wait_for_db.py, entrypoints
│   └── tests/                # pytest (runs against a <db>_test database)
├── admin/                    # React + Vite + TypeScript
├── mobile/                   # Expo (React Native) + TypeScript
└── docs/                     # this file, SRS, experiment results
```

---

## 5. Database Schema (PostgreSQL)

```sql
CREATE TYPE user_role AS ENUM ('donor','recipient','admin');
CREATE TYPE donation_status AS ENUM
  ('offered','allocated','accepted','collected','missed','expired','cancelled');
CREATE TYPE alloc_status AS ENUM
  ('recommended','approved','overridden','accepted','declined','timed_out');

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role user_role NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  fcm_token TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE donor_profiles (
  user_id INT PRIMARY KEY REFERENCES users(id),
  business_name TEXT NOT NULL,
  business_type TEXT,
  address TEXT, latitude DOUBLE PRECISION, longitude DOUBLE PRECISION
);

CREATE TABLE recipient_profiles (
  user_id INT PRIMARY KEY REFERENCES users(id),
  organisation_name TEXT NOT NULL,
  address TEXT, latitude DOUBLE PRECISION, longitude DOUBLE PRECISION,
  capacity_units INT NOT NULL,
  storage_types TEXT[] NOT NULL,        -- e.g. {'ambient','chilled','frozen'}
  accepted_categories TEXT[] NOT NULL,
  open_from TIME, open_to TIME,
  need_level SMALLINT CHECK (need_level BETWEEN 1 AND 5),
  verified BOOLEAN DEFAULT FALSE
);

CREATE TABLE food_categories (id SERIAL PRIMARY KEY, name TEXT UNIQUE);
CREATE TABLE storage_types   (id SERIAL PRIMARY KEY, name TEXT UNIQUE);

CREATE TABLE historical_data (
  id SERIAL PRIMARY KEY,
  donor_id INT REFERENCES donor_profiles(user_id),
  date DATE NOT NULL,
  meal_period TEXT,
  food_category TEXT NOT NULL,
  prepared_amount NUMERIC, sold_amount NUMERIC, leftover_amount NUMERIC,
  is_event BOOLEAN DEFAULT FALSE,
  is_synthetic BOOLEAN DEFAULT FALSE
);

CREATE TABLE model_versions (
  id SERIAL PRIMARY KEY,
  algorithm TEXT NOT NULL,
  trained_at TIMESTAMPTZ DEFAULT now(),
  mae NUMERIC, rmse NUMERIC,
  file_path TEXT,
  active BOOLEAN DEFAULT FALSE
);

CREATE TABLE predictions (
  id SERIAL PRIMARY KEY,
  donor_id INT REFERENCES donor_profiles(user_id),
  date DATE, category TEXT,
  predicted_amount NUMERIC,
  model_version_id INT REFERENCES model_versions(id)
);

CREATE TABLE donations (
  id SERIAL PRIMARY KEY,
  donor_id INT REFERENCES donor_profiles(user_id),
  prediction_id INT REFERENCES predictions(id),     -- optional link
  category TEXT NOT NULL,
  confirmed_amount NUMERIC NOT NULL CHECK (confirmed_amount > 0),
  unit TEXT DEFAULT 'units',
  available_from TIMESTAMPTZ NOT NULL,
  deadline TIMESTAMPTZ NOT NULL,
  storage_requirements TEXT NOT NULL,
  pickup_lat DOUBLE PRECISION, pickup_lng DOUBLE PRECISION,
  notes TEXT,
  status donation_status DEFAULT 'offered',
  needs_manual_allocation BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now(),
  CHECK (deadline > available_from)
);

CREATE TABLE allocations (
  id SERIAL PRIMARY KEY,
  donation_id INT REFERENCES donations(id),
  recipient_id INT REFERENCES recipient_profiles(user_id),
  rank SMALLINT,
  score NUMERIC,
  reasons JSONB,                      -- per-criterion contributions
  status alloc_status DEFAULT 'recommended',
  decided_by INT REFERENCES users(id),
  override_reason TEXT,
  respond_by TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE collection_plans (
  id SERIAL PRIMARY KEY,
  plan_date DATE,
  ordered_stops JSONB,                -- [{allocation_id, eta, leg_minutes}]
  est_distance_km NUMERIC, est_time_min NUMERIC,
  feasibility_flags JSONB
);

CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  type TEXT, message TEXT,
  sent_at TIMESTAMPTZ DEFAULT now(),
  read BOOLEAN DEFAULT FALSE
);

CREATE TABLE settings (key TEXT PRIMARY KEY, value JSONB);   -- weights, response window

CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  action TEXT, entity TEXT, entity_id INT,
  details JSONB, at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON donations (status, deadline);
CREATE INDEX ON allocations (donation_id);
CREATE INDEX ON historical_data (donor_id, date);
```

Use Alembic for migrations. Seed `settings` with default weights and `food_categories` / `storage_types`.

---

## 6. API Endpoints

All under `/api/v1`. JWT bearer auth. Role checks happen **server-side** via a dependency (NFR-SC-03).

| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/auth/register` | public | Register donor/recipient (admin role rejected) |
| POST | `/auth/login` | public | Returns access token |
| GET/PUT | `/users/me` | any | View/edit own profile |
| GET | `/admin/users?role=&verified=` | admin | List users |
| POST | `/admin/users/{id}/verify` | admin | Verify recipient |
| PATCH | `/admin/users/{id}/active` | admin | Activate/deactivate |
| POST | `/admin/admins` | admin | Create admin account |
| POST | `/donations` | donor | Create donation (validated) |
| GET | `/donations` | donor/admin | Own list / all |
| PATCH | `/donations/{id}` | donor | Edit until allocated |
| POST | `/donations/{id}/cancel` | donor | Cancel until allocated |
| POST | `/donations/{id}/collect` | recipient/admin | Mark collected |
| POST | `/donations/{id}/missed` | recipient/admin | Mark missed |
| POST | `/data/upload` | admin | Upload historical CSV |
| POST | `/models/train` | admin | Train baseline + 3 models, store metrics |
| GET | `/models` | admin | List versions with MAE/RMSE |
| POST | `/models/{id}/activate` | admin | Mark current |
| GET | `/predictions?date=&category=` | donor/admin | Estimated surplus (labelled estimate) |
| GET | `/allocations/review` | admin | Offered donations with ranked recommendations |
| POST | `/allocations/{donation_id}/run` | admin/system | Run filter + ranking |
| POST | `/allocations/{id}/approve` | admin | Approve |
| POST | `/allocations/{id}/override` | admin | Pick another recipient + reason |
| GET | `/allocations/inbox` | recipient | Allocations awaiting response |
| POST | `/allocations/{id}/accept` | recipient | Accept |
| POST | `/allocations/{id}/decline` | recipient | Decline → next recipient |
| POST | `/collections/plan` | admin | Build order + ETAs |
| GET | `/collections/{id}` | admin | Plan details |
| PUT | `/collections/{id}/order` | admin | Manual reorder (Could) |
| GET | `/dashboard/admin` | admin | All metrics |
| GET | `/dashboard/me` | donor/recipient | Own summary |
| GET | `/reports/export.csv` | admin | CSV export (Could) |
| POST | `/experiments/run` | admin | Proposed vs nearest-match on scenario set |
| GET/PUT | `/settings` | admin | Weights, categories, storage types, response window |
| GET | `/notifications` | any | List |
| POST | `/notifications/{id}/read` | any | Mark read |
| POST | `/devices/token` | any | Save FCM token |

FastAPI generates OpenAPI at `/docs` automatically (NFR-MT-03).

---

## 7. Module Implementation

### 7.1 Surplus Prediction (Module A)

**Pipeline** (`services/prediction/`):

1. `ingest.py`: read CSV with pandas. Required columns: `date, business, food_type, prepared, sold, leftover, special_event`. Drop/report invalid rows (negative values, bad dates, `sold > prepared`). Fill missing numeric values with the per-category median, or drop if the target is missing. Return `(clean_df, rejected_rows_with_reason)`.
2. `features.py`: `dow`, `month`, `season`, `is_event`, `category` (one-hot), `lag_7_leftover` (same weekday last week), `rolling_7_mean`. Target = `leftover`.
3. `train.py`:
   - Sort by date and split **by time** (e.g. first 80% train, last 20% test).
   - Baseline = mean leftover per (category, weekday) from training data.
   - Models: `LinearRegression`, `RandomForestRegressor(n_estimators=200, random_state=42)`, `GradientBoostingRegressor(random_state=42)`.
   - Compute MAE and RMSE on test, save each model with `joblib` to `models/{algo}_{timestamp}.joblib`, insert row in `model_versions`.
4. `predict.py`: load the `active` model, build the feature row for (date, category, donor), return `max(0, pred)` rounded. Always return `{"estimate": x, "model_version": id, "is_estimate": true}`.

**Acceptance check:** at least one ML model beats the baseline on MAE/RMSE. Record negative results as well.

**Synthetic data** (`scripts/generate_synthetic_data.py`): 6–12 months, 3–5 businesses, 3–4 categories. Leftover = base × weekday factor (weekends higher) × event bump × noise. Set `is_synthetic = true` on every row and mention it in all reports (BR-07).

### 7.2 Donation Management (Module B)

- Pydantic validation: all fields present, `confirmed_amount > 0`, `deadline > available_from`, `deadline > now()`.
- State machine (enforce in one function `transition(donation, new_status)`):
  - `offered → allocated → accepted → collected | missed`
  - `offered | allocated → cancelled` (donor)
  - `offered | allocated | accepted → expired` (background job when `deadline < now()`)
- Edit/cancel only while status is `offered` or `allocated`.
- **Never create a donation from a prediction automatically.** The create endpoint requires `confirmed_amount` from the donor (FR-DN-05).

### 7.3 Eligibility and Fair Allocation (Module C)

**Step 1 — Eligibility (hard rules).** `eligibility.py`:

```python
def is_eligible(donation, recipient, now) -> tuple[bool, str | None]:
    if not recipient.verified:
        return False, "recipient not verified"
    if donation.category not in recipient.accepted_categories:
        return False, "category not accepted"
    if donation.storage_requirements not in recipient.storage_types:
        return False, "storage requirement not met"
    if donation.confirmed_amount > recipient.capacity_units:
        return False, "exceeds capacity"
    eta = now + travel_time(donation.pickup, recipient.location)
    if eta > donation.deadline:
        return False, "cannot reach before deadline"
    if not within_hours(recipient, eta):
        return False, "closed at arrival"
    return True, None
```

Write unit tests for every branch (NFR-MT-02). Scores are never consulted here.

**Step 2 — Scoring.** `scoring.py`: each criterion normalised to 0–1:

| Criterion | Formula |
|---|---|
| need | `(need_level - 1) / 4` |
| capacity_fit | `min(amount / capacity, 1)` (prefer recipients who can use most of it) |
| urgency | `1 - (time_to_deadline / max_window)` clipped, same for all recipients, so combine with recipient's remaining open time |
| distance | `1 - (dist_km / max_dist_km)` |
| fairness | `1 - (recipient_received_30d / max_received_30d)` |

`score = Σ weight_i × criterion_i`. Store `reasons = {criterion: {value, weight, contribution}}` as JSON so the admin screen can show the breakdown (FR-AL-05).

**Step 3 — Assign.** For a single donation: sort eligible by score, save top N (e.g. 3) as `recommended` with `rank`. For a batch of donations on the same day, use OR-Tools (`pywraplp` or CP-SAT) to maximise total score with each donation assigned to ≤ 1 recipient and recipient capacity respected.

**Step 4 — Human control.** Admin approves rank 1 or overrides with a reason (required). Both actions write to `audit_log`. On approve: donation → `allocated`, set `respond_by = now + 60 min`, send push.

**Step 5 — Accept/decline.** Recipient accepts → donation `accepted`. Decline or timeout (background task every minute) → mark `declined/timed_out`, promote next ranked recommendation; if none left set `needs_manual_allocation = true`.

**Baseline (`nearest.py`):** among eligible recipients choose the closest. Used only in experiments (FR-AL-10).

### 7.4 Collection Planning (Module D)

- `routing.py`: call OSRM `GET /route/v1/driving/{lng,lat;lng,lat}` (public demo server for development; self-host OSRM if rate-limited). Cache results per coordinate pair. If it fails, fall back to haversine ÷ 30 km/h and show a "routing unavailable, estimates only" message (NFR-RL-03).
- `order.py`: for ≤ 10 stops, build a travel-time matrix and solve with OR-Tools Routing with time windows (window = `[available_from, deadline]`). If a stop has no feasible slot, mark it `infeasible` (FR-CP-03). Return ordered stops with ETAs and total distance/time.
- UI must label all times as **estimates** (FR-CP-04, NFR-US-04).

### 7.5 Dashboards and Reporting (Module E)

SQL aggregate queries in `services/metrics.py`; charts in the admin panel (Recharts or Plotly.js):

- Predicted vs confirmed surplus over time
- Offered / redistributed / uncollected quantity
- Collected vs missed, % collected before deadline
- Demand by recipient and unfulfilled requests
- Fairness: Gini coefficient of received quantity + demand fulfilment ratio per recipient
- Donor/recipient mobile summary: only their own data (`/dashboard/me`)

Gini helper:

```python
def gini(values):
    v = sorted(values); n = len(v)
    if n == 0 or sum(v) == 0: return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(v))
    return (2 * cum) / (n * sum(v)) - (n + 1) / n
```

### 7.6 Experiments (FR-AD-04)

`scripts/run_experiment.py` (and `/experiments/run`):
1. Generate or load N scenarios (e.g. 30 days of donations + recipient set).
2. Run each scenario with **proposed method** and **nearest-match**.
3. Record: on-time collection rate, total food redistributed, unfulfilled requests, distribution (Gini).
4. Save a table to `docs/experiment_results.csv` and show it in the admin dashboard.

---

## 8. Mobile App (Expo + TypeScript)

**Libraries:** `expo-router`, `axios`, `@tanstack/react-query`, `zustand`, `react-hook-form` + `zod`, `expo-secure-store` (tokens, NFR-SC-06), `expo-location`, `react-native-maps`, `expo-notifications`.

| Screen | Role | Notes |
|---|---|---|
| Sign in / Sign up | all | Role picker (donor/recipient only) |
| Donor home | donor | Estimated surplus card (labelled "Estimate"), create button, donation list |
| Create/Edit donation | donor | GPS or map pin with manual correction, inline field errors |
| Recipient profile | recipient | Capacity, storage, categories, hours, need level |
| Allocation inbox | recipient | Donation details, deadline countdown, Accept/Decline |
| Pickup status | both | Location, deadline, status |
| Notifications / Summary | both | List + own stats |

Implementation notes:
- Keep form state if the network drops, show a retry banner (NFR-RL-04).
- Touch targets ≥ 44 px (NFR-US-05).
- Show a fixed footer note: "Decision support only. Follow food-safety rules." (NFR-SF-01).
- Never display anything implying food is safe (NFR-SF-02).

---

## 9. Admin Panel (React + Vite)

Pages: Sign in · Verify Users · Review Allocations (reason breakdown, approve/override) · Plan Collections (ordered stops, ETAs, infeasible flags) · Data & Models (CSV upload, model table with MAE/RMSE, activate) · Dashboards · Settings & Audit Log (weights, categories, storage types, response window).

Use React Router, React Query, a table library (TanStack Table), and Recharts. Protect every route with a role check, but the backend remains the real gatekeeper.

---

## 10. Security Checklist

- Passwords: argon2id salted hashes via `argon2-cffi` (NFR-SC-01). JWT via `PyJWT`.
- JWT access token with short expiry (e.g. 60 min) + refresh; store in SecureStore on mobile (NFR-SC-05, 06).
- HTTPS in deployment (Caddy/Nginx + Let's Encrypt, or the host's TLS).
- SQLAlchemy ORM / parameterised queries only (NFR-SC-04).
- Per-endpoint role dependencies; donors see only own donations, recipients only own allocations (NFR-PV-03).
- Admin accounts created only by another admin (seed the first admin via a CLI script).
- CORS limited to the admin origin. Rate-limit login.
- Secrets in `.env`, never committed.
- Daily `pg_dump` backup (NFR-RL-02).

---

## 11. Testing Plan

| Level | What | Tool |
|---|---|---|
| Unit | Eligibility branches, scoring, Gini, status transitions, CSV validation | pytest |
| API | Auth, role access (negative tests), donation validation, allocation flow | pytest + FastAPI TestClient |
| ML | Time-split has no leakage, MAE/RMSE computed, ≥ 1 model beats baseline | pytest + script |
| Experiment | Proposed vs nearest on same scenarios | `run_experiment.py` |
| Usability | Task-based test: donor submits a donation in ~5 min (NFR-US-01) | Manual, 5+ users |
| Performance | Ranking 100 recipients < 5 s, plan 10 stops < 10 s, prediction < 2 s | Simple timing script |
| Device | Android 8+ on a mid-range phone, 360×640 dp | Manual |

---

## 12. Build Order (16-week plan)

| Weeks | Work | Done when |
|---|---|---|
| 1–2 | Finalise assumptions above, repo setup, Docker Compose (Postgres), Alembic, auth skeleton | Login works, roles enforced |
| 3–4 | Synthetic data generator, schema complete, seed data | DB populated, CSV format fixed |
| 5–7 | Ingest, features, baseline + 3 models, metrics, model versioning | Metrics table shows ≥ 1 model beating baseline |
| 8–10 | Donation APIs + state machine, recipient profile, mobile screens, admin verify/users | Donor can create donation on phone |
| 11–13 | Eligibility, scoring, review UI, accept/decline, OSRM + OR-Tools planning, dashboards | Full flow: donate → allocate → plan → collect |
| 14–15 | Notifications polish, experiments, testing, bug fixes, docs | Experiment table + test report ready |
| 16 | Final report, demo data, presentation, viva prep | Demo runs end-to-end offline-safe |

**Suggested order inside each week:** backend endpoint → test → admin/mobile screen → manual check. Commit at least daily with clear messages.

---

## 13. Local Setup

See the root `README.md` for the full guide. Short version:

```bash
git clone <repo-url> && cd <repo>
npm run setup      # creates .env files, installs admin + mobile deps
npm run up         # Postgres + backend with hot reload -> http://localhost:8000/docs
npm run mobile:start
```

Backend dependencies are pinned in `backend/requirements.txt` (fastapi, uvicorn, SQLAlchemy 2, alembic,
psycopg 3, pydantic-settings, PyJWT, argon2-cffi, pandas, numpy, scikit-learn, joblib, ortools, httpx).
`firebase-admin` is not installed yet: add it when push notifications are implemented.

---

## 14. Definition of Done

- All **Must** requirements in the SRS pass their tests.
- At least one ML model beats the baseline on MAE/RMSE; all results recorded, including negative ones.
- Experiment table compares proposed allocation with nearest-match on identical scenarios.
- Every override has a reason and an audit-log row.
- Estimates are labelled as estimates everywhere; the safety disclaimer is visible.
- Synthetic data (if used) is labelled in the UI, documentation and report.
- Setup steps and API docs are written and the code is in version control.
