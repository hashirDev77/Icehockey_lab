import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  getTournament,
  getTournamentMatches,
  getTournamentRound,
  getTournamentSeasons,
  getTournamentStandings,
  getTournaments,
  type Match,
} from "../api";
import { DataState } from "../components/DataState";
import { MatchCard } from "../components/MatchCard";

export function TournamentPage() {
  const { id } = useParams();
  const [params, setParams] = useSearchParams();
  const tab = params.get("tab") || "overview";
  const standingType = (params.get("type") || "total") as "total" | "home" | "away";
  const [overview, setOverview] = useState<Record<string, unknown> | null>(null);
  const [seasonId, setSeasonId] = useState<string>("");
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [round, setRound] = useState("1");
  const [panel, setPanel] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const tournamentId = Number(id);

  useEffect(() => {
    if (!tournamentId) return;
    getTournament(tournamentId)
      .then((data) => {
        setOverview(data as unknown as Record<string, unknown>);
        setSeasonId(String(data.currentSeasonId || ""));
      })
      .catch((err: Error) => setError(err.message));
  }, [tournamentId]);

  useEffect(() => {
    if (!tournamentId || tab === "overview") return;
    if (tab === "matches") getTournamentMatches(tournamentId).then(setPanel).catch((err: Error) => setError(err.message));
    if (tab === "calendar") getTournamentMatches(tournamentId, date).then(setPanel).catch((err: Error) => setError(err.message));
    if (tab === "seasons") getTournamentSeasons(tournamentId).then(setPanel).catch((err: Error) => setError(err.message));
    if (tab === "standings" && seasonId) {
      getTournamentStandings(tournamentId, Number(seasonId), standingType).then(setPanel).catch((err: Error) => setError(err.message));
    }
    if (tab === "rounds" && seasonId) {
      getTournamentRound(tournamentId, Number(seasonId), round).then(setPanel).catch((err: Error) => setError(err.message));
    }
  }, [tournamentId, tab, seasonId, date, round, standingType]);

  const tournament = overview?.tournament as { name?: string; country?: string } | undefined;
  const seasons = (overview?.seasons || []) as Array<{ id: number; name: string }>;

  return (
    <DataState loading={!overview && !error} error={error}>
      <h1>{tournament?.name || "Competition"}</h1>
      <p className="meta">{tournament?.country}</p>
      <label className="meta">
        Season{" "}
        <select value={seasonId} onChange={(e) => setSeasonId(e.target.value)}>
          {seasons.map((season) => (
            <option key={season.id} value={season.id}>
              {season.name}
            </option>
          ))}
        </select>
      </label>
      <div className="tabs">
        {["overview", "matches", "calendar", "standings", "rounds", "seasons"].map((item) => (
          <button key={item} className={tab === item ? "active" : ""} onClick={() => setParams({ tab: item })}>
            {item}
          </button>
        ))}
      </div>
      {tab === "overview" && (
        <div className="cards">
          {((overview?.matches || []) as Match[]).map((match) => (
            <MatchCard key={match.id} match={match} />
          ))}
        </div>
      )}
      {tab === "matches" && (
        <>
          {((panel as { days?: Array<{ date: string; matches: Match[] }> } | null)?.days || []).map((day) => (
            <section className="group" key={day.date}>
              <h2>{day.date}</h2>
              <div className="cards">
                {day.matches.map((match) => (
                  <MatchCard key={match.id} match={match} />
                ))}
              </div>
            </section>
          ))}
        </>
      )}
      {tab === "calendar" && (
        <>
          <div className="row">
            <input className="field" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
          <div className="cards">
            {((panel as { matches?: Match[] } | null)?.matches || []).map((match) => (
              <MatchCard key={match.id} match={match} />
            ))}
          </div>
        </>
      )}
      {tab === "standings" && (
        <>
          <div className="tabs">
            {(["total", "home", "away"] as const).map((item) => (
              <button
                key={item}
                className={standingType === item ? "active" : ""}
                onClick={() => setParams({ tab: "standings", type: item })}
              >
                {item}
              </button>
            ))}
          </div>
          <StandingsTable data={panel as { rows?: Array<Record<string, unknown>>; empty?: boolean } | null} />
        </>
      )}
      {tab === "rounds" && (
        <>
          <label className="meta">
            Round <input className="field" value={round} onChange={(e) => setRound(e.target.value)} />
          </label>
          <div className="cards">
            {((panel as { matches?: Match[] } | null)?.matches || []).map((match) => (
              <MatchCard key={match.id} match={match} />
            ))}
          </div>
        </>
      )}
      {tab === "seasons" && (
        <div className="cards">
          {((panel as { seasons?: Array<{ id: number; name: string }> } | null)?.seasons || seasons).map((season) => (
            <div className="card" key={season.id}>
              {season.name} · {season.id}
            </div>
          ))}
        </div>
      )}
    </DataState>
  );
}

function StandingsTable({ data }: { data: { rows?: Array<Record<string, unknown>>; empty?: boolean } | null }) {
  if (!data) return <div className="state">Loading match data...</div>;
  const rows = data.rows || [];
  if (!rows.length) return <div className="state empty">No standings rows for this split.</div>;
  return (
    <table className="table">
      <thead>
        <tr>
          <th>#</th>
          <th>Team</th>
          <th>GP</th>
          <th>W</th>
          <th>L</th>
          <th>OTL</th>
          <th>Pts</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => {
          const team = (row.team || {}) as { id?: number | null; name?: string | null };
          return (
            <tr key={i}>
              <td>{String(row.position ?? "—")}</td>
              <td>{team.id ? <Link to={`/team/${team.id}`}>{String(team.name || team.id)}</Link> : String(team.name || "—")}</td>
              <td>{String(row.played ?? "—")}</td>
              <td>{String(row.won ?? "—")}</td>
              <td>{String(row.lost ?? "—")}</td>
              <td>{String(row.otl ?? "—")}</td>
              <td>{String(row.points ?? "—")}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export function CompetitionsPage() {
  const [data, setData] = useState<{ items: Array<{ id: number; name: string | null }> } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getTournaments().then(setData).catch((err: Error) => setError(err.message));
  }, []);
  return (
    <>
      <h1>Competitions</h1>
      <DataState loading={!data && !error} error={error}>
        <div className="cards">
          {(data?.items || []).map((item) => (
            <Link className="card" key={item.id} to={`/tournament/${item.id}`}>
              <strong>{item.name}</strong>
              <div className="meta">ID {item.id}</div>
            </Link>
          ))}
        </div>
      </DataState>
    </>
  );
}
