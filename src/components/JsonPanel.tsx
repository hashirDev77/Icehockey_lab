import type { ProviderResult } from "../lib/client";

export function JsonPanel({ label, result }: { label?: string; result: ProviderResult | null }) {
  if (!result) return <div className="state">Loading match data...</div>;
  return (
    <div className="panel">
      {label ? <h2>{label}</h2> : null}
      <p className="meta">
        <code>{result.endpoint}</code> · HTTP {result.status}
        {result.error ? ` · ${result.error}` : ""}
      </p>
      {result.body == null ? (
        <p className="empty">This information is not available.</p>
      ) : (
        <pre className="meta">{JSON.stringify(result.body, null, 2)}</pre>
      )}
    </div>
  );
}
