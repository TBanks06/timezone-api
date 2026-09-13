# Nigeria Timezone API

FastAPI service that converts Nigerian time (`Africa/Lagos`, WAT, UTC+1) to any
IANA timezone. Production-ready, containerised, and deployable to Render.

## Endpoints

| Method | Path          | Purpose                                 |
|--------|---------------|-----------------------------------------|
| GET    | `/`           | Service info                            |
| GET    | `/health`     | Health check (Render liveness probe)    |
| GET    | `/timezones`  | List IANA zones (optional `?region=`)   |
| GET    | `/convert`    | Convert NG time → target timezone       |

### Examples

```
GET /convert?target=America/New_York
GET /convert?target=Asia/Tokyo&dt=2026-09-13T09:00:00
GET /timezones?region=Africa
~~~

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Docs: <http://localhost:8000/docs>

## Deploy to Render

1. Push this repo to GitHub.
2. On Render, click **New → Web Service** → connect the repo.
3. Render auto-detects `render.yaml` and `Dockerfile`. Confirm and deploy.
4. Health check path is `/health`.

## Scaling notes

- **Horizontal**: stateless by design — add more instances behind a load balancer.
- **Workers**: the Dockerfile uses 4 gunicorn workers; raise to `2 * CPU cores`.
- **Caching**: for `/timezones`, add an in-memory TTL cache (`fastapi-cache` or
  `cachetools`) if you see hot paths.
- **Rate limiting**: the `RATE_LIMIT_PER_MINUTE` setting is wired but not
  enforced — plug in `slowapi` if you need it.
