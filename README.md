# DataPilot

Upload a CSV/XLSX file, get an instant summary, auto-generated charts, and AI-written insights — powered by a FastAPI + Pandas + Plotly backend and a React + TypeScript + Vite frontend.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router, Plotly |
| Backend | FastAPI, Pandas, Plotly |
| AI | Groq API (`llama-3.3-70b-versatile`) |

## Project Structure

```
DataPilot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point + CORS + router registration
│   │   ├── config.py            # Environment settings (pydantic-settings)
│   │   ├── routers/             # upload.py, analysis.py, insights.py
│   │   ├── services/             # data_loader, data_summary, chart_generator, insights_service
│   │   │   └── ai/               # AIProvider interface + factory + groq_provider (modular AI layer)
│   │   ├── models/schemas.py    # Pydantic request/response schemas
│   │   └── utils/file_validator.py
│   ├── uploads/                 # Uploaded datasets land here (gitignored contents)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/          # ui/, layout/, dashboard/, upload/, charts/, analytics/, chat/, common/
│   │   ├── pages/                # one file per route
│   │   ├── services/api.ts      # the only place that calls fetch()
│   │   ├── hooks/                # TanStack Query hooks
│   │   ├── types/api.ts         # API contract types
│   │   └── routes/
│   ├── package.json
│   └── vite.config.ts
├── sample_data/
│   └── sales_sample.csv         # a ready-made file to test uploads with
└── README.md
```

There is no root-level `requirements.txt` or `package.json` — each lives inside `backend/` and `frontend/` respectively, since those are two independently-run applications.

## What was fixed in this pass

This project had gone through several rounds of frontend/backend contract drift. The version in this folder has all of the following resolved:

- **Charts endpoint** — `ChartSpec`/`ChartsResponse` were being built with fields (`id`, `chart_type`, `columns`, `dataset_id`) that didn't exist on the schema, so every call to `/api/datasets/{id}/charts` threw a `ValidationError`. Now builds `title` / `type` / `figure` and `id` / `charts` as the schema (and frontend) actually expect.
- **AI Insights endpoint** — same category of bug (`InsightsResponse` built with `dataset_id`/`question` instead of `id`/`generated_at`), plus `_build_context()` referenced attributes (`memory_usage_mb`, `non_null`, `sample_values`) that don't exist on the summary objects. Both fixed; Groq API failures now raise properly instead of being returned as if they were a successful insight.
- **Analytics** — `DatasetSummary` was missing `missing_values_total`, which the frontend's Analytics page reads directly. Added to the schema and computed in `build_dataset_summary()`.
- **Upload robustness** — `utils/file_validator.py` existed but was never called; wired in, plus clean `400` responses on unsupported/corrupt files instead of an unhandled `500`.
- **Startup reliability** — `groq_api_key` was a required config field, so the backend would fail to start at all without one, even though Upload/Preview/Analytics/Charts don't need it. Now optional; only AI Insights needs it, and fails gracefully (`503`) if it's missing.
- **`requirements.txt`** — was missing `groq` (imported by `groq_insights.py`) entirely; a fresh install would `ImportError`.
- **`.env.example`** — still documented the old `GEMINI_API_KEY` from before the Groq migration; now documents `GROQ_API_KEY`.
- **Frontend build** — `vite.config.ts` uses Node's `path`/`__dirname`/`process` but `@types/node` was never a dependency, and `tsconfig.app.json`/`tsconfig.json` used the now-deprecated `baseUrl` alongside `paths`, which fails under current TypeScript. Both fixed; verified with a real `tsc -b` run — zero errors.

## AI provider architecture

AI Insights is built behind a small provider abstraction so a new LLM
provider can be added later without touching the router or the
insights-building logic:

- `app/services/ai/base.py` — `AIProvider` abstract class (one method:
  `generate(system_prompt, user_prompt) -> str`).
