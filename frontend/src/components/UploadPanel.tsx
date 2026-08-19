import { useState } from "react";
import { DatasetStats, formatBytes, getStats, uploadFiles } from "@/lib/api";

export default function UploadPanel({
  onUploaded,
}: {
  onUploaded: (stats: DatasetStats) => void;
}) {
  const [files, setFiles] = useState<File[]>([]);
  const [stats, setStats] = useState<DatasetStats | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshStats() {
    try {
      const s = await getStats();
      setStats(s);
      onUploaded(s);
    } catch {
      setStats(null);
    }
  }

  async function handleUpload() {
    if (files.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      const res = await uploadFiles(files);
      setStats(res.stats);
      onUploaded(res.stats);
      setFiles([]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h2>1. Upload Documents</h2>
      <p className="hint">Upload .txt or .pdf files (10–15 recommended). Nothing is hard-coded.</p>

      <input
        type="file"
        accept=".txt,.pdf"
        multiple
        onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
      />
      <button onClick={handleUpload} disabled={busy || files.length === 0}>
        {busy ? "Uploading..." : "Upload files"}
      </button>

      {error && <p className="error">{error}</p>}

      <div className="stats">
        <span>Documents: <b>{stats?.document_count ?? 0}</b></span>
        <span>Total size: <b>{stats ? formatBytes(stats.total_size_bytes) : "0 B"}</b></span>
      </div>

      {stats && stats.files.length > 0 && (
        <ul className="file-list">
          {stats.files.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      )}

      <button className="link" onClick={refreshStats}>
        Refresh stats
      </button>
    </section>
  );
}