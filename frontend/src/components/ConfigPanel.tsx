import { useState } from "react";
import { AppConfig, ProcessResponse, processDocuments } from "@/lib/api";

export default function ConfigPanel({
  config,
  onProcessed,
  disabled,
}: {
  config: AppConfig;
  onProcessed: (res: ProcessResponse) => void;
  disabled: boolean;
}) {
  const [model, setModel] = useState(config.embedding_models[0]);
  const [dbType, setDbType] = useState(config.vector_databases[0]);
  const [chunkSize, setChunkSize] = useState(config.default_chunk_size);
  const [chunkOverlap, setChunkOverlap] = useState(config.default_chunk_overlap);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ProcessResponse | null>(null);

  async function handleProcess() {
    setBusy(true);
    setError(null);
    try {
      const res = await processDocuments(model, dbType, chunkSize, chunkOverlap);
      setResult(res);
      onProcessed(res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h2>2. Embedding & Vector Store</h2>
      <p className="hint">
        Pick a Hugging Face embedding model and a vector database (FAISS or Chroma).
      </p>

      <label>
        Embedding model
        <select value={model} onChange={(e) => setModel(e.target.value)}>
          {config.embedding_models.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </label>

      <label>
        Vector database
        <select value={dbType} onChange={(e) => setDbType(e.target.value)}>
          {config.vector_databases.map((db) => (
            <option key={db} value={db}>
              {db}
            </option>
          ))}
        </select>
      </label>

      <div className="row">
        <label>
          Chunk size
          <input
            type="number"
            min={50}
            step={50}
            value={chunkSize}
            onChange={(e) => setChunkSize(Number(e.target.value))}
          />
        </label>
        <label>
          Chunk overlap
          <input
            type="number"
            min={0}
            value={chunkOverlap}
            onChange={(e) => setChunkOverlap(Number(e.target.value))}
          />
        </label>
      </div>

      <button onClick={handleProcess} disabled={busy || disabled}>
        {busy ? "Processing..." : "Process documents"}
      </button>

      {error && <p className="error">{error}</p>}
      {result && (
        <p className="success">
          Indexed {result.chunks_indexed} chunks into {result.vector_db} using{" "}
          {result.embedding_model}.
        </p>
      )}
    </section>
  );
}