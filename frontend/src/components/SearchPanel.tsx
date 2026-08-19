import { useState } from "react";
import { SearchResponse, searchDocuments } from "@/lib/api";
import ResultsList from "@/components/ResultsList";

export default function SearchPanel({ enabled }: { enabled: boolean }) {
  const [topK, setTopK] = useState(5);
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch() {
    if (!query.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const res = await searchDocuments(query.trim(), topK);
      setResponse(res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h2>3. Semantic Search</h2>
      <p className="hint">Retrieval is based on meaning, not keywords.</p>

      <label>
        Query
        <input
          type="text"
          placeholder="e.g. What are the key ideas in chapter 2?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
      </label>

      <div className="row">
        <label>
          Top-K {topK}
          <input
            type="range"
            min={1}
            max={10}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
          />
        </label>
      </div>

      <button onClick={handleSearch} disabled={busy || !enabled || !query.trim()}>
        {busy ? "Searching..." : "Search"}
      </button>

      {error && <p className="error">{error}</p>}
      {!enabled && (
        <p className="hint">
          Upload and process documents first — Search automatically uses the
          model and vector DB chosen when processing.
        </p>
      )}

      <ResultsList response={response} />
    </section>
  );
}