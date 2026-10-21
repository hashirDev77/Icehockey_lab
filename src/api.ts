import { SAMPLE } from "./catalog";
import { iceHockeyGet, type Json } from "./lib/client";
import { asArray, asRecord, unwrapEvent, unwrapList, unwrapManager, unwrapPlayer, unwrapTeam, unwrapTournament } from "./lib/unwrap";
import {
  groupSearch,
  isLive,
  normalizeMatch,
  normalizeMatches,
  normalizePlayer,
  normalizeSearch,
  normalizeSeason,
  normalizeStandings,
  normalizeTournament,
} from "./lib/normalize";
import type { HockeyMatch, HockeyPlayer } from "./lib/types";

export type Match = HockeyMatch;
export type Player = HockeyPlayer;
export { iceHockeyGet };
export type { ProviderResult } from "./lib/client";

function widget(status: string, data: unknown, note?: string) {
  return { status, data, note };
}

export async function getHome() {
  const [fixtures, liveFeed, tours] = await Promise.all([
    iceHockeyGet("fixtures/today", { limit: 20 }),
    iceHockeyGet("events", { status: "inprogress", limit: 20 }),
    iceHockeyGet("tournaments", { page: 1, limit: 12 }),
  ]);
  const byId = new Map<number, HockeyMatch>();
  for (const match of [...normalizeMatches(fixtures.body), ...normalizeMatches(liveFeed.body)]) {
    byId.set(match.id, match);
  }
  const live: HockeyMatch[] = [];
  const today: HockeyMatch[] = [];
  const upcoming: HockeyMatch[] = [];
  const completed: HockeyMatch[] = [];
  for (const match of byId.values()) {
    const code = match.status.code.toLowerCase();
    if (isLive(match)) live.push(match);
    else if (code.includes("finish") || match.status.label === "Completed") completed.push(match);
    else upcoming.push(match);
    today.push(match);
  }
  const competitions = unwrapList(tours.body)
    .map(normalizeTournament)
    .filter((row): row is NonNullable<typeof row> => Boolean(row));
  return { live, today, upcoming, completed, competitions };
}

export async function getMatches(tab?: string) {
  if (tab === "today" || !tab) {
    const fixtures = await iceHockeyGet("fixtures/today", { limit: 40 });
    const list = normalizeMatches(fixtures.body);
    return { live: list.filter(isLive), today: list, upcoming: list.filter((m) => m.status.label === "Upcoming"), results: list.filter((m) => m.status.label === "Completed") };
  }
  const status = tab === "live" ? "inprogress" : tab === "results" ? "finished" : tab === "upcoming" ? "notstarted" : undefined;
  const events = await iceHockeyGet("events", { status, limit: 40 });
  const list = normalizeMatches(events.body);
  return {
    live: tab === "live" ? list : list.filter(isLive),
    today: list,
    upcoming: tab === "upcoming" ? list : list.filter((m) => m.status.label === "Upcoming"),
    results: tab === "results" ? list : list.filter((m) => m.status.label === "Completed"),
  };
}

export async function getMatch(id: number) {
  const [eventRes, form, h2h, streaks, best] = await Promise.all([
    iceHockeyGet(`event/${id}`),
    iceHockeyGet(`event/${id}/pregame-form`),
    iceHockeyGet(`event/${id}/h2h`),
    iceHockeyGet(`event/${id}/team-streaks`),
    iceHockeyGet(`event/${id}/best-players`),
  ]);
  const match = normalizeMatch(unwrapEvent(eventRes.body) || eventRes.body);
  if (!match) throw new Error("This information could not be loaded.");
  return {
    match,
    endpoint: eventRes.endpoint,
    form: form.body,
    h2h: h2h.body,
    teamStreaks: streaks.body ? widget("SUPPORTED", streaks.body) : widget("EMPTY", null, "Team streak information is not available for this match."),
    bestPlayers: best.body ? widget("SUPPORTED", best.body) : widget("EMPTY", null, "Best player information is not available for this match."),
  };
}

export async function getMatchPanel(id: number, tab: string, type?: string) {
  if (tab === "incidents") return iceHockeyGet(`event/${id}/incidents`, { page: 1, limit: 50 });
  if (tab === "lineups") return iceHockeyGet(`event/${id}/lineups`);
  if (tab === "statistics") return iceHockeyGet(`event/${id}/statistics`);
  if (tab === "players") return iceHockeyGet(`event/${id}/player-statistics`, { page: 1, limit: 50 });
  if (tab === "best-players") return iceHockeyGet(`event/${id}/best-players`);
  if (tab === "h2h") return iceHockeyGet(`event/${id}/h2h`);
  if (tab === "pregame-form") return iceHockeyGet(`event/${id}/pregame-form`);
  if (tab === "team-streaks") return iceHockeyGet(`event/${id}/team-streaks`);
  if (tab === "enrichments" && type) return iceHockeyGet(`event/${id}/enrichments/${type}`);
  if (tab === "enrichments") return iceHockeyGet(`event/${id}/enrichments`);
  throw new Error(`Unknown match tab ${tab}`);
}

