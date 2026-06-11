# MedoraRx Frontend

React + TypeScript + Tailwind UI for the MedoraRx translation pipeline.

## Prerequisites

- Node.js 18+
- The backend running at `http://127.0.0.1:8000` (`uvicorn backend.main:app --reload`)

## Setup

```bash
cd frontend
npm install
npm run dev
```

Open the printed URL (default http://localhost:5173).

## What it does

1. Upload a clinical PDF (drag & drop or browse).
2. Click **Translate & Review** — the app POSTs the file to `/translate`.
3. The pipeline runs (parse → translate → review → report) and the result
   renders in a 3-panel viewer:
   - **Panel 1** — original English, section by section
   - **Panel 2** — Hindi translation (larger Devanagari font)
   - **Panel 3** — Foundry IQ review: confidence score, term counts, and a
     reasoning trace of every flagged / ambiguous term

## Build

```bash
npm run build
npm run preview
```

## Configuration

The backend URL is set in `src/api.ts` (`API_BASE`). The Vite dev server also
proxies `/api/*` to the backend if you prefer same-origin requests.
