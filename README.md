# 🧠 RAG Pipeline with Vector Databases

> A **retrieval-augmented generation (RAG)** system built **from scratch in Python**.
> It embeds your own document set, stores the vectors in **FAISS** or **ChromaDB**,
> and retrieves the most relevant chunks for any query based on **meaning**, not keywords.

<span style="color:#5b8cff">⚡ Frontend on **Vercel** (Next.js)</span>  ·  <span style="color:#5b8cff">🖥️ Backend on **Render** (FastAPI)</span>

---

## 🗄️ 1. The Vector Stores: ChromaDB vs FAISS

Both do the same core job — **find the vectors most similar to a query vector** —
but they are very different tools under the hood.

| | **FAISS** | **ChromaDB** |
|---|---|---|
| **What is it?** | A low-level **library** for ultra-fast nearest-neighbour search (Meta / FAIR) | A full-featured **vector database**, embedded or client/server |
| **Search index** | You choose (Flat / HNSW / IVF + PQ) | HNSW-based ANN index, managed for you |
| **Persistence** | You save & load index files + metadata yourself | Built-in persistent storage + query API |
| **Metadata & filters** | Manual bookkeeping | First-class — store & filter by metadata |
| **CRUD (add/update/delete)** | You rebuild or track deletions | Supported via the database API |
| **Concurrency** | Single-process, in-memory | Client–server mode handles multiple clients |
| **Best for** | Raw speed, control, millions of vectors | Out-of-the-box operational DB |

### 📐 Why the scores look different

- **ChromaDB** returns *cosine similarity* → **higher is better** (e.g. `0.06`)
- **FAISS** (default) returns *L2 distance* → **lower is better** (e.g. `1.33`)

The backend normalizes both to a 0–100% "relevance" bar so the UI is consistent:
`relevance = score` (Chroma) vs `relevance = 1 / (1 + distance)` (FAISS).

> **TL;DR** — FAISS = speed & control (you babysit it). Chroma = an operational DB
> (persistence, filters, clients) with a small perf cost. This repo lets you switch
> live from the UI to compare them directly.

---

## ✂️ 2. Chunking Strategies & Their Trade-offs

Chunking splits documents before embedding — **the single most impactful RAG
design decision** (too small → lost context, too large → diluted meaning). This
project exposes **chunk size** and **overlap** in the UI so you can test them live.

### Strategy A — Fixed-size / Recursive (default here)
```python
RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
```
- 🟢 Simple, deterministic, fast, language-agnostic; overlap preserves context
- 🔴 Ignores semantic boundaries; fixed size ignores document structure

### Strategy B — Structural / sentence-aware
Split on paragraph/Markdown headers or sentences, then merge up to a target size.
- 🟢 Chunks match logical units → more coherent retrieval hits
- 🔴 More code to tune; unreliable on tables/code/scanned PDFs

### Strategy C — Semantic (embedding-based)
Use the embedding model itself to detect topic-change points and break there.
- 🟢 Best retrieval quality per chunk; self-adapts to content
- 🔴 Expensive (embeds the whole corpus twice); threshold tuning; slowest

| Strategy | Cost 💸 | Quality 🎯 | Complexity 🧩 | Best for |
|---|:-:|:-:|:-:|---|
| Fixed-size recursive | Low | Medium | Low | Quick POCs, generic text |
| Structural / sentence | Medium | High | Medium | Reports, Markdown, clean docs |
| Semantic (embedding) | High | Highest | High | High-value retrieval accuracy |

> **Recommendation:** start with fixed-size recursive (the default), measure
> retrieval quality on your own queries, then raise overlap or switch to
> sentence-level splitting.

---

## 🏗️ 3. Scalable RAG Architecture (labeled)

### Components as deployed
```
┌─────────────────────┐          ┌────────────────────────────────────┐
│  FRONTEND (Vercel)  │  HTTPS   │  BACKEND (Render)                  │
│  · Next.js UI       │  JSON    │  ┌──────────────────────────────┐  │
│  ┌───────────────┐  │◄────────►│  │  FastAPI application layer   │  │
│  │  Upload docs  │  │          │  │  /upload /process /search    │  │
│  │  Pick model+DB│  │          │  │  ┌────────────────────────┐  │  │
│  │  Top-K slider │  │          │  │  │ Ingestion (chunk+embed) │  │  │
│  │  Results view │  │          │  │  └────────────────────────┘  │  │
│  └───────────────┘  │          │  └─────────────┬──────────────┘  │
└─────────────────────┘          │  ┌─────────────▼──────────────┐  │
                                 │  │ Vector store (FAISS/Chroma) │  │
                                 │  └──────────────────────────────┘  │
                                 └────────────────────────────────────┘
```

### Scale-up path (production)
```
┌───────────┐    ┌──────────────┐    ┌─────────────────────┐
│ CDN + UI  │    │ API Gateway  │    │ Ingestion workers   │
│ (Vercel)  │───►│ + Load       │───►│ (queue consumers)   │
└───────────┘    │ Balancer     │    └──────────┬──────────┘
                 └──────────────┘               │
                       │               ┌────────▼─────────┐
                       │               │ Object storage   │
                       │               │ (S3 / R2 docs)   │
                       │               └────────┬─────────┘
                       │                        │
                       │      ┌────────────────┐ ▼ ┌───────────────┐
                       │      │ Embedding API  │   │ Metadata/Jobs │
                       │      │ (HF / OpenAI)  │   │ (Postgres/    │
                       │      └────────┬───────┘   │  Redis)       │
                       │               │           └───────────────┘
                       │      ┌────────▼──────────┐
                       │      │ Managed Vector DB │   Pinecone · Qdrant
                       │      │  (ann search)     │   pgvector · Supabase
                       │      └────────┬──────────┘
                       │               │ top-k chunks
                       │      ┌────────▼──────────┐
                       │      │ Generator LLM     │  (optional GPT/hosted)
                       │      └────────────────────┘
                       └────→ ranked chunks / grounded answer
```

