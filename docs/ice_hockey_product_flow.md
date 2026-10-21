# Ice Hockey Product — user flow test

Walked against the local Vite app at `http://127.0.0.1:5176` (proxy `/msdata`). Sample entity IDs from catalog: event `14124239`, team `58336109`, player `69552988`, manager `58284567`, tournament `40307999`, season `12009093`.

## Journeys

| Journey | Endpoints used | User sees | Completes? | Issue |
| --- | --- | --- | --- | --- |
| Home `/` | `GET fixtures/today` (total=33), `GET events?status=inprogress` (total=5), `GET tournaments` (total=115) | Live Now + Today + Recently Completed cards with competition names (NHL, KHL, Liiga…); Competitions grid; Upcoming empty | Partial | `notstarted` fixtures shown under Live Now with Live badge; Home Upcoming empty |
| Live `/live` | same as Home (`getHome`) | 12 cards mixing true `inprogress` and `notstarted` all tagged Live | Partial | Live chrome does not call `events?status=inprogress` alone; status label bug |
| Matches → Live | `GET events?status=inprogress` (total=5) | 5 in-progress cards only | Yes | — |
| Matches → Today | `GET fixtures/today` (total=33) | 33 cards; competition names present | Yes | Upcoming-looking rows still show Live badge when status is `notstarted` |
| Matches → Upcoming | `GET events?status=notstarted` (total=20) | 20 cards | Partial | Every card badge says Live (`labelForStatus` treats `"ot"` inside `notstarted` / `Not started` as live) |
| Matches → Results | `GET events?status=finished` (total=8) | 8 completed cards; no canceled | Yes | — |
| Match overview `/match/14124239` | `GET event/{id}`, `pregame-form`, `h2h`, `team-streaks`, `best-players` | CBJ 2–6 TOR header, periods, venue; form / H2H / streaks / best players panels | Yes | H2H `managerDuel` is null (shown as JSON null, tab not blank) |
| Match → incidents | `GET event/{id}/incidents` (HTTP 200, 26 rows) | Incidents table | Yes | — |
| Match → lineups | `GET event/{id}/lineups` (HTTP 200) | Home/away tables; coaches Rick Bowness / Craig Berube link to `/manager/...` | Yes | Primary path into Manager (no chrome nav) |
| Match → statistics | `GET event/{id}/statistics` (HTTP 200) | Period statistics JSON | Yes | Raw JSON panel |
| Match → players | `GET event/{id}/player-statistics` (22 rows); click → `GET event/{id}/player/{playerId}/statistics` (HTTP 200 for `47474035`) | Player table + per-player JSON | Yes | — |
| Match → best-players | `GET event/{id}/best-players` (HTTP 200) | Best players JSON | Yes | — |
| Match → h2h | `GET event/{id}/h2h` (HTTP 200) | `teamDuel` wins + `managerDuel: null` | Yes | — |
| Match → pregame-form | `GET event/{id}/pregame-form` (HTTP 200) | Form JSON | Yes | — |
| Match → team-streaks | `GET event/{id}/team-streaks` (HTTP 200) | Streaks JSON | Yes | — |
| Match → enrichments | `GET event/{id}/enrichments` (8 types); typed `.../enrichments/best_players` (HTTP 200) | Type chips + JSON; no raw 404 banner | Yes | — |
| Search `q=dallas` | `GET search` (total=2) | Players: Dallas Ehrhardt; Teams: Dallas Stars; Competitions empty | Yes | — |
| Teams `/teams` | `GET teams` (total=532, page of 20) | Team cards with IDs | Yes | — |
| Team overview `/team/58336109` | `GET team/{id}`, `near-events`, `featured-event` | Toronto Maple Leafs; previous/next/featured cards | Partial | “No manager id on this team payload.”; next match shows Live + “Not started” |
| Team → matches | `GET team/{id}/events/last` + `.../next` | Fixtures (4) + Results (15) | Yes | — |
| Team → squad | `GET team/{id}/players` (53) | forwards / defense / goalies / **unknown** groups | Yes | Some players land in `unknown` position bucket |
| Team → performance | `GET team/{id}/performance` (10 events) | Match cards | Yes | — |
| Team → rankings | `GET team/{id}/rankings` → HTTP 404 | Empty copy: “Rankings are not recorded for this team.” | Yes | Optional 404 handled; not raw error JSON |
| Team → competitions | `GET team/{id}/unique-tournaments` (2) | NHL, NHL Preseason links | Yes | — |
| Team → standings-seasons | `GET team/{id}/standings-seasons` (HTTP 200) | JSON panel | Yes | — |
| Team → media | `GET team/{id}/media` (10) | Media JSON | Yes | — |
| Team → enrichments | `GET team/{id}/enrichments` (9 types); typed `events_last` (HTTP 200) | Type chips + JSON | Yes | — |
| Players `/players` | `GET players` (total=15177, page of 20) | Player cards (Ovechkin, McDavid, …) | Yes | — |
| Player `/player/69552988` | `GET player/{id}` | Connor McDavid · C · #97 | Partial | “Team unknown · Country unknown” — API `team: null`, no country on payload |
| Player → statistics | `GET player/{id}/unique-tournament/{tid}/season/{sid}/statistics` (HTTP 200) | Season stats JSON (appearances, points, …) | Yes | Hard-coded SAMPLE tournament/season IDs |
| Player → recent | `GET player/{id}/events/last` (10 of total=961) | Recent match cards | Yes | — |
| Player → upcoming | `GET player/{id}/events/next` (total=0) | “No upcoming matches.” | Yes | Empty is accurate for this player |
| Competitions `/competitions` | `GET tournaments` (30 on page) | NHL, IIHF, Olympics, KHL, SHL… | Yes | — |
| Tournament overview `/tournament/40307999` | `GET unique-tournament/{id}`, `seasons`, `events` | NHL · North America; match cards dated **2009** | Partial | `/events` first page is ancient; not current season |
| Tournament → matches | `GET unique-tournament/{id}/events` | Days grouped in Apr 2009 | Partial | Same oldest-first list |
| Tournament → calendar | `GET unique-tournament/{id}/scheduled-events/2026-10-21` (total=8) | 8 NHL cards for today | Yes | — |
| Tournament → standings | `GET .../season/12009093/standings/total` | 96-row table (NHL 26/27) | Yes | — |
| Tournament → rounds | `GET .../season/{sid}/round/1` (40 of total=202) | Current-season round cards | Yes | — |
| Tournament → seasons | `GET unique-tournament/{id}/seasons` | 20 season cards (NHL 26/27 …) | Yes | — |
| Manager `/manager/58284567` | `GET manager/{id}` (HTTP 200) | Rick Bowness + JSON | Yes | Not in chrome nav; team overview has no manager id; reachable from lineups coaches |
| Endpoints `/endpoints` | Lab can `GET` any of the 40 catalog routes | 40 route buttons + sample ID fields | Yes | Lab-only; not a product journey |

