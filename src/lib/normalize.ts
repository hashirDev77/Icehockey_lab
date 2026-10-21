import type { Json } from "./client";
import { asArray, asRecord, unwrapEvent, unwrapList, unwrapPlayer, unwrapTournament } from "./unwrap";
import type {
  HockeyMatch,
  HockeyPlayer,
  HockeyScore,
  HockeySeason,
  HockeyStanding,
  HockeyStatus,
  HockeyTeamRef,
  HockeyTournament,
  HockeyTournamentRef,
  SearchHit,
} from "./types";

function num(value: unknown): number | null {
  if (value == null || value === "") return null;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : null;
}

function str(value: unknown): string | null {
  if (value == null) return null;
  if (typeof value === "object") return null;
  const text = String(value).trim();
  return text ? text : null;
}

export function teamRef(value: unknown): HockeyTeamRef {
  const rec = asRecord(value) || {};
  return {
    id: num(rec.id),
    name: str(rec.name) || str(rec.shortName),
    shortName: str(rec.shortName) || str(rec.nameCode),
    country: str(asRecord(rec.country)?.name) || str(rec.country),
  };
}

function labelForStatus(code: string, description?: string | null): string {
  const value = `${code} ${description || ""}`.toLowerCase();
  if (value.includes("inprogress") || value.includes("live") || value.includes("period") || value.includes("ot")) {
    return "Live";
  }
  if (value.includes("notstarted") || value.includes("upcoming") || code === "0") return "Upcoming";
  if (value.includes("finished") || value.includes("complete") || value.includes("aet") || ["100", "110"].includes(code)) {
    return "Completed";
  }
  if (value.includes("cancel")) return "Cancelled";
  if (value.includes("postpon")) return "Postponed";
  return description || code;
}

export function normalizeStatus(raw: unknown): HockeyStatus {
  if (typeof raw === "string") {
    return { code: raw, label: labelForStatus(raw), description: raw };
  }
  const rec = asRecord(raw) || {};
  const code = str(rec.type) || str(rec.code) || str(rec.description) || "unknown";
  const description = str(rec.description);
  return { code, label: labelForStatus(code, description), description };
}

export function normalizeTimestamp(raw: unknown): string | null {
  if (raw == null) return null;
  if (typeof raw === "number") return new Date(raw * 1000).toISOString();
  const text = String(raw);
  if (/^\d+$/.test(text)) {
    const seconds = Number(text);
    if (seconds > 1e9) return new Date(seconds * 1000).toISOString();
  }
  const parsed = Date.parse(text);
  if (!Number.isNaN(parsed)) return new Date(parsed).toISOString();
  return text;
}

function scoreFromBlock(block: unknown): HockeyScore {
  const rec = asRecord(block) || {};
  const current = num(rec.current) ?? num(rec.display);
  const display = str(rec.display) || (current != null ? String(current) : null);
  return {
    display,
    current,
    period1: num(rec.period1),
    period2: num(rec.period2),
    period3: num(rec.period3),
    overtime: num(rec.overtime),
    normaltime: num(rec.normaltime),
  };
}

export function isLive(match: HockeyMatch): boolean {
  const code = match.status.code.toLowerCase();
  const desc = (match.status.description || "").toLowerCase();
  return match.status.label === "Live" || code.includes("inprogress") || desc.includes("period");
}

export function normalizeMatch(raw: unknown): HockeyMatch | null {
  const rec = asRecord(raw) || unwrapEvent(asRecord(raw));
  if (!rec || rec.id == null) return null;
  const nestedTour = asRecord(rec.tournament);
  const tournamentRaw = asRecord(rec.uniqueTournament) || asRecord(nestedTour?.uniqueTournament) || nestedTour;
  const tournament: HockeyTournamentRef = {
    id: num(tournamentRaw?.id) ?? num(rec.tournamentId) ?? num(rec.uniqueTournamentId),
    name: str(tournamentRaw?.name) || str(rec.tournamentName) || str(rec.competitionName),
  };
  const status = normalizeStatus(rec.status ?? rec.statusType);
  return {
    id: Number(rec.id),
    status,
    startTime: normalizeTimestamp(rec.startTimestamp ?? rec.startTime),
    tournament,
    homeTeam: teamRef(rec.homeTeam),
    awayTeam: teamRef(rec.awayTeam),
    score: { home: scoreFromBlock(rec.homeScore), away: scoreFromBlock(rec.awayScore) },
    venue: str(asRecord(rec.venue)?.name) || str(rec.venue),
    result: str(rec.note) || (status.label === "Completed" ? status.description ?? null : null),
  };
}

