import { useState } from "react";
import { AppConfig, SearchResponse, searchDocuments } from "@/lib/api";
import ResultsList from "@/components/ResultsList";

export default function SearchPanel({
  config,
  enabled,
}: {
  config: AppConfig;
  enabled: boolean;
}) {
  const [model, setModel] = useState(config.embedding_models[0]);
  const [dbType, setDbType] = useState(config.vector_databases[0]);
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
      const res = await searchDocuments(query.trim(), model, dbType, topK);
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
          Model
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            {config.embedding_models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>
        <label>
          Vector DB
          <select value={dbType} onChange={(e) => setDbType(e.target.value)}>
            {config.vector_databases.map((db) => (
              <option key={db} value={db}>
                {db}
              </option>
            ))}
          </select>
        </label>
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
      {!enabled && <p className="hint">Upload and process documents before searching.</p>}

      <ResultsList response={response} />
    </section>
  );
}