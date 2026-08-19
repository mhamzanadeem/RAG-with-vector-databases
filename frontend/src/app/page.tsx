"use client";

import { useEffect, useState } from "react";
import { API_URL, AppConfig, ProcessResponse, getConfig } from "@/lib/api";
import UploadPanel from "@/components/UploadPanel";
import ConfigPanel from "@/components/ConfigPanel";
import SearchPanel from "@/components/SearchPanel";

export default function Home() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [ready, setReady] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [dbReady, setDbReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        const cfg = await getConfig();
        if (cancelled) return;
        setConfig(cfg);
        if (cfg.active_config) setDbReady(true);
      } catch (e) {
        if (!cancelled) {
          setApiError(
            `Could not reach the backend at ${API_URL}: ${(e as Error).message}. Make sure the backend is running and NEXT_PUBLIC_API_URL points to it.`
          );
        }
      }
    }

    init();
    return () => {
      cancelled = true;
    };
  }, []);

  function handleProcessed(res: ProcessResponse) {
    if (res.chunks_indexed > 0) {
      setDbReady(true);
      // Lock Search to whatever model + DB just built the store.
      setConfig((prev) =>
        prev
          ? {
              ...prev,
              active_config: {
                model_name: res.embedding_model,
                db_type: res.vector_db,
              },
            }
          : prev
      );
    }
  }

  function handleUploaded() {
    // A new dataset was uploaded but not yet processed, so search stays disabled.
    setDbReady(false);
  }

  if (apiError) {
    return (
      <main className="page">
        <div className="card error-card">{apiError}</div>
      </main>
    );
  }

  if (!config) {
    return (
      <main className="page">
        <div className="card">Loading configuration…</div>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="hero">
        <h1>RAG Semantic Search</h1>
        <p>
          Retrieval-augmented search over your own documents. Choose an embedding
          model, a vector database, upload files, then ask semantic queries.
        </p>
      </header>

      <div className="layout">
        <UploadPanel onUploaded={handleUploaded} />
        <ConfigPanel config={config} onProcessed={handleProcessed} disabled={!config} />
        <SearchPanel enabled={dbReady} />
      </div>

      <footer className="footer">
        Frontend: {API_URL}
      </footer>
    </main>
  );
}