## Endpoint coverage from the product

| Catalog route | Called from UI? | Screen |
| --- | --- | --- |
| `/v1/ice_hockey/event/{eventId}` | yes | Match overview |
| `/v1/ice_hockey/event/{eventId}/best-players` | yes | Match overview + best-players tab |
| `/v1/ice_hockey/event/{eventId}/enrichments` | yes | Match enrichments |
| `/v1/ice_hockey/event/{eventId}/enrichments/{type}` | yes | Match enrichments type chip |
| `/v1/ice_hockey/event/{eventId}/h2h` | yes | Match overview + h2h tab |
| `/v1/ice_hockey/event/{eventId}/incidents` | yes | Match incidents |
| `/v1/ice_hockey/event/{eventId}/lineups` | yes | Match lineups |
| `/v1/ice_hockey/event/{eventId}/player-statistics` | yes | Match players |
| `/v1/ice_hockey/event/{eventId}/player/{playerId}/statistics` | yes | Match players row click |
| `/v1/ice_hockey/event/{eventId}/pregame-form` | yes | Match overview + pregame-form |
| `/v1/ice_hockey/event/{eventId}/statistics` | yes | Match statistics |
| `/v1/ice_hockey/event/{eventId}/team-streaks` | yes | Match overview + team-streaks |
| `/v1/ice_hockey/events` | yes | Home/Live merge; Matches Live/Upcoming/Results |
| `/v1/ice_hockey/fixtures/today` | yes | Home; Matches Today |
| `/v1/ice_hockey/manager/{managerId}` | yes | Manager page (from lineup coach links) |
| `/v1/ice_hockey/player/{playerId}` | yes | Player |
| `/v1/ice_hockey/player/{playerId}/events/{direction}` | yes | Player recent / upcoming |
| `/v1/ice_hockey/player/{playerId}/unique-tournament/{tournamentId}/season/{seasonId}/statistics` | yes | Player statistics |
| `/v1/ice_hockey/players` | yes | Players list |
| `/v1/ice_hockey/search` | yes | Search |
| `/v1/ice_hockey/team/{teamId}` | yes | Team overview |
| `/v1/ice_hockey/team/{teamId}/enrichments` | yes | Team enrichments |
| `/v1/ice_hockey/team/{teamId}/enrichments/{type}` | yes | Team enrichments type chip |
| `/v1/ice_hockey/team/{teamId}/events/{direction}` | yes | Team matches |
| `/v1/ice_hockey/team/{teamId}/featured-event` | yes | Team overview |
| `/v1/ice_hockey/team/{teamId}/media` | yes | Team media |
| `/v1/ice_hockey/team/{teamId}/near-events` | yes | Team overview |
| `/v1/ice_hockey/team/{teamId}/performance` | yes | Team performance |
| `/v1/ice_hockey/team/{teamId}/players` | yes | Team squad |
| `/v1/ice_hockey/team/{teamId}/rankings` | yes | Team rankings (404 → empty copy) |
| `/v1/ice_hockey/team/{teamId}/standings-seasons` | yes | Team standings-seasons |
| `/v1/ice_hockey/team/{teamId}/unique-tournaments` | yes | Team competitions |
| `/v1/ice_hockey/teams` | yes | Teams list |
| `/v1/ice_hockey/tournaments` | yes | Home competitions; Competitions |
| `/v1/ice_hockey/unique-tournament/{tournamentId}` | yes | Tournament |
| `/v1/ice_hockey/unique-tournament/{tournamentId}/events` | yes | Tournament overview / matches |
| `/v1/ice_hockey/unique-tournament/{tournamentId}/scheduled-events/{date}` | yes | Tournament calendar |
| `/v1/ice_hockey/unique-tournament/{tournamentId}/season/{seasonId}/round/{round}` | yes | Tournament rounds |
| `/v1/ice_hockey/unique-tournament/{tournamentId}/season/{seasonId}/standings/{type}` | yes | Tournament standings |
| `/v1/ice_hockey/unique-tournament/{tournamentId}/seasons` | yes | Tournament overview / seasons |

