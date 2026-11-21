# AI-Powered Smart Food Waste Prediction and Fair Redistribution

Final Year Project monorepo. A decision-support system that predicts surplus food, filters and fairly ranks recipient organisations, and plans collection. Predictions are estimates only; food-safety rules and human oversight always apply.

| Part | Folder | Tech |
|---|---|---|
| Backend API | `backend/` | FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, scikit-learn, OR-Tools |
| Admin web panel | `admin/` | React 19 + Vite + TypeScript |
| Mobile app (donor / recipient) | `mobile/` | React Native + Expo + TypeScript |
| Docs | `docs/` | Implementation guide (SRS-based) |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (runs PostgreSQL and the backend)
- [Node.js](https://nodejs.org/) 20 or newer (admin panel, Expo, helper scripts)
- Git
- Optional: the **Expo Go** app on your Android phone, or Android Studio for an emulator

You do **not** need to install Python or PostgreSQL on your laptop. They run inside Docker.

## Quick start

```bash
git clone https://github.com/alisulmanpro/ai-powered-smart-food-waste-prediction-and-fair-redistribution.git
cd ai-powered-smart-food-waste-prediction-and-fair-redistribution

npm run setup     # creates .env files, installs admin + mobile dependencies
npm run up        # builds and starts PostgreSQL + backend (hot reload)
```

Then open:

| What | URL |
|---|---|
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

On the first start the backend container automatically waits for the database, applies the migrations, and seeds default data plus a first admin:

- Email: `admin@example.com`
- Password: `admin12345` (change it in `.env` before sharing or deploying)

In Swagger, click **Authorize** and log in with those credentials to try protected endpoints.

### Run the admin panel

Either on your laptop:

```bash
npm run admin:dev          # http://localhost:5173
```

or inside Docker together with the rest: `npm run up:admin`.

### Run the mobile app

```bash
npm run mobile:start       # then scan the QR code with Expo Go, or press "a" for an Android emulator
```

The phone cannot reach `localhost` of your laptop. Edit `mobile/.env`:

| Where the app runs | `EXPO_PUBLIC_API_URL` |
|---|---|
| Android emulator | `http://10.0.2.2:8000` |
| Physical phone (same Wi-Fi) | `http://<your-laptop-LAN-IP>:8000` (e.g. `http://192.168.1.20:8000`) |
| Web / iOS simulator | `http://localhost:8000` |

After changing `.env`, restart Expo with `npx expo start --clear` (run it inside `mobile/`). If the phone still cannot connect, allow port 8000 in your laptop firewall.

## Hot reload

- **Backend:** `./backend` is mounted into the container and uvicorn runs with `--reload`. Save a `.py` file and the API restarts by itself. File polling is enabled so this also works on Windows and macOS Docker.
- **Admin / mobile:** Vite and Expo reload as usual.
- Changed `requirements.txt`? Rebuild the image: `npm run up` (it passes `--build`).

## Daily commands

All of these run from the repo root (they use `docker compose` under the hood).

| Command | What it does |
|---|---|
| `npm run up` | Start db + backend with logs in the terminal |
| `npm run up:d` | Same, in the background |
| `npm run up:admin` | Also start the admin panel container |
| `npm run down` | Stop everything (data is kept) |
| `npm run reset` | Stop and **delete the database volume** (fresh start) |
| `npm run logs` | Follow backend logs |
| `npm test` | Run backend tests (uses a separate `foodwaste_test` database) |
| `npm run lint` / `npm run format` | Ruff lint / format for the backend |
| `npm run migrate` | Apply migrations (also done on container start) |
| `npm run makemigration -- "add donation index"` | Autogenerate a new Alembic migration after changing models |
| `npm run seed` | Re-run the (idempotent) seed |
| `npm run shell` | Shell inside the backend container |
| `npm run psql` | `psql` console in the database |

Prefer plain Docker? `docker compose up --build`, `docker compose exec backend pytest`, and so on work the same way.

## Project layout

```
.
├── docker-compose.yml        # db + backend (reload) + optional admin
├── .env.example              # copy to .env (npm run setup does it)
├── package.json              # the npm run ... shortcuts above
├── scripts/setup.mjs
├── backend/
│   ├── Dockerfile            # `dev` target (reload, pytest, ruff) and `prod` target
│   ├── app/                  # main.py, core/, db/, models/, schemas/, api/v1/, services/
│   ├── alembic/              # migrations (initial schema included)
│   ├── scripts/              # seed.py, wait_for_db.py, entrypoints
│   └── tests/
├── admin/                    # React admin panel
├── mobile/                   # Expo app
└── docs/implementation.md    # architecture, schema, API plan, build order
```

## What is already implemented

- Full PostgreSQL schema as SQLAlchemy models with an initial Alembic migration
- Auth: register (donor / recipient only), login (OAuth2 password flow, JWT), argon2 password hashes
- Server-side role checks (`require_roles`), audit log helper
- Profiles for donors and recipients, admin user listing, recipient verification, activate/deactivate, admin-created admins
- Health endpoints, CORS, seed data (categories, storage types, default allocation weights, first admin)
- 14 backend tests; admin and mobile apps that sign in against the API

Next steps (see `docs/implementation.md`): donations, historical data + prediction, eligibility and allocation, collection planning, dashboards.

## Troubleshooting

| Problem | Fix |
|---|---|
| `port is already allocated` | Change `BACKEND_PORT`, `DB_PORT` or `ADMIN_PORT` in `.env` |
| Backend does not reload on Windows | Make sure the repo is on a normal drive path, not inside a network share. Polling is already on |
| `database ... does not exist` / schema looks wrong | `npm run reset`, then `npm run up` |
| Mobile app says "API not reachable" | Fix `EXPO_PUBLIC_API_URL` (see table above), restart Expo with `npx expo start --clear` in `mobile/` |
| Changes in models not in the DB | `npm run makemigration -- "message"`, review the file in `backend/alembic/versions/`, then `npm run migrate` |

## Production notes

- Build the `prod` image target (`docker build --target prod ./backend`): no reload, non-root user.
- Set a strong `JWT_SECRET` (the app refuses to start in production with the default), change the admin password, and serve everything over HTTPS.
- Passwords are stored as salted argon2 hashes; never commit `.env`.
