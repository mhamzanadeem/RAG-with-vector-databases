# ChromaDB vs FAISS

Both are vector stores used by this project (selectable in the UI and the
`/api/process` endpoint). They serve the same job — **find the most similar
embedding vectors to a query vector** — but are very different tools.

| Aspect | FAISS | ChromaDB |
|---|---|---|
| **What it is** | A low-level **library** for fast nearest-neighbour search (from Meta/Facebook AI Research) | A full-featured **vector database** (server/embedded) with an API |
| **Search algorithm** | HNSW / IVF-PQ / exact flat indexes; you choose the index type | HNSW-backed ANN index managed internally |
| **Persistence** | You save/load an index file yourself (`.index` + metadata JSON) | Built-in persistent storage + a client API to query it |
| **Metadata / filtering** | Manual — you keep a mapping of index → document separately | First-class — store documents + metadata alongside vectors and filter on it |
| **CRUD (add/update/delete)** | Rebuild or track deletions yourself | Supported via the DB API |
| **Language of choice** | C++ with Python bindings | Python (with client/server modes in other languages) |
| **Concurrency / multi-user** | Not a server — single process owns the index | Client–server mode supports concurrent clients |
| **Use case fit** | High-performance, self-managed similarity search in research / high throughput | When you want a managed store with persistence, filtering, and a query API out of the box |
| **In this repo** | `Vector_Store/vector_store_manager.py` saves/loads a local FAISS index | The same module persists a Chroma collection |

## Key differences in one sentence each

- **FAISS gives you raw speed and control** (it is an in-memory index library), but
  *you* are responsible for persistence, metadata, and bookkeeping.
- **ChromaDB gives you an operational database** (persistence, metadata, filtering,
  client access) at the cost of some performance and control.

## Which one does the score mean?

The similarity metric also differs, which is why the API normalizes both:

- **ChromaDB** returns **cosine similarity**, higher is better (`0.06` in the test).
- **FAISS** (default) returns **L2 distance**, lower is better (`1.33` in the test).

The backend converts FAISS L2 distance to relevance with `1 / (1 + distance)`, so the
frontend can display one consistent 0–100% relevance bar for both backends
(see `backend/app/pipeline.py` → `search_documents_with_scores`).

## When to use which in production

- Small-to-medium datasets where you want zero infra: **FAISS** on disk, or
  **ChromaDB** embedded.
- Multi-user apps, shared datasets, and remote teams: **ChromaDB client/server**
  (or a hosted vector DB).
- Millions of vectors, latency-critical: **FAISS** with an optimized index
  (IVF/HNSW/quantization), or a managed ANN service.