All **40** catalog routes are reachable from product screens (plus `/endpoints` lab).

## User-facing issues (priority)

1. **Live badge on non-live games (blocker).** `labelForStatus` treats substring `"ot"` as overtime/live, so `notstarted` / description `Not started` become label `Live`. Home Live Now, chrome Live, Matches Upcoming, and team “next match” all mislabel. Cause: client (`src/lib/normalize.ts`).

2. **Home / chrome Live mix upcoming into Live (high).** `LivePage` and Home Live section use `getHome()` + broken `isLive`, so `notstarted` fixtures appear as live while true Live count from API is 5. Matches → Live (status filter) is correct. Cause: client.

3. **Home Upcoming empty (high).** Same mislabel pushes upcoming into Live; user sees “No matches in this section right now.” while Matches → Upcoming has 20. Cause: client.

4. **Tournament overview / matches show 2009 games (high).** `GET unique-tournament/{id}/events` first page is oldest-first; calendar/standings/rounds for current season work. Cause: API ordering + client not filtering by season on overview/matches.

5. **Manager unreachable from chrome / team overview (medium).** No nav link; Leafs `GET team/{id}` has no `manager` / `managerId`. Manager works at `/manager/58284567` and from lineup coach links. Cause: API payload gap + product IA.

6. **Player profile missing team/country (medium).** McDavid page shows “Team unknown · Country unknown” while season stats work. Cause: API `player.team` null / no country fields.

7. **Squad “unknown” position group (low).** Some roster players not mapped to forwards/defense/goalies. Cause: client role heuristics / sparse position strings.

8. **Many detail tabs are raw JSON (low).** Statistics, enrichments, H2H, media, etc. are readable for a lab but not end-user UI. Cause: product lab design.

Not observed this run: `[object Object]` errors; Home “Competition unknown” with name present; Results canceled games; rankings tab dumping HTTP 404 JSON; blank H2H tab; player season stats missing when route 200s.

## Not walked

- Every enrichment type chip beyond `best_players` (event) and `events_last` (team).
- Tournament standings `home` / `away` splits (only `total`).
- Pagination beyond first page on Teams / Players / Competitions.
- Live match detail while a game is in progress (sample walk used finished event `14124239`).