export async function getEventPlayerStatistics(eventId: number, playerId: number) {
  return iceHockeyGet(`event/${eventId}/player/${playerId}/statistics`);
}

export async function getSearch(q: string) {
  const result = await iceHockeyGet("search", { q, page: 1, limit: 20 });
  const hits = normalizeSearch(result.body);
  const seen = new Set<string>();
  const unique = hits.filter((hit) => {
    const key = `${hit.type}:${hit.id}:${hit.name}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  return { query: q, ...groupSearch(unique) };
}

export async function getPlayer(id: number) {
  const result = await iceHockeyGet(`player/${id}`);
  const player = normalizePlayer(unwrapPlayer(result.body) || result.body);
  if (!player) throw new Error("This information could not be loaded.");
  return { player };
}

export async function getPlayerMatches(id: number) {
  const [last, next] = await Promise.all([
    iceHockeyGet(`player/${id}/events/last`, { page: 1, limit: 10 }),
    iceHockeyGet(`player/${id}/events/next`, { page: 1, limit: 10 }),
  ]);
  return { recent: normalizeMatches(last.body), upcoming: normalizeMatches(next.body) };
}

export async function getPlayerStatistics(
  id: number,
  tournamentId = SAMPLE.tournamentId,
  seasonId = SAMPLE.seasonId,
) {
  const result = await iceHockeyGet(
    `player/${id}/unique-tournament/${tournamentId}/season/${seasonId}/statistics`,
  );
  if (result.status === 404 || !result.body) {
    return { available: false, tournamentId, seasonId, body: null };
  }
  return { available: true, tournamentId, seasonId, body: result.body };
}

export async function getPlayers(page = 1) {
  const result = await iceHockeyGet("players", { page, limit: 20 });
  return {
    items: unwrapList(result.body)
      .map((row) => normalizePlayer(row))
      .filter((row): row is HockeyPlayer => Boolean(row)),
    hasMore: Boolean(asRecord(result.body)?.hasMore),
  };
}

export async function getTeam(id: number) {
  const [profile, near, featured] = await Promise.all([
    iceHockeyGet(`team/${id}`),
    iceHockeyGet(`team/${id}/near-events`),
    iceHockeyGet(`team/${id}/featured-event`),
  ]);
  const team = asRecord(unwrapTeam(profile.body) || profile.body);
  if (!team) throw new Error("This information could not be loaded.");
  const featuredEvent = unwrapEvent(featured.body);
  return {
    team: {
      id,
      name: team.name,
      country: asRecord(team.country)?.name || team.country || null,
      managerId: asRecord(team.manager)?.id || team.managerId || null,
    },
    previousMatch: normalizeMatch(asRecord(near.body?.previousEvent)),
    nextMatch: normalizeMatch(asRecord(near.body?.nextEvent)),
    featuredEvent: featuredEvent ? normalizeMatch(featuredEvent) : null,
  };
}

export async function getTeamMatches(id: number) {
  const [last, next] = await Promise.all([
    iceHockeyGet(`team/${id}/events/last`, { page: 1, limit: 15 }),
    iceHockeyGet(`team/${id}/events/next`, { page: 1, limit: 15 }),
  ]);
  return { results: normalizeMatches(last.body), fixtures: normalizeMatches(next.body) };
}

export async function getTeamSquad(id: number) {
  const result = await iceHockeyGet(`team/${id}/players`);
  const players = unwrapList(result.body)
    .map((row) => normalizePlayer(row))
    .filter((row): row is HockeyPlayer => Boolean(row));
  const roleGroup = (role: string | null) => {
    const value = (role || "").toLowerCase();
    if (value === "g" || value.includes("goal")) return "goalies";
    if (value === "d" || value.includes("defenc") || value.includes("defens")) return "defense";
    if (["c", "lw", "rw", "f", "w"].includes(value) || value.includes("forward") || value.includes("center") || value.includes("wing")) {
      return "forwards";
    }
    return "unknown";
  };
  return {
    players,
    grouped: {
      forwards: players.filter((player) => roleGroup(player.role) === "forwards"),
      defense: players.filter((player) => roleGroup(player.role) === "defense"),
      goalies: players.filter((player) => roleGroup(player.role) === "goalies"),
      unknown: players.filter((player) => roleGroup(player.role) === "unknown"),
    },
  };
}

export async function getTeamPerformance(id: number) {
  const result = await iceHockeyGet(`team/${id}/performance`, { page: 1, limit: 10 });
  return { events: normalizeMatches(result.body), raw: result.body };
}

export async function getTeamRankings(id: number) {
  const result = await iceHockeyGet(`team/${id}/rankings`, { page: 1, limit: 20 });
  return { items: unwrapList(result.body), missing: result.status === 404 };
}

export async function getTeamCompetitions(id: number) {
  const result = await iceHockeyGet(`team/${id}/unique-tournaments`, { page: 1, limit: 30 });
  return { items: unwrapList(result.body).map(normalizeTournament).filter(Boolean) };
}

export async function getTeamStandingsSeasons(id: number) {
  const result = await iceHockeyGet(`team/${id}/standings-seasons`, { page: 1, limit: 20 });
  return { items: unwrapList(result.body), body: result.body };
}

export async function getTeamMedia(id: number) {
  const result = await iceHockeyGet(`team/${id}/media`, { page: 1, limit: 20 });
  return { items: unwrapList(result.body) };
}

export async function getTeamEnrichments(id: number, type?: string) {
  if (type) return iceHockeyGet(`team/${id}/enrichments/${type}`);
  return iceHockeyGet(`team/${id}/enrichments`);
}

export async function getTeams(page = 1) {
  const result = await iceHockeyGet("teams", { page, limit: 20 });
  return {
    items: unwrapList(result.body)
      .map((row) => {
        const rec = asRecord(row) || {};
        return { id: Number(rec.id), name: String(rec.name || rec.shortName || "") };
      })
      .filter((team) => team.id && team.name),
    hasMore: Boolean(asRecord(result.body)?.hasMore),
  };
}

export async function getManager(id: number) {
  const result = await iceHockeyGet(`manager/${id}`);
  return { manager: unwrapManager(result.body) || result.body, status: result.status, result };
}

export async function getTournaments(page = 1) {
  const result = await iceHockeyGet("tournaments", { page, limit: 30 });
  return { items: unwrapList(result.body).map(normalizeTournament).filter(Boolean) };
}

export async function getTournament(id: number) {
  const [profile, seasons, events] = await Promise.all([
    iceHockeyGet(`unique-tournament/${id}`),
    iceHockeyGet(`unique-tournament/${id}/seasons`, { page: 1, limit: 20 }),
    iceHockeyGet(`unique-tournament/${id}/events`, { page: 1, limit: 10 }),
  ]);
  const tournament = normalizeTournament(unwrapTournament(profile.body) || profile.body);
  const seasonList = unwrapList(seasons.body)
    .map(normalizeSeason)
    .filter((row): row is NonNullable<typeof row> => Boolean(row));
  return {
    tournament,
    seasons: seasonList,
    currentSeasonId: tournament?.currentSeasonId ?? (seasons.body as Json | null)?.currentSeasonId ?? seasonList[0]?.id ?? null,
    matches: normalizeMatches(events.body),
  };
}

export async function getTournamentMatches(id: number, date?: string) {
  const result = date
    ? await iceHockeyGet(`unique-tournament/${id}/scheduled-events/${date}`)
    : await iceHockeyGet(`unique-tournament/${id}/events`, { page: 1, limit: 40 });
  const matches = normalizeMatches(result.body);
  const byDay = new Map<string, typeof matches>();
  for (const match of matches) {
    const day = match.startTime ? match.startTime.slice(0, 10) : "Unknown date";
    const list = byDay.get(day) || [];
    list.push(match);
    byDay.set(day, list);
  }
  return { days: [...byDay.entries()].map(([dateKey, items]) => ({ date: dateKey, matches: items })), matches };
}

export async function getTournamentSeasons(id: number) {
  const result = await iceHockeyGet(`unique-tournament/${id}/seasons`, { page: 1, limit: 30 });
  return {
    seasons: unwrapList(result.body)
      .map(normalizeSeason)
      .filter((row): row is NonNullable<typeof row> => Boolean(row)),
  };
}

export async function getTournamentStandings(id: number, seasonId: number, type: "total" | "home" | "away" = "total") {
  const result = await iceHockeyGet(`unique-tournament/${id}/season/${seasonId}/standings/${type}`);
  const rows = normalizeStandings(result.body);
  return { columns: ["position", "team", "played", "won", "lost", "otl", "points"], rows, empty: rows.length === 0 };
}

export async function getTournamentRound(id: number, seasonId: number, round: string) {
  const result = await iceHockeyGet(`unique-tournament/${id}/season/${seasonId}/round/${round}`, { page: 1, limit: 40 });
  return { matches: normalizeMatches(result.body) };
}

export function enrichmentTypes(body: Json | null): string[] {
  return asArray(body?.types)
    .map((item) => {
      const rec = asRecord(item);
      return typeof item === "string" ? item : String(rec?.type || rec?.name || "");
    })
    .filter(Boolean);
}