- `app/services/ai/groq_provider.py` — `GroqProvider`, the only provider
  implemented right now. Reads `GROQ_API_KEY` / `GROQ_MODEL` from settings.
- `app/services/ai/factory.py` — `get_ai_provider()` picks a provider from
  the `_PROVIDERS` registry using the `AI_PROVIDER` env var (default,
  and only supported value today: `groq`).
- `app/services/insights_service.py` — builds the dataset context/prompt
  (unchanged behavior) and calls whatever provider the factory returns.

To add another provider later (Gemini, OpenAI, ...): implement an
`AIProvider` subclass in its own module under `app/services/ai/`, add one
line to the `_PROVIDERS` dict in `factory.py`, and add its settings to
`config.py`. No changes needed in `routers/insights.py` or
`insights_service.py`. Gemini is intentionally **not** implemented in this
version — only Groq is wired up and tested.

Dashboard and History don't call the backend at all — they track recently-uploaded datasets in the browser's `localStorage` — so they work as soon as the frontend builds, independent of backend state.

## Run it

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then fill in GROQ_API_KEY
uvicorn app.main:app --reload
```

Runs at `http://localhost:8000`. Visit `http://localhost:8000/health` to confirm it's up — this works even without a Groq key.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env             # VITE_BACKEND_URL, defaults to localhost:8000
npm run dev
```

Runs at `http://localhost:5173`.

## Environment variables

**`backend/.env`**

| Variable | Required | Default | Notes |
|---|---|---|---|
| `AI_PROVIDER` | No | `groq` | Selects the AI provider from `app/services/ai/factory.py`. Only `groq` is implemented right now. |
| `GROQ_API_KEY` | Only for AI Insights/Reports | none | Get one at console.groq.com. Everything else runs fine without it. |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model name used for insight generation. |
| `UPLOAD_DIR` | No | `uploads` | Where uploaded files are stored on disk. |
| `MAX_UPLOAD_MB` | No | `50` | Rejects larger uploads with a `400`. |
| `CORS_ORIGINS` | No | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated. Note: `main.py` currently allows `*` regardless — see below. |

**`frontend/.env`**

| Variable | Required | Default | Notes |
|---|---|---|---|
| `VITE_BACKEND_URL` | No | `http://localhost:8000` | Also used by Vite's dev proxy for `/api/*`. |

> Note: `backend/app/main.py` currently sets CORS to `allow_origins=["*"]` rather than reading `settings.cors_origin_list`. This isn't broken (it still permits the frontend), just unused config — worth wiring up if you ever need credentialed requests or a stricter origin allowlist.

## Testing steps

1. **Health check** — `curl http://localhost:8000/health` → `{"status":"ok"}`. Confirms the backend started even with no Groq key set.
2. **Upload** — in the app, go to Upload, drop in `sample_data/sales_sample.csv`. Should redirect to a Dataset Preview page showing row/column counts.
3. **Preview** — confirm the row table loads, and search/sort/pagination work.
4. **Analytics** — open the Analytics tab for that dataset; confirm per-column stats render and the "Missing values" KPI card shows a number (not blank/crashed).
5. **Charts** — open Charts; confirm at least a histogram and, if the CSV has 2+ numeric columns, a correlation heatmap render.
6. **AI Insights** — open AI Chat, ask a question. Requires `GROQ_API_KEY` to be set; without it you should see a clean error message (503), not a blank crash.
7. **Reports** — click "Generate report" — same endpoint as Insights, different prompt.
8. **Dashboard / History** — upload 2–3 files, then check Dashboard shows the most recent one and History lists all of them. These are `localStorage`-backed, so they'll reset if you clear browser storage, and won't show datasets uploaded from a different browser/machine.
9. **Restart test** — stop and restart `uvicorn`. Old dataset IDs become invalid (in-memory store, by design) — confirm Preview/Analytics/Charts for a stale ID return a clean `404` rather than crashing, and that a fresh upload works immediately after restart.