**Why each piece scales independently**
- **Frontend** → static/CDN-cached, auto-scales on Vercel, zero server code
- **API tier** → stateless FastAPI behind a load balancer; add replicas as traffic grows
- **Ingestion workers** → heavy embedding jobs off the request path, scaled separately
- **Embedding service** → API-based models avoid running GPUs on your web servers
- **Vector store** → managed DB gives persistence + concurrency across redeploys
- **Generator LLM** → hosted model API, no GPU infrastructure to maintain

> ⚠️ **Production note:** in this repo the vector store lives on Render's disk and is
> rebuilt when you re-process data — perfect for the homework. For a persistent
> production dataset, point `backend/Vector_Store/` at a managed vector database.

---

## ✨ Features

- 📤 Upload your own `.txt` / `.pdf` documents — nothing is hard-coded
- 🤖 Pick a Hugging Face embedding model (`all-MiniLM-L6-v2`, `bge-small-en-v1.5`)
- 🗄️ Pick FAISS or Chroma — live-switchable
- 🔢 Configurable chunk size / overlap and top-K retrieval
- 🎯 Ordered, relevance-scored results with source file + % match
- 🔒 Search automatically locked to the model + DB used at index time
- 🧩 REST API backend + web UI + optional local Streamlit GUI

---

## 📁 Project structure

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
│   ├── data/                 # uploaded docs (txt/pdf, runtime, gitignored)
│   ├── stores/               # persisted indexes + active config (runtime, gitignored)
│   ├── model_cache/          # downloaded HF models (runtime, gitignored)
│   └── requirements.txt
├── frontend/                 # Next.js app (deployed on Vercel)
│   ├── src/
│   │   ├── app/              #   page, layout, styles
│   │   ├── components/       #   Upload / Config / Search panels
│   │   └── lib/api.ts        #   typed API client
│   └── .env.example
├── experiments/report/       # retrieval evaluation template
└── render.yaml               # Render Blueprint for the backend
```

---

## 🚀 Local development

> **Prerequisites:** Python 3.10+, Node.js 18+ and npm — two terminals run side by side.

### Backend (API on http://localhost:8000)
```bash
cd backend
pip install -r requirements.txt        # first time only
python -m uvicorn app.main:app --reload
```
Check it: http://localhost:8000/docs (Swagger UI) or `GET /health`.
Optional local GUI: `python -m streamlit run backend/gui.py`

### Frontend (UI on http://localhost:3000)
```bash
cd frontend
copy .env.example .env.local            # Windows   (or `cp` on macOS/Linux)
# set NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.local
npm install                             # first time only
npm run dev
```

### Test it end-to-end
1. Open http://localhost:3000
2. Upload `.txt` or `.pdf` documents → **Upload files** 📤
3. Pick embedding model + vector DB → **Process documents** ⚙️
4. Type a query → **Search** 🔍

### Useful CLI commands
```bash
# run API                     python -m uvicorn app.main:app --reload
# health check                curl http://localhost:8000/health
# available models/DBs        curl http://localhost:8000/api/config
# upload docs                 curl -X POST http://localhost:8000/api/upload -F "files=@doc.pdf"
# build the store             curl -X POST http://localhost:8000/api/process \
#                               -H "Content-Type: application/json" \
#                               -d '{"model_name":"sentence-transformers/all-MiniLM-L6-v2","db_type":"FAISS"}'
# search (uses locked config) curl -X POST http://localhost:8000/api/search \
#                               -H "Content-Type: application/json" \
#                               -d '{"query":"what is RAG?","top_k":3}'

# frontend                    npm run dev | npm run build | npm start
```

---

## ☁️ Deployment

### 1. Backend on Render
**Option A — Blueprint (recommended):** import the repo in Render with `render.yaml`.
**Option B — manual:** Web Service → root dir `backend` → build `pip install -r
requirements.txt` → start `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
> ⚠️ Use a paid instance (**≥ 2 GB RAM**) — local Hugging Face models don't fit free tier.

### 2. Frontend on Vercel
1. Import the repo on [vercel.com](https://vercel.com) → framework **Next.js** (auto-detected)
2. Add env var: `NEXT_PUBLIC_API_URL` = `https://your-backend.onrender.com`
3. Deploy — CORS is already enabled on the backend.

---

## 📡 API reference

| Method | Endpoint | Body | Returns |
|---|---|---|---|
| GET | `/health` | — | `{status}` |
| GET | `/api/config` | — | models, DBs, chunk defaults, active config |
| GET | `/api/stats` | — | doc count, file list, total size |
| POST | `/api/upload` | multipart `files` | saved count + stats |
| POST | `/api/process` | `{model_name, db_type, chunk_size, chunk_overlap}` | chunks indexed |
| POST | `/api/search` | `{query, top_k}` | ordered results + relevance (uses stored config) |

---

## 🎓 Academic integrity & submission

**CS-4015 Homework 1 – Phase 1** deliverable (see `HW1_Phase1_AgenticAI.pdf`).
Individual assignment — commit regularly before the deadline.