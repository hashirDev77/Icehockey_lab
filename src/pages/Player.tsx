import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { getPlayer, getPlayerMatches, getPlayerStatistics, getPlayers, type Match, type Player } from "../api";
import { DataState } from "../components/DataState";
import { MatchCard } from "../components/MatchCard";

export function PlayerPage() {
  const { id } = useParams();
  const [params, setParams] = useSearchParams();
  const tab = params.get("tab") || "overview";
  const [overview, setOverview] = useState<{ player: Player } | null>(null);
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [matches, setMatches] = useState<{ recent: Match[]; upcoming: Match[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const playerId = Number(id);

  useEffect(() => {
    if (!playerId) return;
    getPlayer(playerId).then(setOverview).catch((err: Error) => setError(err.message));
  }, [playerId]);

  useEffect(() => {
    if (!playerId) return;
    if (tab === "statistics") {
      getPlayerStatistics(playerId).then(setStats).catch((err: Error) => setError(err.message));
    }
    if (tab === "recent" || tab === "upcoming") {
      getPlayerMatches(playerId).then(setMatches).catch((err: Error) => setError(err.message));
    }
  }, [playerId, tab]);

  const player = overview?.player;
  return (
    <DataState loading={!overview && !error} error={error}>
      {player && (
        <>
          <h1>{player.name}</h1>
          <p className="meta">
            {player.team?.id ? <Link to={`/team/${player.team.id}`}>{player.team.name}</Link> : player.team?.name || "Team unknown"} ·{" "}
            {player.country || "Country unknown"} · {player.role || "Position unknown"}
            {player.jerseyNumber ? ` · #${player.jerseyNumber}` : ""}
          </p>
          <div className="tabs">
            {["overview", "statistics", "recent", "upcoming"].map((item) => (
              <button key={item} className={tab === item ? "active" : ""} onClick={() => setParams({ tab: item })}>
                {item}
              </button>
            ))}
          </div>
          {tab === "overview" && (
            <div className="panel">
              <p>Team: {player.team?.name || "—"}</p>
              <p>Country: {player.country || "—"}</p>
              <p>Position: {player.role || "—"}</p>
              <p>Jersey: {player.jerseyNumber || "—"}</p>
            </div>
          )}
          {tab === "statistics" && (
            <DataState loading={!stats} error={null} empty={Boolean(stats && stats.available === false)} emptyText="No statistics available for this season.">
              {stats && stats.available !== false && (
                <div className="panel">
                  <h2>
                    Season {String(stats.seasonId)} · tournament {String(stats.tournamentId)}
                  </h2>
                  <pre className="meta">{JSON.stringify(stats.body, null, 2)}</pre>
                </div>
              )}
            </DataState>
          )}
          {tab === "recent" && (
            <div className="cards">
              {(matches?.recent || []).map((match) => (
                <MatchCard key={match.id} match={match} />
              ))}
            </div>
          )}
          {tab === "upcoming" && (
            <DataState loading={!matches} error={null} empty={Boolean(matches && !matches.upcoming.length)} emptyText="No upcoming matches.">
              <div className="cards">
                {(matches?.upcoming || []).map((match) => (
                  <MatchCard key={match.id} match={match} />
                ))}
              </div>
            </DataState>
          )}
        </>
      )}
    </DataState>
  );
}

export function PlayersPage() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<{ items: Player[]; hasMore: boolean } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getPlayers(page).then(setData).catch((err: Error) => setError(err.message));
  }, [page]);
  return (
    <>
      <h1>Players</h1>
      <DataState loading={!data && !error} error={error}>
        <div className="cards">
          {(data?.items || []).map((player) => (
            <Link className="card" key={player.id} to={`/player/${player.id}`}>
              <strong>{player.name}</strong>
              <div className="meta">{player.role || ""}</div>
            </Link>
          ))}
        </div>
        <div className="row" style={{ marginTop: 12 }}>
          <button className="btn ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Previous
          </button>
          <button className="btn ghost" disabled={!data?.hasMore} onClick={() => setPage(page + 1)}>
            Next
          </button>
        </div>
      </DataState>
    </>
  );
}