export function normalizeMatches(body: Json | null): HockeyMatch[] {
  return unwrapList(body)
    .map((item) => normalizeMatch(item))
    .filter((item): item is HockeyMatch => Boolean(item));
}

export function normalizePlayer(raw: unknown): HockeyPlayer | null {
  const rec = asRecord(raw) || unwrapPlayer(asRecord(raw));
  const nested = rec ? unwrapPlayer(rec) || rec : null;
  const player = nested && nested.id != null ? nested : rec;
  if (!player || player.id == null) return null;
  const team = asRecord(player.team) || asRecord(rec?.team);
  return {
    id: Number(player.id),
    name: str(player.name) || [str(player.firstName), str(player.lastName)].filter(Boolean).join(" ") || null,
    team: team ? teamRef(team) : null,
    country: str(asRecord(player.country)?.name) || str(player.country) || str(player.nationality),
    role: str(player.position) || str(player.role) || str(rec?.position),
    jerseyNumber: str(player.jerseyNumber) || str(rec?.jerseyNumber),
  };
}

export function normalizeTournament(raw: unknown): HockeyTournament | null {
  const rec = asRecord(raw) || unwrapTournament(asRecord(raw));
  if (!rec || rec.id == null) return null;
  return {
    id: Number(rec.id),
    name: str(rec.name),
    country: str(asRecord(rec.category)?.name) || str(asRecord(rec.country)?.name) || str(rec.country),
    category: str(asRecord(rec.category)?.name) || str(rec.category),
    currentSeasonId: num(asRecord(rec.currentSeason)?.id) ?? num(rec.currentSeasonId),
  };
}

export function normalizeSeason(raw: unknown): HockeySeason | null {
  const rec = asRecord(raw);
  if (!rec || rec.id == null) return null;
  return { id: Number(rec.id), name: str(rec.name) || str(rec.year), year: str(rec.year) || str(rec.name) };
}

export function normalizeStandings(body: Json | null): HockeyStanding[] {
  const standings = asArray(body?.standings);
  const rows = standings.flatMap((group) => asArray(asRecord(group)?.rows));
  return rows.map((row) => {
    const rec = asRecord(row) || {};
    return {
      position: num(rec.position) ?? num(rec.rank),
      team: teamRef(rec.team),
      played: num(rec.matches) ?? num(rec.played) ?? num(rec.p),
      won: num(rec.wins) ?? num(rec.won) ?? num(rec.w),
      lost: num(rec.losses) ?? num(rec.lost) ?? num(rec.l),
      otl: num(rec.overtimeLosses) ?? num(rec.otl),
      points: num(rec.points) ?? num(rec.pts),
      raw: rec,
    };
  });
}

export function normalizeSearch(body: Json | null): SearchHit[] {
  return unwrapList(body).map((row) => {
    const rec = asRecord(row) || {};
    const rawType = str(rec.type) || str(rec.entityType) || "";
    const type = rawType.toLowerCase().includes("player")
      ? "player"
      : rawType.toLowerCase().includes("team")
        ? "team"
        : rawType.toLowerCase().includes("tournament")
          ? "tournament"
          : "unknown";
    return {
      type,
      id: num(rec.id),
      name: str(rec.name),
      country: str(asRecord(rec.country)?.name) || str(rec.countryAlpha2) || str(rec.country),
    };
  });
}

export function groupSearch(hits: SearchHit[]) {
  return {
    players: hits.filter((hit) => hit.type === "player"),
    teams: hits.filter((hit) => hit.type === "team"),
    competitions: hits.filter((hit) => hit.type === "tournament"),
    other: hits.filter((hit) => hit.type === "unknown"),
  };
}

export function periodLine(score: HockeyScore): string {
  const parts = [
    score.period1 != null ? `P1 ${score.period1}` : null,
    score.period2 != null ? `P2 ${score.period2}` : null,
    score.period3 != null ? `P3 ${score.period3}` : null,
    score.overtime != null && score.overtime !== 0 ? `OT ${score.overtime}` : null,
  ].filter(Boolean);
  return parts.join(" · ");
}
