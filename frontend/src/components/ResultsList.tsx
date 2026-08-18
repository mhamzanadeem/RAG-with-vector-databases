import { SearchResponse } from "@/lib/api";

export default function ResultsList({
  response,
}: {
  response: SearchResponse | null;
}) {
  if (!response) return null;

  if (response.results.length === 0) {
    return <p className="hint">No relevant documents found.</p>;
  }

  return (
    <div className="results">
      <p className="success">
        Found {response.results.length} relevant chunk(s) for:{" "}
        <em>{response.query}</em>
      </p>

      {response.results.map((r, i) => {
        const pct = Math.round(r.relevance * 100);
        return (
          <article className="result" key={i}>
            <header>
              <span className="rank">#{i + 1}</span>
              <span className="source">{r.source || "unknown source"}</span>
              <span className="bar">
                <span style={{ width: `${pct}%` }} />
              </span>
              <span className="pct">{pct}%</span>
            </header>
            <p>{r.content}</p>
          </article>
        );
      })}
    </div>
  );
}