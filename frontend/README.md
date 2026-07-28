# DataPilot Frontend

Production frontend for the DataPilot AI data analyst. React 19 + TypeScript + Vite + Tailwind CSS.

## Quick start

```bash
npm install
npm run dev
```

Open http://localhost:5173. In dev, Vite proxies `/api/*` requests to your FastAPI backend (see `vite.config.ts`).

## Configuration

Copy `.env.example` to `.env` and set your backend URL:

```
VITE_BACKEND_URL=http://localhost:8000
```

## Backend contract

This frontend was built against the following confirmed FastAPI endpoints:

| Method | Endpoint | Used by |
| --- | --- | --- |
| POST | `/api/upload` | Upload page |
| GET | `/api/datasets/{id}/summary` | Dataset Preview, Analytics |
| GET | `/api/datasets/{id}/charts` | Charts page |
| POST | `/api/datasets/{id}/insights` | AI Chat, Reports |

### Not yet implemented server-side

A few pages call stub functions in `src/services/api.ts` marked `TODO` because the backend doesn't expose these yet:

- **Dataset listing** (`GET /api/datasets`) — Dashboard/History currently track recent uploads in `localStorage` instead.
- **Multi-turn chat** — the Chat page calls `/insights` per-message rather than a real conversation endpoint.
- **Report export/PDF** — the Reports page exports the AI-generated text as Markdown client-side instead.

Wire these up in `src/services/api.ts` once the corresponding routes exist — nothing else in the app needs to change.

## Project structure

```
src/
  components/   ui/ layout/ dashboard/ upload/ charts/ analytics/ chat/ common/
  pages/        one file per route
  hooks/        data-fetching + utility hooks (TanStack Query)
  services/     api.ts — the only place that calls fetch()
  context/      Theme + Settings providers
  types/        API contract types
  routes/       route table + path helpers
  lib/          cn(), query client
```

## Tech stack

React 19, TypeScript, Vite, Tailwind CSS, Radix UI primitives (hand-rolled shadcn/ui-style components), TanStack Query, React Router, React Hook Form + Zod, Plotly (react-plotly.js), Lucide icons.
