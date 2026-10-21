# Ice Hockey API — Testing Report

Live API test run against all **40** catalog routes. This document is for QA and integrators
(response shapes, verdicts, pagination, failures).

- **Test run (UTC):** 2026-10-21T15:49:34.751780+00:00
- **Base URL:** `https://sports-api.sportsdata365.com/msdata/v1/ice_hockey/...`
- **Evidence JSON:** [`../data/ice-hockey-endpoint-evidence.json`](../data/ice-hockey-endpoint-evidence.json)

## How tests were executed

1. Discover IDs via `search`, `team/.../events/last`, `lineups`, `enrichments`, `seasons`.
2. Call each route template with those IDs (see table below).
3. Record HTTP status, response size, top-level keys, list key, pagination, sample row keys.
4. Run additional filter/pagination/validation probes (see end).

### IDs used in this run

```json
{
  "eventId": 14124239,
  "teamId": 58336109,
  "playerId": 69552988,
  "lineupPlayerId": 25961100,
  "playerIdForEventStats": 47474035,
  "managerId": 58284567,
  "tournamentId": 40307999,
  "seasonId": 12009093,
  "enrichmentType": "best_players",
  "teamEnrichmentType": "events_last",
  "round": "1",
  "date": "2026-10-21"
}
```

## Verdict summary

| Verdict | Count | Meaning |
| --- | ---: | --- |
| **PASS** | 38 | HTTP 200 and non-empty payload fits expected type |
| **PASS_PARTIAL** | 0 | HTTP 200 but sparse or incomplete business data |
| **PASS_EMPTY** | 1 | HTTP 200 with valid empty/null business data |
| **OPTIONAL_MISSING** | 1 | HTTP 404 enrichment not recorded (optional route) |
| **FAIL** | 0 | Unexpected error |
| **EXPECTED** | 0 | Expected validation error |

## Matrix (all catalog routes)

