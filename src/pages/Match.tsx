import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { enrichmentTypes, getEventPlayerStatistics, getMatch, getMatchPanel, type Match } from "../api";
import { DataState } from "../components/DataState";
import { JsonPanel } from "../components/JsonPanel";
import { asArray, asRecord, unwrapList } from "../lib/unwrap";
import { periodLine } from "../lib/normalize";
import type { ProviderResult } from "../lib/client";

const tabs = [
  "overview",
  "incidents",
  "lineups",
  "statistics",
  "players",
  "best-players",
  "h2h",
  "pregame-form",
  "team-streaks",
  "enrichments",
] as const;

function score(side: Match["score"]["home"]) {
  return side.display || (side.current != null ? String(side.current) : "—");
}

export function MatchPage() {
  const { id } = useParams();
  const [params, setParams] = useSearchParams();
  const tab = (params.get("tab") || "overview") as (typeof tabs)[number];
  const type = params.get("type") || "";
  const playerId = params.get("player") || "";
  const [overview, setOverview] = useState<Record<string, unknown> | null>(null);
  const [panel, setPanel] = useState<ProviderResult | null>(null);
  const [playerStats, setPlayerStats] = useState<ProviderResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const matchId = Number(id);

  useEffect(() => {
    if (!matchId) return;
    setOverview(null);
    getMatch(matchId).then(setOverview).catch((err: Error) => setError(err.message));
  }, [matchId]);

  useEffect(() => {
    if (!matchId || tab === "overview") {
      setPanel(null);
      return;
    }
    getMatchPanel(matchId, tab, type || undefined)
      .then(setPanel)
      .catch((err: Error) => setError(err.message));
  }, [matchId, tab, type]);

  useEffect(() => {
    if (!matchId || tab !== "players" || !playerId) {
      setPlayerStats(null);
      return;
    }
    getEventPlayerStatistics(matchId, Number(playerId))
      .then(setPlayerStats)
      .catch((err: Error) => setError(err.message));
  }, [matchId, tab, playerId]);

  const match = overview?.match as Match | undefined;
  const types = tab === "enrichments" && panel ? enrichmentTypes(panel.body) : [];

  return (
    <DataState loading={!overview && !error} error={error}>
      {overview && match && (
        <>
          <div className="header-match card">
            <div className="meta">
              {match.tournament.id ? <Link to={`/tournament/${match.tournament.id}`}>{match.tournament.name}</Link> : match.tournament.name || "Tournament unavailable"}
            </div>
            <div className="teams">
              <div>
                <div>
                  {match.homeTeam.id ? <Link to={`/team/${match.homeTeam.id}`}>{match.homeTeam.name}</Link> : match.homeTeam.name}
                </div>
                <div className="score">{score(match.score.home)}</div>
                <div className="periods">{periodLine(match.score.home)}</div>
              </div>
              <div className="meta">vs</div>
              <div>
                <div>
                  {match.awayTeam.id ? <Link to={`/team/${match.awayTeam.id}`}>{match.awayTeam.name}</Link> : match.awayTeam.name}
                </div>
                <div className="score">{score(match.score.away)}</div>
                <div className="periods">{periodLine(match.score.away)}</div>
              </div>
            </div>
            <div className="meta">
              {match.status.label === "Live" ? <span className="live">Live</span> : match.status.label}{" "}
              {match.status.description ? `· ${match.status.description}` : ""}{" "}
              {match.startTime ? `· ${new Date(match.startTime).toLocaleString()}` : ""} {match.venue ? `· ${match.venue}` : ""}
            </div>
          </div>
          <div className="tabs">
            {tabs.map((item) => (
              <button key={item} className={tab === item ? "active" : ""} onClick={() => setParams({ tab: item })}>
                {item}
              </button>
            ))}
          </div>
          {tab === "overview" && <Overview overview={overview} match={match} />}
          {tab === "incidents" && <Incidents result={panel} />}
          {tab === "lineups" && <Lineups result={panel} />}
          {tab === "players" && (
            <PlayerStats
              result={panel}
              playerStats={playerStats}
              selected={playerId}
              onSelect={(pid) => setParams({ tab: "players", player: String(pid) })}
            />
          )}
          {tab !== "overview" && tab !== "incidents" && tab !== "lineups" && tab !== "players" && (
            <>
              {tab === "enrichments" && types.length > 0 && (
                <div className="tabs">
                  {types.map((item) => (
                    <button
                      key={item}
                      className={type === item ? "active" : ""}
                      onClick={() => setParams({ tab: "enrichments", type: item })}
                    >
                      {item}
                    </button>
                  ))}
                </div>
              )}
              <JsonPanel result={panel} />
            </>
          )}
        </>
      )}
    </DataState>
  );
}

