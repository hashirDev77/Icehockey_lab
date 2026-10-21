export interface HockeyStatus {
  code: string;
  label: string;
  description?: string | null;
}

export interface HockeyScore {
  display: string | null;
  current: number | null;
  period1: number | null;
  period2: number | null;
  period3: number | null;
  overtime: number | null;
  normaltime: number | null;
}

export interface HockeyTeamRef {
  id: number | null;
  name: string | null;
  shortName?: string | null;
  country?: string | null;
}

export interface HockeyTournamentRef {
  id: number | null;
  name: string | null;
}

export interface HockeyMatch {
  id: number;
  status: HockeyStatus;
  startTime: string | null;
  tournament: HockeyTournamentRef;
  homeTeam: HockeyTeamRef;
  awayTeam: HockeyTeamRef;
  score: { home: HockeyScore; away: HockeyScore };
  venue: string | null;
  result: string | null;
}

export interface HockeyPlayer {
  id: number;
  name: string | null;
  team: HockeyTeamRef | null;
  country: string | null;
  role: string | null;
  jerseyNumber: string | null;
}

export interface HockeyTournament {
  id: number;
  name: string | null;
  country: string | null;
  category: string | null;
  currentSeasonId: number | null;
}

export interface HockeySeason {
  id: number;
  name: string | null;
  year: string | null;
}

export interface HockeyStanding {
  position: number | null;
  team: HockeyTeamRef;
  played: number | null;
  won: number | null;
  lost: number | null;
  otl: number | null;
  points: number | null;
  raw: Record<string, unknown>;
}

export interface SearchHit {
  type: "player" | "team" | "tournament" | "unknown";
  id: number | null;
  name: string | null;
  country?: string | null;
}
