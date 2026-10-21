import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  enrichmentTypes,
  getManager,
  getTeam,
  getTeamCompetitions,
  getTeamEnrichments,
  getTeamMatches,
  getTeamMedia,
  getTeamPerformance,
  getTeamRankings,
  getTeamSquad,
  getTeamStandingsSeasons,
  getTeams,
  type Match,
  type Player,
} from "../api";
import { DataState } from "../components/DataState";
import { JsonPanel } from "../components/JsonPanel";
import { MatchCard } from "../components/MatchCard";
import { asRecord } from "../lib/unwrap";
import type { ProviderResult } from "../lib/client";

export function TeamPage() {
  const { id } = useParams();
  const [params, setParams] = useSearchParams();
  const tab = params.get("tab") || "overview";
  const type = params.get("type") || "";
  const [overview, setOverview] = useState<Record<string, unknown> | null>(null);
  const [panel, setPanel] = useState<unknown>(null);
  const [enrich, setEnrich] = useState<ProviderResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const teamId = Number(id);

  useEffect(() => {
    if (!teamId) return;
    getTeam(teamId).then(setOverview).catch((err: Error) => setError(err.message));
  }, [teamId]);

  useEffect(() => {
    if (!teamId || tab === "overview") return;
    if (tab === "enrichments") {
      getTeamEnrichments(teamId, type || undefined)
        .then(setEnrich)
        .catch((err: Error) => setError(err.message));
      return;
    }
    const request =
      tab === "matches"
        ? getTeamMatches(teamId)
        : tab === "squad"
          ? getTeamSquad(teamId)
          : tab === "performance"
            ? getTeamPerformance(teamId)
            : tab === "rankings"
              ? getTeamRankings(teamId)
              : tab === "competitions"
                ? getTeamCompetitions(teamId)
                : tab === "standings-seasons"
                  ? getTeamStandingsSeasons(teamId)
                  : getTeamMedia(teamId);
    request.then(setPanel).catch((err: Error) => setError(err.message));
  }, [teamId, tab, type]);

  const team = overview?.team as { id: number; name: string; country?: string; managerId?: number } | undefined;
  const types = tab === "enrichments" && enrich ? enrichmentTypes(enrich.body) : [];

  return (
    <DataState loading={!overview && !error} error={error}>
      {team && (
        <>
          <h1>{String(team.name)}</h1>
          <p className="meta">{team.country ? String(team.country) : "Country unknown"}</p>
          <div className="tabs">
            {["overview", "matches", "squad", "performance", "rankings", "competitions", "standings-seasons", "media", "enrichments"].map(
              (item) => (
                <button key={item} className={tab === item ? "active" : ""} onClick={() => setParams({ tab: item })}>
                  {item}
                </button>
              ),
            )}
          </div>
          {tab === "overview" && (
            <div className="grid">
              <div className="panel">
                <h2>Previous match</h2>
                {overview?.previousMatch ? <MatchCard match={overview.previousMatch as Match} /> : <p className="empty">No previous match.</p>}
              </div>
              <div className="panel">
                <h2>Next match</h2>
                {overview?.nextMatch ? <MatchCard match={overview.nextMatch as Match} /> : <p className="empty">No next match.</p>}
              </div>
              <div className="panel">
                <h2>Featured event</h2>
                {overview?.featuredEvent ? <MatchCard match={overview.featuredEvent as Match} /> : <p className="empty">No featured event.</p>}
              </div>
              {team.managerId ? (
                <Link className="panel" to={`/manager/${team.managerId}`}>
                  Manager / staff #{String(team.managerId)}
                </Link>
              ) : (
                <div className="panel empty">No manager id on this team payload.</div>
              )}
            </div>
          )}
          {tab === "matches" && <TeamMatches data={panel as { fixtures?: Match[]; results?: Match[] } | null} />}
          {tab === "squad" && <Squad data={panel as { grouped?: Record<string, Player[]>; players?: Player[] } | null} />}
          {tab === "performance" && (
            <div className="cards">
              {((panel as { events?: Match[] } | null)?.events || []).map((match) => (
                <MatchCard key={match.id} match={match} />
              ))}
            </div>
          )}
          {tab === "rankings" && (
            <DataState
              loading={!panel}
              error={null}
              empty={Boolean(panel && ((panel as { missing?: boolean; items?: unknown[] }).missing || !(panel as { items?: unknown[] }).items?.length))}
              emptyText="Rankings are not recorded for this team."
            >
              <pre className="panel meta">{JSON.stringify((panel as { items?: unknown[] } | null)?.items, null, 2)}</pre>
            </DataState>
          )}
          {tab === "competitions" && (
            <div className="cards">
              {((panel as { items?: Array<{ id: number; name: string }> } | null)?.items || []).map((item) => (
                <Link className="card" key={item.id} to={`/tournament/${item.id}`}>
                  {item.name}
                </Link>
              ))}
            </div>
          )}
          {tab === "standings-seasons" && <pre className="panel meta">{JSON.stringify(panel, null, 2)}</pre>}
          {tab === "media" && <pre className="panel meta">{JSON.stringify((panel as { items?: unknown[] } | null)?.items, null, 2)}</pre>}
          {tab === "enrichments" && (
            <>
              {types.length > 0 && (
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
              <JsonPanel result={enrich} />
            </>
          )}
        </>
      )}
    </DataState>
  );
}

function TeamMatches({ data }: { data: { fixtures?: Match[]; results?: Match[] } | null }) {
  if (!data) return <div className="state">Loading match data...</div>;
  return (
    <>
      <h2>Fixtures</h2>
      <div className="cards">
        {(data.fixtures || []).map((match) => (
          <MatchCard key={match.id} match={match} />
        ))}
      </div>
      <h2>Results</h2>
      <div className="cards">
        {(data.results || []).map((match) => (
          <MatchCard key={match.id} match={match} />
        ))}
      </div>
    </>
  );
}

function Squad({ data }: { data: { grouped?: Record<string, Player[]>; players?: Player[] } | null }) {
  if (!data) return <div className="state">Loading match data...</div>;
  const groups = data.grouped || {};
  return (
    <>
      {Object.entries(groups).map(([name, players]) => (
        <section className="group" key={name}>
          <h2>{name}</h2>
          <div className="cards">
            {players.map((player) => (
              <Link className="card" key={player.id} to={`/player/${player.id}`}>
                {player.name}{" "}
                <div className="meta">
                  {player.role || "Position not available"}
                  {player.jerseyNumber ? ` · #${player.jerseyNumber}` : ""}
                </div>
              </Link>
            ))}
          </div>
        </section>
      ))}
    </>
  );
}

export function TeamsPage() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<{ items: Array<{ id: number; name: string }>; hasMore: boolean } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getTeams(page).then(setData).catch((err: Error) => setError(err.message));
  }, [page]);
  return (
    <>
      <h1>Teams</h1>
      <DataState loading={!data && !error} error={error}>
        <div className="cards">
          {(data?.items || []).map((team) => (
            <Link className="card" key={team.id} to={`/team/${team.id}`}>
              <strong>{team.name}</strong>
              <div className="meta">ID {team.id}</div>
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

export function ManagerPage() {
  const { id } = useParams();
  const [data, setData] = useState<Awaited<ReturnType<typeof getManager>> | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!id) return;
    getManager(Number(id)).then(setData).catch((err: Error) => setError(err.message));
  }, [id]);
  const manager = asRecord(data?.manager);
  return (
    <DataState loading={!data && !error} error={error}>
      <h1>{String(manager?.name || `Manager ${id}`)}</h1>
      <JsonPanel label="GET /manager/{id}" result={data?.result || null} />
    </DataState>
  );
}
