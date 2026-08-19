export interface ActiveConfig {
  model_name: string;
  db_type: string;
}

export interface AppConfig {
  embedding_models: string[];
  vector_databases: string[];
  default_chunk_size: number;
  default_chunk_overlap: number;
  active_config: ActiveConfig | null;
}

export interface DatasetStats {
  document_count: number;
  files: string[];
  total_size_bytes: number;
}

export interface SearchResult {
  content: string;
  source: string;
  score: number;
  relevance: number;
}

export interface SearchResponse {
  query: string;
  top_k: number;
  model_name: string;
  db_type: string;
  results: SearchResult[];
}

export interface ProcessResponse {
  status: string;
  vector_db: string;
  embedding_model: string;
  chunks_indexed: number;
}

const API_URL: string =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export { API_URL };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, init);
  } catch (e) {
    throw new Error(
      `Could not reach backend at ${API_URL}. Start it (python -m uvicorn app.main:app --reload) and check NEXT_PUBLIC_API_URL.`
    );
  }
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status} (${API_URL}${path}): ${detail}`);
  }
  return res.json() as Promise<T>;
}

export function getConfig(): Promise<AppConfig> {
  return request<AppConfig>("/api/config");
}

export function getStats(): Promise<DatasetStats> {
  return request<DatasetStats>("/api/stats");
}

export function uploadFiles(files: File[]): Promise<{ saved: number; stats: DatasetStats }> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  return request("/api/upload", {
    method: "POST",
    body: formData,
  });
}

export function processDocuments(
  modelName: string,
  dbType: string,
  chunkSize: number,
  chunkOverlap: number
): Promise<ProcessResponse> {
  return request("/api/process", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model_name: modelName,
      db_type: dbType,
      chunk_size: chunkSize,
      chunk_overlap: chunkOverlap,
    }),
  });
}

export function searchDocuments(query: string, topK: number): Promise<SearchResponse> {
  return request("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      top_k: topK,
    }),
  });
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}