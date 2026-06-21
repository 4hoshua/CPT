# Packet Tracer Extractor

A web app that wraps two Packet Tracer CLI scripts so they run anywhere
(Windows included) without WSL:

- **`ptexplorer.py`** — decodes a `.pkt`/`.pka` file into XML.
- **`extract_devices_cables.py`** — extracts devices & cables from that XML into JSON.

It ships a **FastAPI** backend (JWT login + the two conversions), a **Vite +
React/TS** frontend, and **NGINX** to serve the built frontend and reverse-proxy
the API — all wired together with **docker-compose**.

```
.pkt  ──/api/convert/xml──▶  XML  ──/api/convert/json──▶  JSON
```

---

## Quick start (Docker — recommended)

Requires Docker + Docker Compose.

```bash
# 1. Configure environment (set a real SECRET_KEY and admin credentials)
cp .env.example .env

# 2. Build and start
docker compose up --build
```

Then open **http://localhost** and log in with the credentials from `.env`
(defaults: `admin` / `admin`).

In the UI:

1. **.pkt → XML** — upload a `.pkt`/`.pka` file, download the decoded XML.
2. **XML → JSON** — upload that XML, view and download the devices & cables JSON.

Stop with `Ctrl+C`, or `docker compose down` (add `-v` to also wipe the user database).

> **Note:** only the frontend (port 80) is exposed. The backend is reachable
> only through NGINX at `/api`, on the internal compose network.

### Configuration (`.env`)

| Variable | Description | Default |
| --- | --- | --- |
| `SECRET_KEY` | JWT signing secret — generate with `openssl rand -hex 32` | `change-me-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `60` |
| `INITIAL_ADMIN_USERNAME` | Admin seeded on first startup | `admin` |
| `INITIAL_ADMIN_PASSWORD` | Admin password seeded on first startup | `admin` |
| `DATABASE_URL` | SQLite path inside the backend container | `sqlite:////data/app.db` |

The admin user is created **only on first startup** (when the database is empty).
The database persists in the `backend-data` Docker volume.

---

## API

| Method | Endpoint | Body | Auth | Returns |
| --- | --- | --- | --- | --- |
| `POST` | `/api/auth/login` | form: `username`, `password` | — | `{ access_token }` |
| `POST` | `/api/convert/xml` | multipart `file=@*.pkt` | Bearer | XML file |
| `POST` | `/api/convert/json` | multipart `file=@*.xml` | Bearer | JSON |

Example with `curl`:

```bash
TOKEN=$(curl -s -X POST -d "username=admin&password=admin" \
  http://localhost/api/auth/login | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $TOKEN" -F file=@atv.pkt \
  http://localhost/api/convert/xml -o outfile.xml

curl -H "Authorization: Bearer $TOKEN" -F file=@outfile.xml \
  http://localhost/api/convert/json -o topologia.json
```

---

## Local development (without Docker)

**Backend** (http://localhost:8000):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export SECRET_KEY=dev-secret        # Windows: set SECRET_KEY=dev-secret
uvicorn app.main:app --reload
```

**Frontend** (http://localhost:5173, proxies `/api` to the backend):

```bash
cd frontend
npm install
npm run dev
```

---

## Original CLI

The standalone scripts still work directly:

```bash
python3 ptexplorer.py -d atv.pkt outfile
python3 extract_devices_cables.py outfile -o topologia.json
```

---

## Project layout

```
backend/        FastAPI app (app/) + vendored scripts (pt/) + Dockerfile
frontend/       Vite + React/TS app + multi-stage Dockerfile + nginx.conf
docker-compose.yml
.env.example
```