function Overview({ overview, match }: { overview: Record<string, unknown>; match: Match }) {
  const streaks = overview.teamStreaks as { status: string; note?: string; data?: unknown };
  const best = overview.bestPlayers as { status: string; note?: string; data?: unknown };
  return (
    <div className="grid">
      <div className="panel">
        <h2>Match</h2>
        <p>Tournament: {match.tournament.name || "—"}</p>
        <p>Venue: {match.venue || "—"}</p>
        <p>Start: {match.startTime ? new Date(match.startTime).toLocaleString() : "—"}</p>
        <p>Status: {match.status.description || match.status.label}</p>
      </div>
      <div className="panel">
        <h2>Recent Form</h2>
        <pre className="meta">{JSON.stringify(overview.form, null, 2)}</pre>
      </div>
      <div className="panel">
        <h2>Head to Head</h2>
        <pre className="meta">{JSON.stringify(overview.h2h, null, 2)}</pre>
      </div>
      <div className="panel">
        <h2>Team Streaks</h2>
        {streaks?.status === "SUPPORTED" ? (
          <pre className="meta">{JSON.stringify(streaks.data, null, 2)}</pre>
        ) : (
          <p className="empty">{streaks?.note || "Team streak information is not available for this match."}</p>
        )}
      </div>
      <div className="panel">
        <h2>Best Players</h2>
        {best?.status === "SUPPORTED" ? (
          <pre className="meta">{JSON.stringify(best.data, null, 2)}</pre>
        ) : (
          <p className="empty">{best?.note || "Best player information is not available for this match."}</p>
        )}
      </div>
    </div>
  );
}

function Incidents({ result }: { result: ProviderResult | null }) {
  if (!result) return <div className="state">Loading match data...</div>;
  const rows = unwrapList(result.body);
  if (!rows.length) return <div className="state empty">No incidents are available for this match.</div>;
  return (
    <div className="panel">
      <p className="meta">
        <code>{result.endpoint}</code> · HTTP {result.status}
      </p>
      <table className="table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Type</th>
            <th>Player</th>
            <th>Detail</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const rec = asRecord(row) || {};
            const player = asRecord(rec.player);
            const pid = player?.id ?? rec.playerId;
            const name = String(player?.name || rec.playerName || "—");
            return (
              <tr key={i}>
                <td>{String(rec.time || rec.minute || rec.period || "—")}</td>
                <td>{String(rec.incidentType || rec.type || rec.class || "—")}</td>
                <td>{pid ? <Link to={`/player/${pid}`}>{name}</Link> : name}</td>
                <td>{String(rec.text || rec.reason || rec.description || "")}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Lineups({ result }: { result: ProviderResult | null }) {
  if (!result) return <div className="state">Loading match data...</div>;
  const body = result.body;
  if (!body) return <div className="state empty">No lineups are available for this match.</div>;
  return (
    <div className="grid">
      {(["home", "away"] as const).map((side) => {
        const block = asRecord(body[side]) || {};
        const manager = asRecord(block.manager) || asRecord(block.coach);
        const players = asArray(block.players);
        return (
          <div className="panel" key={side}>
            <h2>{side}</h2>
            {manager?.id ? (
              <p className="meta">
                Coach: <Link to={`/manager/${manager.id}`}>{String(manager.name || manager.id)}</Link>
              </p>
            ) : (
              <p className="meta">Coach: —</p>
            )}
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Player</th>
                  <th>Pos</th>
                </tr>
              </thead>
              <tbody>
                {players.map((row, i) => {
                  const rec = asRecord(row) || {};
                  const player = asRecord(rec.player) || rec;
                  const pid = player.id;
                  const name = String(player.name || "—");
                  return (
                    <tr key={i}>
                      <td>{String(player.jerseyNumber || rec.jerseyNumber || rec.shirtNumber || "—")}</td>
                      <td>{pid ? <Link to={`/player/${pid}`}>{name}</Link> : name}</td>
                      <td>{String(player.position || rec.position || "—")}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
}

function PlayerStats({
  result,
  playerStats,
  selected,
  onSelect,
}: {
  result: ProviderResult | null;
  playerStats: ProviderResult | null;
  selected: string;
  onSelect: (id: number) => void;
}) {
  if (!result) return <div className="state">Loading match data...</div>;
  const rows = unwrapList(result.body);
  if (!rows.length) return <div className="state empty">No player statistics are available for this match.</div>;
  return (
    <div className="grid">
      <div className="panel">
        <p className="meta">
          <code>{result.endpoint}</code> · click a row for <code>/event/{"{id}"}/player/{"{playerId}"}/statistics</code>
        </p>
        <table className="table">
          <thead>
            <tr>
              <th>Player</th>
              <th>Pos</th>
              <th>Team</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => {
              const rec = asRecord(row) || {};
              const player = asRecord(rec.player) || rec;
              const team = asRecord(rec.team);
              const pid = Number(player.id);
              return (
                <tr key={i}>
                  <td>
                    {pid ? (
                      <button className="btn ghost" onClick={() => onSelect(pid)}>
                        {String(player.name || pid)}
                      </button>
                    ) : (
                      String(player.name || "—")
                    )}
                  </td>
                  <td>{String(rec.position || player.position || "—")}</td>
                  <td>{team?.id ? <Link to={`/team/${team.id}`}>{String(team.name)}</Link> : "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {selected ? <JsonPanel label={`Player ${selected} match statistics`} result={playerStats} /> : null}
    </div>
  );
}