| Verdict | HTTP | Route | Response kind | List key | Count |
| --- | ---: | --- | --- | --- | ---: |
| PASS | 200 | `/event/{eventId}` | match object | — | — |
| PASS | 200 | `/event/{eventId}/best-players` | paginated list | leaderboard | 10 |
| PASS | 200 | `/event/{eventId}/enrichments` | list envelope | types | 8 |
| PASS | 200 | `/event/{eventId}/enrichments/{type}` | paginated list | leaderboard | 10 |
| PASS_EMPTY | 200 | `/event/{eventId}/h2h` | object (teamDuel, managerDuel) | — | — |
| PASS | 200 | `/event/{eventId}/incidents` | paginated list | incidents | 5 |
| PASS | 200 | `/event/{eventId}/lineups` | home/away split (lineups or similar) | — | — |
| PASS | 200 | `/event/{eventId}/player-statistics` | paginated list | playerStatistics | 5 |
| PASS | 200 | `/event/{eventId}/player/{playerId}/statistics` | player object | — | — |
| PASS | 200 | `/event/{eventId}/pregame-form` | pregame form envelope | — | — |
| PASS | 200 | `/event/{eventId}/statistics` | list envelope | statistics | 4 |
| PASS | 200 | `/event/{eventId}/team-streaks` | object (general, generalPerLastX, genera | — | — |
| PASS | 200 | `/events` | paginated list | items | 5 |
| PASS | 200 | `/fixtures/today` | paginated list | items | 5 |
| PASS | 200 | `/manager/{managerId}` | manager object | — | — |
| PASS | 200 | `/player/{playerId}` | player object | — | — |
| PASS | 200 | `/player/{playerId}/events/{direction}` | paginated list | events | 5 |
| PASS | 200 | `/player/{playerId}/unique-tournament/{tournamentId}/season/{seasonId}/statistics` | statistics object | — | — |
| PASS | 200 | `/players` | paginated list | items | 5 |
| PASS | 200 | `/search` | paginated list | items | 1 |
| PASS | 200 | `/team/{teamId}` | team object | — | — |
| PASS | 200 | `/team/{teamId}/enrichments` | list envelope | types | 9 |
| PASS | 200 | `/team/{teamId}/enrichments/{type}` | paginated list | events | 10 |
| PASS | 200 | `/team/{teamId}/events/{direction}` | paginated list | events | 5 |
| PASS | 200 | `/team/{teamId}/featured-event` | match object | — | — |
| PASS | 200 | `/team/{teamId}/media` | paginated list | media | 5 |
| PASS | 200 | `/team/{teamId}/near-events` | previous/next event envelope | — | — |
| PASS | 200 | `/team/{teamId}/performance` | paginated list | events | 5 |
| PASS | 200 | `/team/{teamId}/players` | list envelope | players | 53 |
| OPTIONAL_MISSING | 404 | `/team/{teamId}/rankings` | error envelope | — | — |
| PASS | 200 | `/team/{teamId}/standings-seasons` | paginated list | uniqueTournamentSeasons | 1 |
| PASS | 200 | `/team/{teamId}/unique-tournaments` | paginated list | uniqueTournaments | 2 |
| PASS | 200 | `/teams` | paginated list | items | 5 |
| PASS | 200 | `/tournaments` | paginated list | items | 5 |
| PASS | 200 | `/unique-tournament/{tournamentId}` | competition object | — | — |
| PASS | 200 | `/unique-tournament/{tournamentId}/events` | paginated list | events | 5 |
| PASS | 200 | `/unique-tournament/{tournamentId}/scheduled-events/{date}` | paginated list | events | 5 |
| PASS | 200 | `/unique-tournament/{tournamentId}/season/{seasonId}/round/{round}` | paginated list | events | 5 |
| PASS | 200 | `/unique-tournament/{tournamentId}/season/{seasonId}/standings/{type}` | list envelope | standings | 1 |
| PASS | 200 | `/unique-tournament/{tournamentId}/seasons` | paginated list | seasons | 5 |

---

## Per-endpoint test results

### `/event/{eventId}`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 3813 bytes
- **Request:** `event/14124239`
- **Expected data (test plan):** Full match: teams, status object, period scores, venue, tournament.
- **Actual data returned:** match object · keys: `event` · nested: `id, homeTeam, awayTeam, tournament, season, roundInfo, status, statusType, startTimestamp, endTimestamp, sourceUpdatedAt, homeScore, awayScore, format`
- **Pagination:** N/A (not a paginated list)

### `/event/{eventId}/best-players`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 17216 bytes
- **Request:** `event/14124239/best-players`
- **Expected data (test plan):** Optional enrichment: ranked players for the match.
- **Actual data returned:** paginated list · keys: `bestHomeTeamPlayer, bestAwayTeamPlayer, leaderboard, page, limit, total, totalPages, hasMore` · array `leaderboard` (n=10) · row fields: `label, player, team, value`
- **Pagination:** page=1, limit=10, total=10, totalPages=1, hasMore=False

### `/event/{eventId}/enrichments`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 934 bytes
- **Request:** `event/14124239/enrichments`
- **Expected data (test plan):** Index of available match enrichment types.
- **Actual data returned:** list envelope · keys: `types` · array `types` (n=8) · row fields: `type, useCase`
- **Pagination:** N/A (not a paginated list)

### `/event/{eventId}/enrichments/{type}`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 17216 bytes
- **Request:** `event/14124239/enrichments/best_players`
- **Expected data (test plan):** Payload for one enrichment type (e.g. h2h_events → events list).
- **Actual data returned:** paginated list · keys: `bestHomeTeamPlayer, bestAwayTeamPlayer, leaderboard, page, limit, total, totalPages, hasMore` · array `leaderboard` (n=10) · row fields: `label, player, team, value`
- **Pagination:** page=1, limit=10, total=10, totalPages=1, hasMore=False

### `/event/{eventId}/h2h`

- **Verdict:** **PASS_EMPTY** — 200 but teamDuel/managerDuel null — no H2H data for sample.
- **HTTP:** 200 · **Response size:** 69 bytes
- **Request:** `event/14124239/h2h`
- **Expected data (test plan):** Prior meetings: teamDuel / managerDuel or linked events.
- **Actual data returned:** object (teamDuel, managerDuel) · keys: `teamDuel, managerDuel`
- **Pagination:** N/A (not a paginated list)

### `/event/{eventId}/incidents`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 9590 bytes
- **Request:** `event/14124239/incidents` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Match timeline: goals, penalties, period events.
- **Actual data returned:** paginated list · keys: `incidents, page, limit, total, totalPages, hasMore` · array `incidents` (n=5) · row fields: `time, timeMarker, timeSeconds, period, periodTimeSeconds, isHome, incidentType, incidentClass, player, playerIn, playerOut, assist, assists, penaltyDurationSeconds`
- **Pagination:** page=1, limit=5, total=26, totalPages=6, hasMore=True

### `/event/{eventId}/lineups`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 10923 bytes
- **Request:** `event/14124239/lineups`
- **Expected data (test plan):** home/away lineups: skaters, goalies, manager.
- **Actual data returned:** home/away split (lineups or similar) · keys: `home, away`
- **Pagination:** N/A (not a paginated list)

### `/event/{eventId}/player-statistics`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 11747 bytes
- **Request:** `event/14124239/player-statistics` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Paginated box-score rows per player.
- **Actual data returned:** paginated list · keys: `playerStatistics, page, limit, total, totalPages, hasMore, coverage` · array `playerStatistics` (n=5) · row fields: `team, player, position, statistics`
- **Pagination:** page=1, limit=5, total=22, totalPages=5, hasMore=True

### `/event/{eventId}/player/{playerId}/statistics`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 2004 bytes
- **Request:** `event/14124239/player/47474035/statistics`
- **Expected data (test plan):** One player's stats for this match.
- **Actual data returned:** player object · keys: `team, player, position, statistics` · nested: `id, name, firstName, lastName, shortName, position, gender, height, jerseyNumber, userCount, dateOfBirthTimestamp, marketValueCurrency, proposedMarketValueRaw, fieldTranslations`
- **Pagination:** N/A (not a paginated list)

### `/event/{eventId}/pregame-form`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 205 bytes
- **Request:** `event/14124239/pregame-form`
- **Expected data (test plan):** Recent W/L form and sample event ids per team.
- **Actual data returned:** pregame form envelope · keys: `homeTeam, awayTeam`
- **Pagination:** N/A (not a paginated list)

### `/event/{eventId}/statistics`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 13100 bytes
- **Request:** `event/14124239/statistics`
- **Expected data (test plan):** Team comparison stats (shots, goals, FO%, PIM).
- **Actual data returned:** list envelope · keys: `statistics, inconsistencies` · array `statistics` (n=4) · row fields: `period, groups`
- **Pagination:** N/A (not a paginated list)

### `/event/{eventId}/team-streaks`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 262 bytes
- **Request:** `event/14124239/team-streaks`
- **Expected data (test plan):** Streak buckets (may be empty arrays).
- **Actual data returned:** object (general, generalPerLastX, generalTotal, head2head, head2HeadPerLastX, head2HeadTotal) · keys: `general, generalPerLastX, generalTotal, head2head, head2HeadPerLastX, head2HeadTotal`
- **Pagination:** N/A (not a paginated list)

### `/events`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 2240 bytes
- **Request:** `events` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Paginated items[] of matches; supports page/limit/status.
- **Actual data returned:** paginated list · keys: `items, page, limit, total, totalPages, hasMore` · array `items` (n=5) · row fields: `id, tournamentId, homeTeam, awayTeam, startTimestamp, status, homeScore, awayScore, seasonId, competitionName`
- **Pagination:** page=1, limit=5, total=33, totalPages=7, hasMore=True

### `/fixtures/today`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 2240 bytes
- **Request:** `fixtures/today` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Paginated items[] for today's schedule.
- **Actual data returned:** paginated list · keys: `items, page, limit, total, totalPages, hasMore` · array `items` (n=5) · row fields: `id, tournamentId, homeTeam, awayTeam, startTimestamp, status, homeScore, awayScore, seasonId, competitionName`
- **Pagination:** page=1, limit=5, total=33, totalPages=7, hasMore=True

### `/manager/{managerId}`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 134 bytes
- **Request:** `manager/58284567`
- **Expected data (test plan):** Manager/coach profile object.
- **Actual data returned:** manager object · keys: `manager` · nested: `id, name, imageUrl`
- **Pagination:** N/A (not a paginated list)

### `/player/{playerId}`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 672 bytes
- **Request:** `player/69552988`
- **Expected data (test plan):** Player profile object.
- **Actual data returned:** player object · keys: `player` · nested: `id, name, firstName, lastName, shortName, position, gender, height, jerseyNumber, userCount, dateOfBirthTimestamp, marketValueCurrency, proposedMarketValueRaw, fieldTranslations`
- **Pagination:** N/A (not a paginated list)

### `/player/{playerId}/events/{direction}`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 18485 bytes
- **Request:** `player/69552988/events/last` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Paginated events[] (last/next).
- **Actual data returned:** paginated list · keys: `events, page, limit, total, totalPages, hasMore` · array `events` (n=5) · row fields: `id, homeTeam, awayTeam, tournament, season, roundInfo, status, statusType, startTimestamp, endTimestamp, sourceUpdatedAt, homeScore, awayScore, format`
- **Pagination:** page=1, limit=5, total=961, totalPages=193, hasMore=True

### `/player/{playerId}/unique-tournament/{tournamentId}/season/{seasonId}/statistics`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 904 bytes
- **Request:** `player/69552988/unique-tournament/40307999/season/12009093/statistics` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Season totals for one player in a competition.
- **Actual data returned:** statistics object · keys: `player, team, statistics, inconsistencies, playerId, teamId, uniqueTournamentId, seasonId` · nested: `appearances, assists, averageEvenTimeOnIce, averagePowerPlayTimeOnIce, averageShifts, averageShortHandedTimeOnIce, averageTimeOnIce, blocked, evenStrengthAssists, evenStrengthGoals, evenStrengthPoints, evenTimeOnIce, faceOffPercentage, faceOffTaken`
- **Pagination:** N/A (not a paginated list)

### `/players`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 455 bytes
- **Request:** `players` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Paginated items[] player directory.
- **Actual data returned:** paginated list · keys: `items, page, limit, total, totalPages, hasMore` · array `items` (n=5) · row fields: `id, name, countryAlpha2, position`
- **Pagination:** page=1, limit=5, total=15177, totalPages=3036, hasMore=True

### `/search`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 164 bytes
- **Request:** `search` · query `{'page': 1, 'limit': 5, 'q': 'Maple Leafs'}`
- **Expected data (test plan):** Paginated items[] typed hits (requires q).
- **Actual data returned:** paginated list · keys: `items, page, limit, total, totalPages, hasMore` · array `items` (n=1) · row fields: `type, id, name, countryAlpha2, gender`
- **Pagination:** page=1, limit=5, total=1, totalPages=1, hasMore=False

### `/team/{teamId}`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 842 bytes
- **Request:** `team/58336109`
- **Expected data (test plan):** Team profile object.
- **Actual data returned:** team object · keys: `team` · nested: `id, name, shortName, fullName, nameCode, type, gender, national, disabled, userCount, sport, country, teamColors, fieldTranslations`
- **Pagination:** N/A (not a paginated list)

### `/team/{teamId}/enrichments`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 1231 bytes
- **Request:** `team/58336109/enrichments`
- **Expected data (test plan):** types[] of team-level enrichments.
- **Actual data returned:** list envelope · keys: `types` · array `types` (n=9) · row fields: `type, useCase`
- **Pagination:** N/A (not a paginated list)

### `/team/{teamId}/enrichments/{type}`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 40181 bytes
- **Request:** `team/58336109/enrichments/events_last`
- **Expected data (test plan):** Data for one team enrichment (e.g. events_last).
- **Actual data returned:** paginated list · keys: `events, page, limit, total, totalPages, hasMore` · array `events` (n=10) · row fields: `id, homeTeam, awayTeam, tournament, season, roundInfo, status, statusType, startTimestamp, endTimestamp, sourceUpdatedAt, format, homeScore, awayScore`
- **Pagination:** page=1, limit=10, total=30, totalPages=3, hasMore=True

### `/team/{teamId}/events/{direction}`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 18917 bytes
- **Request:** `team/58336109/events/last` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Paginated events[] team schedule.
- **Actual data returned:** paginated list · keys: `events, page, limit, total, totalPages, hasMore` · array `events` (n=5) · row fields: `id, homeTeam, awayTeam, tournament, season, roundInfo, status, statusType, startTimestamp, endTimestamp, sourceUpdatedAt, homeScore, awayScore, format`
- **Pagination:** page=1, limit=5, total=1106, totalPages=222, hasMore=True

### `/team/{teamId}/featured-event`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 3908 bytes
- **Request:** `team/58336109/featured-event`
- **Expected data (test plan):** Single highlighted event object.
- **Actual data returned:** match object · keys: `event` · nested: `id, homeTeam, awayTeam, tournament, season, roundInfo, status, statusType, startTimestamp, endTimestamp, sourceUpdatedAt, format, homeScore, awayScore`
- **Pagination:** N/A (not a paginated list)

### `/team/{teamId}/media`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 1914 bytes
- **Request:** `team/58336109/media` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Paginated media[] (highlights URLs).
- **Actual data returned:** paginated list · keys: `media, page, limit, total, totalPages, hasMore` · array `media` (n=5) · row fields: `title, subtitle, url, sourceUrl, thumbnailUrl, mediaType, doFollow, livestream, keyHighlight, createdAtTimestamp, forCountries`
- **Pagination:** page=1, limit=5, total=10, totalPages=2, hasMore=True

### `/team/{teamId}/near-events`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 7811 bytes
- **Request:** `team/58336109/near-events`
- **Expected data (test plan):** previousEvent / nextEvent envelope.
- **Actual data returned:** previous/next event envelope · keys: `previousEvent, nextEvent, sourceUpdatedAt`
- **Pagination:** N/A (not a paginated list)

### `/team/{teamId}/performance`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 22702 bytes
- **Request:** `team/58336109/performance` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** form, events, points with pagination.
- **Actual data returned:** paginated list · keys: `order, sampleSize, form, events, points, page, limit, total, totalPages, hasMore` · array `events` (n=5) · row fields: `id, homeTeam, awayTeam, tournament, season, roundInfo, status, statusType, startTimestamp, endTimestamp, sourceUpdatedAt, format, homeScore, awayScore`
- **Pagination:** page=1, limit=5, total=20, totalPages=4, hasMore=True

### `/team/{teamId}/players`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 175397 bytes
- **Request:** `team/58336109/players`
- **Expected data (test plan):** players[] roster for team.
- **Actual data returned:** list envelope · keys: `players` · array `players` (n=53) · row fields: `player, position`
- **Pagination:** N/A (not a paginated list)

### `/team/{teamId}/rankings`

- **Verdict:** **OPTIONAL_MISSING** — Enrichment not on file for this entity (404).
- **HTTP:** 404 · **Response size:** 343 bytes
- **Request:** `team/58336109/rankings` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Optional enrichment rankings (often 404).
- **Actual data returned:** error envelope · keys: `statusCode, message, error, details, path, timestamp, requestId`
- **Pagination:** N/A (not a paginated list)
- **API error body:** `NotFound` — Enrichment "rankings" for ice hockey team 58336109 was not found.

### `/team/{teamId}/standings-seasons`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 5540 bytes
- **Request:** `team/58336109/standings-seasons` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Tournament/season groupings for standings.
- **Actual data returned:** paginated list · keys: `uniqueTournamentSeasons, tournamentSeasons, page, limit, total, totalPages, hasMore` · array `uniqueTournamentSeasons` (n=1) · row fields: `uniqueTournament, seasons`
- **Pagination:** page=1, limit=5, total=1, totalPages=1, hasMore=False

### `/team/{teamId}/unique-tournaments`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 1448 bytes
- **Request:** `team/58336109/unique-tournaments` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Paginated uniqueTournaments[].
- **Actual data returned:** paginated list · keys: `uniqueTournaments, page, limit, total, totalPages, hasMore` · array `uniqueTournaments` (n=2) · row fields: `id, name, userCount, primaryColorHex, secondaryColorHex, category, fieldTranslations, hasPerformanceGraphFeature, hasEventPlayerStatistics, displayInverseHomeAwayTeams, tennisPoints`
- **Pagination:** page=1, limit=5, total=2, totalPages=1, hasMore=False

### `/teams`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 384 bytes
- **Request:** `teams` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Paginated items[] team directory.
- **Actual data returned:** paginated list · keys: `items, page, limit, total, totalPages, hasMore` · array `items` (n=5) · row fields: `id, name, countryAlpha2`
- **Pagination:** page=1, limit=5, total=532, totalPages=107, hasMore=True

### `/tournaments`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 929 bytes
- **Request:** `tournaments` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Paginated items[] competition directory.
- **Actual data returned:** paginated list · keys: `items, page, limit, total, totalPages, hasMore` · array `items` (n=5) · row fields: `id, name, categoryName, countryAlpha2, logoUrl`
- **Pagination:** page=1, limit=5, total=115, totalPages=23, hasMore=True

### `/unique-tournament/{tournamentId}`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 642 bytes
- **Request:** `unique-tournament/40307999`
- **Expected data (test plan):** Competition metadata object.
- **Actual data returned:** competition object · keys: `uniqueTournament` · nested: `id, name, userCount, primaryColorHex, secondaryColorHex, category, fieldTranslations, hasPerformanceGraphFeature, hasEventPlayerStatistics, displayInverseHomeAwayTeams, tennisPoints`
- **Pagination:** N/A (not a paginated list)

### `/unique-tournament/{tournamentId}/events`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 17072 bytes
- **Request:** `unique-tournament/40307999/events` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Paginated events[] in competition.
- **Actual data returned:** paginated list · keys: `events, page, limit, total, totalPages, hasMore` · array `events` (n=5) · row fields: `id, homeTeam, awayTeam, tournament, season, roundInfo, status, statusType, startTimestamp, endTimestamp, sourceUpdatedAt, homeScore, awayScore, format`
- **Pagination:** page=1, limit=5, total=16141, totalPages=3229, hasMore=True

### `/unique-tournament/{tournamentId}/scheduled-events/{date}`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 18538 bytes
- **Request:** `unique-tournament/40307999/scheduled-events/2026-10-21` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Events on a calendar date.
- **Actual data returned:** paginated list · keys: `events, page, limit, total, totalPages, hasMore` · array `events` (n=5) · row fields: `id, homeTeam, awayTeam, tournament, season, roundInfo, status, statusType, startTimestamp, endTimestamp, sourceUpdatedAt, homeScore, awayScore, format`
- **Pagination:** page=1, limit=5, total=8, totalPages=2, hasMore=True

### `/unique-tournament/{tournamentId}/season/{seasonId}/round/{round}`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 18558 bytes
- **Request:** `unique-tournament/40307999/season/12009093/round/1` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Events for a season round.
- **Actual data returned:** paginated list · keys: `events, page, limit, total, totalPages, hasMore` · array `events` (n=5) · row fields: `id, homeTeam, awayTeam, tournament, season, roundInfo, status, statusType, startTimestamp, endTimestamp, sourceUpdatedAt, homeScore, awayScore, format`
- **Pagination:** page=1, limit=5, total=202, totalPages=41, hasMore=True

### `/unique-tournament/{tournamentId}/season/{seasonId}/standings/{type}`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 39563 bytes
- **Request:** `unique-tournament/40307999/season/12009093/standings/total`
- **Expected data (test plan):** standings[] table (total/home/away).
- **Actual data returned:** list envelope · keys: `standings` · array `standings` (n=1) · row fields: `type, descriptions, rows`
- **Pagination:** N/A (not a paginated list)

### `/unique-tournament/{tournamentId}/seasons`

- **Verdict:** **PASS** — 200 with parseable payload matching expected shape.
- **HTTP:** 200 · **Response size:** 425 bytes
- **Request:** `unique-tournament/40307999/seasons` · query `{'page': 1, 'limit': 5}`
- **Expected data (test plan):** Paginated seasons[].
- **Actual data returned:** paginated list · keys: `seasons, page, limit, total, totalPages, hasMore, currentSeasonId` · array `seasons` (n=5) · row fields: `id, name, year, editor`
- **Pagination:** page=1, limit=5, total=20, totalPages=4, hasMore=True

---

## Additional API tests (beyond 40-route catalog)

### events status=finished

- **Verdict:** **PASS** — Status filter returned rows.
- **HTTP:** 200 · **Path:** `events` · params `{'page': 1, 'limit': 5, 'status': 'finished'}`
- **Response:** paginated list · page=1, limit=5, total=8, totalPages=2, hasMore=True
- **List:** `items` count=5

### events status=inprogress

- **Verdict:** **PASS** — Status filter returned rows.
- **HTTP:** 200 · **Path:** `events` · params `{'page': 1, 'limit': 5, 'status': 'inprogress'}`
- **Response:** paginated list · page=1, limit=5, total=3, totalPages=1, hasMore=False
- **List:** `items` count=3

### events page=9999

- **Verdict:** **PASS_EMPTY** — Out-of-range page returns empty items with total unchanged (not 404).
- **HTTP:** 200 · **Path:** `events` · params `{'page': 9999, 'limit': 5}`
- **Response:** paginated list · page=9999, limit=5, total=33, totalPages=7, hasMore=False
- **List:** `items` count=0

### events page=2 differs from page=1

- **Verdict:** **PASS** — Page 2 first id (92487897) differs from page 1 (46983765).
- **HTTP:** 200 · **Path:** `events` · params `{'page': 2, 'limit': 5}`
- **Response:** paginated list · page=2, limit=5, total=33, totalPages=7, hasMore=True
- **List:** `items` count=5
- **Pagination check:** `{'page1FirstId': 46983765, 'page2FirstId': 92487897, 'differentPages': True}`

### search missing q

- **Verdict:** **EXPECTED** — Correct rejection when q is missing on /search.
- **HTTP:** 400 · **Path:** `search` · params `{'page': 1, 'limit': 5}`
- **Response:** error envelope · N/A (not a paginated list)

### event id non-numeric

- **Verdict:** **EXPECTED** — Expected validation error.
- **HTTP:** 400 · **Path:** `event/abc` · params `None`
- **Response:** error envelope · N/A (not a paginated list)

### event id unknown

- **Verdict:** **EXPECTED** — Unknown numeric event id should return 404.
- **HTTP:** 404 · **Path:** `event/999999999` · params `None`
- **Response:** error envelope · N/A (not a paginated list)

### standings home

- **Verdict:** **PASS_EMPTY** — 200 but standings rows empty for home/away split in this season.
- **HTTP:** 200 · **Path:** `unique-tournament/40307999/season/12009093/standings/home` · params `None`
- **Response:** list envelope · N/A (not a paginated list)
- **List:** `standings` count=1

### standings away

- **Verdict:** **PASS_EMPTY** — 200 but standings rows empty for home/away split in this season.
- **HTTP:** 200 · **Path:** `unique-tournament/40307999/season/12009093/standings/away` · params `None`
- **Response:** list envelope · N/A (not a paginated list)
- **List:** `standings` count=1

### player events next

- **Verdict:** **PASS_EMPTY**
- **HTTP:** 200 · **Path:** `player/69552988/events/next` · params `{'page': 1, 'limit': 5}`
- **Response:** paginated list · page=1, limit=5, total=0, totalPages=0, hasMore=False
- **List:** `events` count=0

### team events next

- **Verdict:** **PASS**
- **HTTP:** 200 · **Path:** `team/58336109/events/next` · params `{'page': 1, 'limit': 5}`
- **Response:** paginated list · page=1, limit=5, total=4, totalPages=1, hasMore=False
- **List:** `events` count=4

---

## Notes

- Catalog count is **40** ice hockey routes (`ice_hockey` prefix).
- List calls used `page=1&limit=5` unless the route is a single object.
- `/team/{teamId}/rankings` returned 404 `ENRICHMENT_NOT_FOUND` (optional).
- `/event/{eventId}/h2h` returned 200 with null `teamDuel` / `managerDuel` for the sample match.
- `/events?status=finished` and `inprogress` returned real rows (unlike some other sports where those filters are empty).
- `/events?page=9999` is HTTP 200 with an empty `items` list; `total` / `totalPages` stay set (leftover pagination totals).
- Home/away standings exist as envelopes with empty `rows` for this season; `total` standings are populated.
- Per-event player statistics need a player from `/player-statistics`, not an arbitrary lineup row (`PLAYER_NOT_FOUND` / `not_in_match` otherwise).

## Regenerate this report

```bash
python3 scripts/probe_all_endpoints.py
python3 scripts/generate_api_testing_report.py
```
