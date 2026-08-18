# Scalable RAG Architecture

A production RAG system separates the **frontend**, the **API/application layer**,
the **embedding service**, the **vector store**, and (optionally) a **generator
LLM**. Each component scales independently.

## Current deployment (this repo)

```
┌─────────────────────┐          ┌──────────────────────────────┐
│   FRONTEND (Vercel) │          │      BACKEND (Render)        │
│                     │  HTTPS   │  ┌────────────────────────┐  │
│  Next.js SPA        │◄────────►│  │  FastAPI application   │  │
│  · upload docs      │  JSON    │  │  · upload /process/    │  │
│  · pick model + db  │          │  │    search endpoints    │  │
│  · top-k slider     │          │  │  ┌──────────────────┐  │  │
│  · view results     │          │  │  │ Chunking +       │  │  │
└─────────────────────┘          │  │  │ Embedding (HF)   │  │  │
                                 │  │  └──────────────────┘  │  │
                                 │  └───────────┬────────────┘  │
                                 │              │ local disk    │
                                 │  ┌───────────▼────────────┐  │
                                 │  │ Vector Store           │  │
                                 │  │ FAISS index / ChromaDB │  │
                                 │  └────────────────────────┘  │
                                 └──────────────────────────────┘
```

### Components labeled

1. **Frontend (Vercel)** — stateless UI (Next.js). Owns no data. Only talks to the
   backend over HTTPS/JSON (`frontend/src/lib/api.ts`).
2. **API / application layer (Render)** — FastAPI. Validates requests, orchestrates
   the pipeline, returns JSON. `backend/app/main.py`.
3. **Ingestion pipeline** — loads documents, chunks them, embeds chunks.
   `backend/app/pipeline.py` + `backend/embeddings/`.
4. **Vector store** — FAISS or ChromaDB. Holds chunk embeddings + metadata.
   `backend/Vector_Store/`.
5. **Retrieval** — nearest-neighbour search over the query embedding, returns the
   top-k most relevant chunks with a relevance score.

## Scale-up path (production)

```
┌────────────┐      ┌──────────────┐      ┌──────────────────────┐
│ CDN + UI   │      │  API Gateway │      │   Ingestion workers  │
│ (Vercel)   │─────►│  + LB        │─────►│  (queue consumers)   │
└────────────┘      └──────────────┘      └──────────┬───────────┘
        │                    │                       │
        │                    │              ┌────────▼───────────┐
        │                    │              │ Object storage     │
        │                    │              │ (S3 / R2 docs)     │
        │                    │              └────────┬───────────┘
        │                    │                       │
        │                    ▼                       ▼
        │            ┌─────────────────┐    ┌──────────────────┐
        │            │ Embedding API   │    │ Metadata / jobs  │
        │            │ (HF / OpenAI)   │    │ (Postgres/Redis) │
        │            └────────┬────────┘    └──────────────────┘
        │                     │
        │            ┌────────▼─────────┐
        │            │ Managed Vector DB│
        │            │ (Pinecone,       │
        │            │  Qdrant,         │
        │            │  Supabase pgvec) │
        │            └────────┬─────────┘
        │                     │ top-k
        │            ┌────────▼─────────┐
        │            │ Generator LLM   │  (optional, for RAG QA)
        │            │ (GPT / hosted)  │
        │            └──────────────────┘
        └───── return ranked chunks / grounded answer ─────────┘
```

### Why each piece scales independently

- **Frontend**: static/CDN-cached, scales automatically on Vercel, no server code.
- **API tier**: stateless FastAPI behind a load balancer — add replicas as traffic grows.
- **Ingestion workers**: long-running embed jobs moved off the request path into a queue;
  scale them separately from query traffic.
- **Embedding service**: an API-based embedding provider avoids running GPU models on
  your web servers (this is the main reason Render free/Starter instances can't run
  this repo's local models comfortably).
- **Vector store**: managed vector DB provides persistence, concurrency, and ANN
  search at scale — and survives redeploys (the local-disk FAISS/Chroma in this repo
  is rebuilt when you upload data, which is fine for the homework but not for prod).
- **Generator LLM**: hosted model API — no GPU infrastructure to maintain.

### Notes / limitations of the current repo

- The vector store lives on the **Render instance's disk**, so it is rebuilt on each
  deploy. For a persistent production dataset, point `vector_store_manager.py` at a
  managed vector database instead.
- Local Hugging Face embeddings load the model into memory per request; on Render,
  use a paid instance (≥ 2 GB RAM) or swap to an embedding API.
