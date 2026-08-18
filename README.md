# RAG Pipeline with Vector Databases

A **retrieval-augmented generation (RAG)** system built from scratch in Python.
It embeds your own document set, stores the vectors in **FAISS** or **ChromaDB**,
and retrieves the most relevant chunks for any query based on *meaning* rather
than keywords.

Deployed as a **serverless frontend on Vercel** (Next.js) + a **FastAPI backend
on Render**.

---

## Features

- Upload your own `.txt` documents (nothing is hard-coded)
- Pick a Hugging Face **embedding model** (`all-MiniLM-L6-v2`, `bge-small-en-v1.5`)
- Pick a **vector database** (FAISS or Chroma) — live-switchable
- Configurable **chunk size / overlap** and **top-k** retrieval
- Ordered, relevance-scored semantic results with source file and % match
- REST API backend + web UI

## Deliverables

| Requirement | Where |
|---|---|
| Working RAG pipeline (from scratch) | `backend/app/pipeline.py`, `backend/embeddings/`, `backend/Vector_Store/` |
| ChromaDB vs FAISS explained | [docs/vector-db-comparison.md](docs/vector-db-comparison.md) |
| ≥ 2 chunking strategies + trade-offs | [docs/chunking-strategies.md](docs/chunking-strategies.md) |
| Scalable RAG architecture (labeled) | [docs/architecture.md](docs/architecture.md) |
| Evaluation report | `experiments/report/report_template.md` |

---

## Architecture

```
Frontend (Vercel)                    Backend (Render)
┌───────────────────┐   HTTPS/JSON  ┌──────────────────────────────┐
│  Next.js UI       │◄─────────────►│  FastAPI  ·  /api/* endpoints│
│  upload · config  │               │  chunking · embedding ·      │
│  search · results │               │  retrieval (FAISS/Chroma)    │
└───────────────────┘               └──────────────────────────────┘
```

Full labeled diagram and scale-up path: [docs/architecture.md](docs/architecture.md)

## Project structure

```
.
├── backend/                  # FastAPI service (deployed on Render)
│   ├── app/
│   │   ├── main.py           #   FastAPI routes (/api/config, /api/upload, /api/process, /api/search)
│   │   ├── pipeline.py       #   RAG pipeline: load → chunk → embed → store → search
│   │   └── config.py         #   models, DB options, paths, chunking defaults
│   ├── embeddings/           # Hugging Face embedding wrapper
│   ├── Vector_Store/         # FAISS + Chroma create/load
│   ├── gui.py                # Optional local Streamlit GUI
│   ├── data/                 # uploaded documents (runtime, gitignored)
│   ├── stores/               # persisted indexes (runtime, gitignored)
│   ├── model_cache/          # downloaded HF models (runtime, gitignored)
│   └── requirements.txt
├── frontend/                 # Next.js app (deployed on Vercel)
│   ├── src/
│   │   ├── app/              #   page, layout, styles
│   │   ├── components/       #   Upload / Config / Search panels
│   │   └── lib/api.ts        #   typed API client
│   └── .env.example
├── docs/                     # assignment deliverables
├── experiments/report/       # evaluation template
└── render.yaml               # Render Blueprint for the backend
```

---

## Local development

### Backend (Python 3.10+)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload          # runs on http://localhost:8000
```

Check it: http://localhost:8000/docs (Swagger UI) or `GET /health`.

Optional local GUI:

```bash
streamlit run backend/gui.py
```

### Frontend (Node 18+)

```bash
cd frontend
cp .env.example .env.local              # point NEXT_PUBLIC_API_URL at the backend
npm install
npm run dev                             # runs on http://localhost:3000
```

---

## Deployment

### 1. Backend on Render

**Option A — Blueprint (recommended):** import the repo in Render and use the
included `render.yaml`.

**Option B — manual:**

1. New → **Web Service** → connect your GitHub repo.
2. Root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Instance type: use a paid instance (**≥ 2 GB RAM**) — local Hugging Face
   models don't fit on the free tier.

> Your service URL will look like `https://rag-backend.onrender.com`.

> **Note:** the vector store lives on the instance disk and is rebuilt when you
> upload + process data. For a persistent dataset across redeploys, use a managed
> vector database (see [docs/architecture.md](docs/architecture.md)).

### 2. Frontend on Vercel

1. Import the `frontend/` directory (or repo root if you set the root directory) on
   [vercel.com](https://vercel.com).
2. Framework preset: **Next.js** (auto-detected).
3. Add an environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://rag-backend.onrender.com`
4. Deploy. CORS is already enabled on the backend.

### 3. Verify

1. Open the Vercel app.
2. Upload `.txt` documents → **Upload files**.
3. Choose model + vector DB → **Process documents**.
4. Ask a query → **Search** and review ranked, relevance-scored results.

---

## API reference

| Method | Endpoint | Body | Returns |
|---|---|---|---|
| GET | `/health` | — | `{status}` |
| GET | `/api/config` | — | available models, DBs, chunk defaults |
| GET | `/api/stats` | — | doc count, file list, total size |
| POST | `/api/upload` | multipart `files` | saved count + stats |
| POST | `/api/process` | `{model_name, db_type, chunk_size, chunk_overlap}` | chunks indexed |
| POST | `/api/search` | `{query, model_name, db_type, top_k}` | ordered results + relevance |

---

## Academic integrity & submission

This is the **CS-4015 Homework 1 – Phase 1** deliverable
(see `HW1_Phase1_AgenticAI.pdf`). Individual assignment — commit regularly before
the deadline.
