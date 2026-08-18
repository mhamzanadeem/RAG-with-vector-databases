# Chunking Strategies and Trade-offs

Chunking splits documents into pieces that get embedded and stored in the vector
database. It is the **most impactful** RAG design decision: too-small chunks lose
context, too-large chunks dilute meaning.

This repo exposes **chunk size** and **chunk overlap** in the UI and in the
`/api/process` endpoint, so you can compare strategies empirically.

## Strategy 1 — Fixed-size / Recursive character splitting (default in this repo)

Split text into fixed-size pieces (default `500` chars) with a **configurable
overlap** (`100` chars) so boundaries don't cut sentences in half at awkward spots.

```python
RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,      # 500
    chunk_overlap=CHUNK_OVERLAP # 100
)
```

**Pros**
- Simple, deterministic, fast, and language-agnostic.
- Predictable vector size and index behavior.
- Overlap preserves context across chunk boundaries.

**Cons**
- Splits ignore *semantic* boundaries — a chunk may start/end mid-sentence or
  mid-topic.
- Fixed size does not adapt to the natural structure of the document.
- Can degrade retrieval quality for documents with long coherent sections.

**Trade-off to tune**: higher overlap recovers context but creates redundant
chunks (more storage, more similar vectors that can dominate search results).

## Strategy 2 — Semantic / structural chunking

Split on natural boundaries first (paragraphs, headers, sentences, code blocks),
then optionally merge small pieces until they reach a target size.

- **Paragraph/heading splitting**: use document structure (Markdown `#`, newlines,
  PDF sections). Great for reports and web docs where each section is self-contained.
- **Sentence-level with merging**: split on sentences and merge until a size target;
  guarantees each chunk starts and ends at a sentence boundary.

**Pros**
- Chunks match logical units, so retrieval hits are more coherent and relevant.
- Less overlap needed; less redundancy.

**Cons**
- More complex to implement and to tune (needs custom splitter logic).
- Sentence/paragraph boundaries are not reliable in all document types (e.g.,
  tables, code, scanned PDFs).
- Slightly slower at ingest time.

## Strategy 3 — Semantic (embedding-based) chunking

Use the embedding model itself to find topic change points: embed rolling windows
of text and break where the similarity between adjacent windows drops sharply.
(Example: LangChain's `SemanticChunker`.)

**Pros**
- Chunks align with meaning, giving the best retrieval quality per chunk.
- Auto-adapts to content, no magic size constants.

**Cons**
- **Expensive**: requires embedding the whole corpus before chunking (a second pass).
- Harder to reason about and tune (threshold sensitivity).
- Slowest of the three.

## Trade-off summary

| Strategy | Cost | Quality | Complexity | Best for |
|---|---|---|---|---|
| Fixed-size recursive | Low | Medium | Low | Quick POCs, generic text |
| Structural / sentence | Medium | High | Medium | Reports, Markdown, clean docs |
| Semantic (embedding-based) | High | Highest | High | High-value retrieval accuracy |

## Recommendation for this project

Start with **fixed-size recursive splitting** (the default), then measure retrieval
quality on your test queries. If results look fragmented or miss context, raise the
overlap or move to **sentence-level structural splitting** — both are achievable by
changing the `chunk_size`/`chunk_overlap` parameters here or swapping the splitter
in `backend/app/pipeline.py`.
