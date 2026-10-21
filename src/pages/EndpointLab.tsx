import { useState } from "react";
import { CATALOG, SAMPLE } from "../catalog";
import { iceHockeyGet, type ProviderResult } from "../lib/client";
import { JsonPanel } from "../components/JsonPanel";

const defaults: Record<string, string> = {
  eventId: String(SAMPLE.eventId),
  teamId: String(SAMPLE.teamId),
  playerId: String(SAMPLE.playerIdForEventStats),
  tournamentId: String(SAMPLE.tournamentId),
  managerId: String(SAMPLE.managerId),
  seasonId: String(SAMPLE.seasonId),
  type: SAMPLE.enrichmentType,
  direction: SAMPLE.direction,
  date: new Date().toISOString().slice(0, 10),
  round: SAMPLE.round,
};

function fill(path: string, ids: Record<string, string>) {
  return path.replace(/\{([^}]+)\}/g, (_, key) => ids[key] || `{${key}}`);
}

export function EndpointLabPage() {
  const [ids, setIds] = useState(defaults);
  const [selected, setSelected] = useState<(typeof CATALOG)[number]>(CATALOG[12]);
  const [result, setResult] = useState<ProviderResult | null>(null);
  const [q, setQ] = useState("Maple Leafs");
  const [error, setError] = useState<string | null>(null);

  async function run(path: (typeof CATALOG)[number]) {
    setSelected(path);
    setError(null);
    const filled = fill(path, ids).replace(/^\/v1\/ice_hockey\//, "");
    const params: Record<string, string | number | undefined> = {};
    if (path.endsWith("/search")) params.q = q;
    if ((path.endsWith("/events") || path.endsWith("/players") || path.endsWith("/teams") || path.endsWith("/tournaments") || path.includes("/events/")) && !path.includes("{direction}")) {
      params.limit = 5;
    }
    if (path.includes("/events/{direction}")) params.limit = 5;
    try {
      setResult(await iceHockeyGet(filled, params));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setResult(null);
    }
  }

  return (
    <>
      <h1>40 deployed routes</h1>
      <p className="meta">Each button calls SportsAPI365 `GET /v1/ice_hockey/...` with the IDs below (from the catalog sweep).</p>
      <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
        {Object.entries(ids).map(([key, value]) => (
          <label className="meta" key={key}>
            {key}{" "}
            <input className="field" value={value} onChange={(e) => setIds({ ...ids, [key]: e.target.value })} />
          </label>
        ))}
        <label className="meta">
          search q <input className="field" value={q} onChange={(e) => setQ(e.target.value)} />
        </label>
      </div>
      <div className="cards" style={{ marginTop: 16 }}>
        {CATALOG.map((path) => (
          <button
            key={path}
            className={selected === path ? "card" : "card"}
            onClick={() => run(path)}
            style={{ textAlign: "left", borderColor: selected === path ? "var(--gold)" : undefined }}
          >
            <code>{path}</code>
          </button>
        ))}
      </div>
      {error ? <p className="state error">This information could not be loaded. {error}</p> : null}
      {result && <JsonPanel label={selected} result={result} />}
    </>
  );
}
