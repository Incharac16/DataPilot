# DataPilot

DataPilot is a local web application for uploading CSV/XLSX datasets, browsing and searching their rows, reviewing deterministic analytics and data-quality checks, viewing automatically generated Plotly charts, asking Groq for a grounded explanation, and exporting a PDF report.

## Stack

- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router, Plotly
- **Backend:** FastAPI, Pandas, SQLite (standard library), Plotly, ReportLab
- **AI:** Groq through the existing provider interface (`GROQ_MODEL` defaults to `openai/gpt-oss-20b`)

## Repository layout

```text
DataPilot/
├── backend/
│   ├── app/
│   │   ├── routers/       # Upload/history, analytics/charts/PDF, AI insights
│   │   ├── services/      # Loading, profiling, charting, facts, reports, AI
│   │   ├── models/        # Pydantic API contracts
│   │   └── utils/
│   ├── tests/             # unittest + FastAPI TestClient tests
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── routes/
│   │   └── services/api.ts
│   └── package.json
├── docs/SYSTEM_DESIGN.md
└── sample_data/sales_sample.csv
```

## Run locally

Run the backend from its directory because its `.env` file and default `uploads/` and `data/` paths are relative to the process working directory.

### Backend (PowerShell)

```powershell
Set-Location backend
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set GROQ_API_KEY to enable AI insights and AI-written reports.
uvicorn app.main:app --reload
```

The API is at `http://localhost:8000`; `http://localhost:8000/health` works without an AI key. Interactive API documentation is at `http://localhost:8000/docs`.

### Frontend (in a second terminal)

```powershell
Set-Location frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open `http://localhost:5173`. In development, Vite proxies `/api` to `http://localhost:8000`. Set `VITE_BACKEND_URL` in `frontend/.env` when the backend runs at a different address.

## Typical workflow

1. Open **Upload Dataset** and upload a CSV or Excel workbook (`.xlsx`/`.xls`).
2. The upload response opens the dataset preview. The Analytics view has a server-searched and server-paginated preview, profiling, deterministic quality checks, and up to six suitable visualizations.
3. Open **History** to retrieve backend-stored datasets after a page reload or server restart. Selecting a record opens its analytics; deleting it removes both its metadata and its stored upload.
4. **Export PDF Report** on Analytics downloads a data-derived report with dataset overview, per-column statistics, quality findings, and selected vector charts.
5. AI Chat and the AI-written report use the configured Groq model. AI requests include bounded, Pandas-computed facts; the API returns those facts separately from the model narrative.

## HTTP API

All application routes are prefixed with `/api` except `/` and `/health`.

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/api/upload` | Validate and parse a CSV/XLSX upload, then persist the file and metadata |
| `GET` | `/api/datasets` | List persisted dataset metadata and indicate missing stored files |
| `DELETE` | `/api/datasets/{id}` | Delete a dataset's stored upload and SQLite metadata |
| `GET` | `/api/datasets/{id}/summary` | Return full-dataset analytics and one page of preview rows |
| `GET` | `/api/datasets/{id}/charts` | Return generated Plotly charts, detected columns, and suitability diagnostics |
| `POST` | `/api/datasets/{id}/insights` | Generate a Groq narrative and return separate verified Pandas facts |
| `GET` | `/api/datasets/{id}/report.pdf` | Download a generated PDF report |
| `GET` | `/health` | Basic backend health response |

The summary endpoint accepts `page` (1-based), `page_size` (1–100), `search`, `sort_by`, and `sort_desc`. Search is case-insensitive across all columns and is applied to the full DataFrame before sorting and pagination. The response includes total rows, matching rows, effective page, and page size.

Chart generation detects usable numeric, categorical, and date/time columns, avoids inferred identifiers as measurements, and skips unsuitable chart types with reasons. Automatic output is capped at six charts; high-volume chart data is sampled or bounded to keep responses and rendering manageable. Plotly figures support hover/zoom and PNG export when the browser's Plotly environment supports it.

## Configuration

Copy `backend/.env.example` to `backend/.env`. Do not commit `.env` or put real credentials in source control.

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `groq` | AI provider registry key; Groq is the implemented provider |
| `GROQ_API_KEY` | unset | Required only for AI insights and AI-written reports |
| `GROQ_MODEL` | `openai/gpt-oss-20b` | Groq model name; this project default is retained |
| `UPLOAD_DIR` | `uploads` | Directory for UUID-named uploaded source files |
| `DATA_DIR` | `data` | Directory containing `datasets.sqlite3` |
| `MAX_UPLOAD_MB` | `50` | Maximum accepted upload size |
| `CORS_ORIGINS` | localhost Vite origins | Comma-separated allowed browser origins |
| `VITE_BACKEND_URL` | empty | Optional frontend API base URL; Vite's development proxy defaults to port 8000 |

SQLite stores **metadata only** (dataset ID, original filename, upload timestamp, format, row/column counts, size, absolute storage path, and status). Uploaded file bytes remain in `UPLOAD_DIR`. Keep both the SQLite database and upload directory on persistent storage to retain datasets across restarts. Back them up together. This is a single-instance local setup, not a distributed storage service.

The Dashboard's recent-upload widget remains browser-local and is limited by its local-storage implementation. The History page is the backend-persisted list.

## Tests and checks

Backend tests use the virtual environment created above:

```powershell
Set-Location backend
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Frontend production build (includes the TypeScript project checks):

```powershell
Set-Location frontend
npm run build
```

ESLint is available with `npm run lint`.

## Known limitations

- No authentication, authorization, per-user ownership, upload rate limiting, or multi-tenant isolation is implemented. Do not expose this development service to untrusted networks.
- SQLite and local upload files are intended for a single application instance. Multiple instances need shared durable object storage and a coordinated database.
- AI narratives depend on Groq credentials, network availability, and model output. Use the separately returned verified facts as the exact calculated values.
- The current history records remain until explicitly deleted; no automatic retention or orphan-file cleanup policy is implemented.
- `/health` is a basic liveness response; it does not test SQLite, file storage, or Groq availability.

For the request/data flows, persistence boundary, error handling, and a clearly separated future scale-out design, see [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md).
