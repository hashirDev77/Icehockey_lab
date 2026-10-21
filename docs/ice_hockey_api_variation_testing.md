# Ice Hockey API — Variation & pagination testing

Supplement to [`ice_hockey_api_testing_report.md`](./ice_hockey_api_testing_report.md).
Tests **different entities**, **match states**, **status filters**, **list vs detail**, **auth**, **validity**, and **pagination** (including **page 2000**).

- **Generated (UTC):** 2026-10-21T16:00:32.481494+00:00
- **Raw JSON:** [`../data/ice-hockey-variation-tests.json`](../data/ice-hockey-variation-tests.json)
- **Tests run:** 123

## Event IDs used (by state)

```json
{
  "finished": 14124239,
  "canceled": 75533566,
  "notstarted": 13888228,
  "inprogress": 58366713
}
```

Same sub-routes were called on **finished**, **canceled**, and **notstarted** events when those IDs were discoverable from search, team history, fixtures, or status filters.

```json
{
  "teamId": 58336109,
  "teamName": "Maple Leafs",
  "team2Id": 67204796,
  "team2Name": "Montr\u00e9al Canadiens",
  "playerId": 69552988,
  "playerName": "McDavid",
  "player2Id": 94770949,
  "player2Name": "Sidney Crosby",
  "tournamentId": 40307999,
  "seasonId": 12009093
}
```

## Verdict summary

| Verdict | Count |
| --- | ---: |
| EXPECTED | 15 |
| PASS | 78 |
| PASS_EMPTY | 30 |

## Does page 2000 return real data?

| Endpoint | page=2000 result | Interpretation |
| --- | --- | --- |
| `events` | HTTP 200, count=0, totalPages=7 | **Empty 200** — page is beyond `totalPages`; list = []. Not fake rows; **misleading `total` stays high**. |
| `players` | HTTP 200, count=5, totalPages=3036 | **Real data** — page exists within `totalPages`. |
| `teams` | HTTP 200, count=0, totalPages=107 | **Empty 200** — page is beyond `totalPages`; list = []. Not fake rows; **misleading `total` stays high**. |
| `team/58336109/events/last` | HTTP 200, count=0, totalPages=222 | **Empty 200** — page is beyond `totalPages`; list = []. Not fake rows; **misleading `total` stays high**. |
| `unique-tournament/40307999/events` | HTTP 200, count=5, totalPages=3229 | **Real data** — page exists within `totalPages`. |
| `event/14124239/incidents` | HTTP 200, count=0, totalPages=6 | **Empty 200** — page is beyond `totalPages`; list = []. Not fake rows; **misleading `total` stays high**. |

**Important:** `GET /unique-tournament/40307999/events?page=2000` returned **real rows** because `totalPages` is ≥ 2000.

**`limit=2000`:** `events limit=2000` HTTP 400, `search limit=2000` HTTP 400.

## Status filter matrix (`GET /events`)

| status param | HTTP | total | items in page |
| --- | ---: | ---: | ---: |
| `finished` | 200 | 8 | 5 |
| `inprogress` | 200 | 3 | 3 |
| `notstarted` | 200 | 22 | 5 |
| `canceled` | 200 | 0 | 0 |
| `postponed` | 200 | 0 | 0 |
| `ended` | 400 | — | — |

Team `events/last` has a long finished history (total=1106) while unfiltered `/events` is a **windowed** feed (total=33). `status=finished` on that window is **not empty**.

## All variation tests

| Category | Name | HTTP | Verdict | list count | total | totalPages |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| pagination | events page 1 vs page 2 | 200 | PASS | 5 | 33 | 7 |
| pagination | events page 1 | 200 | PASS | 5 | 33 | 7 |
| pagination | players page 1 vs page 2 | 200 | PASS | 5 | 15177 | 3036 |
| pagination | players page 1 | 200 | PASS | 5 | 15177 | 3036 |
| pagination | teams page 1 vs page 2 | 200 | PASS | 5 | 532 | 107 |
| pagination | teams page 1 | 200 | PASS | 5 | 532 | 107 |
| pagination | team events last page 1 vs page 2 | 200 | PASS | 5 | 1106 | 222 |
| pagination | team events last page 1 | 200 | PASS | 5 | 1106 | 222 |
| pagination | ut events page 1 vs page 2 | 200 | PASS | 5 | 16141 | 3229 |
| pagination | ut events page 1 | 200 | PASS | 5 | 16141 | 3229 |
| pagination | incidents page 1 vs page 2 | 200 | PASS | 5 | 26 | 6 |
| pagination | incidents page 1 | 200 | PASS | 5 | 26 | 6 |
| pagination_edge | events page 2000 | 200 | PASS_EMPTY | 0 | 33 | 7 |
| pagination_edge | events page 9999 | 200 | PASS_EMPTY | 0 | 33 | 7 |
| pagination_edge | events last page (7) | 200 | PASS | 3 | 33 | 7 |
| pagination_edge | events page 8 beyond totalPages | 200 | PASS_EMPTY | 0 | 33 | 7 |
| pagination_edge | players page 2000 | 200 | PASS | 5 | 15177 | 3036 |
| pagination_edge | players page 9999 | 200 | PASS_EMPTY | 0 | 15177 | 3036 |
| pagination_edge | players last page (3036) | 200 | PASS | 2 | 15177 | 3036 |
| pagination_edge | players page 3037 beyond totalPages | 200 | PASS_EMPTY | 0 | 15177 | 3036 |
| pagination_edge | teams page 2000 | 200 | PASS_EMPTY | 0 | 532 | 107 |
| pagination_edge | teams page 9999 | 200 | PASS_EMPTY | 0 | 532 | 107 |
| pagination_edge | teams last page (107) | 200 | PASS | 2 | 532 | 107 |
| pagination_edge | teams page 108 beyond totalPages | 200 | PASS_EMPTY | 0 | 532 | 107 |
| pagination_edge | team events last page 2000 | 200 | PASS_EMPTY | 0 | 1106 | 222 |
| pagination_edge | team events last page 9999 | 200 | PASS_EMPTY | 0 | 1106 | 222 |
| pagination_edge | team events last last page (222) | 200 | PASS | 1 | 1106 | 222 |
| pagination_edge | team events last page 223 beyond totalPages | 200 | PASS_EMPTY | 0 | 1106 | 222 |
| pagination_edge | ut events page 2000 | 200 | PASS | 5 | 16141 | 3229 |
| pagination_edge | ut events page 9999 | 200 | PASS_EMPTY | 0 | 16141 | 3229 |
| pagination_edge | ut events last page (3229) | 200 | PASS | 1 | 16141 | 3229 |
| pagination_edge | ut events page 3230 beyond totalPages | 200 | PASS_EMPTY | 0 | 16141 | 3229 |
| pagination_edge | incidents (short list) page 2000 | 200 | PASS_EMPTY | 0 | 26 | 6 |
| pagination_edge | incidents (short list) page 9999 | 200 | PASS_EMPTY | 0 | 26 | 6 |
| pagination_edge | incidents (short list) last page (6) | 200 | PASS | 1 | 26 | 6 |
| pagination_edge | incidents (short list) page 7 beyond totalPages | 200 | PASS_EMPTY | 0 | 26 | 6 |
| limit_variation | events limit=1 | 200 | PASS | 1 | 33 | 33 |
| limit_variation | events limit=100 | 200 | PASS | 33 | 33 | 1 |
| limit_variation | events limit=2000 | 400 | EXPECTED | — | — | — |
| limit_variation | search limit=1 | 200 | PASS | 1 | 1 | 1 |
| limit_variation | search limit=100 | 200 | PASS | 1 | 1 | 1 |
| limit_variation | search limit=2000 | 400 | EXPECTED | — | — | — |
| status_filter | events status=finished | 200 | PASS | 5 | 8 | 2 |
| status_filter | events status=inprogress | 200 | PASS | 3 | 3 | 1 |
| status_filter | events status=notstarted | 200 | PASS | 5 | 22 | 5 |
| status_filter | events status=canceled | 200 | PASS_EMPTY | 0 | 0 | 0 |
| status_filter | events status=postponed | 200 | PASS_EMPTY | 0 | 0 | 0 |
| status_filter | events status=ended | 400 | EXPECTED | — | — | — |
| status_filter | team events last vs events?status=finished | 200 | PASS | 30 | 1106 | 37 |
| query_params | invalid standings type | 400 | EXPECTED | — | — | — |
| query_params | invalid events direction | 400 | EXPECTED | — | — | — |
| query_params | invalid calendar date | 400 | EXPECTED | — | — | — |
| response_stats | events | 200 | PASS | 5 | 33 | 7 |
| response_stats | players | 200 | PASS | 5 | 15177 | 3036 |
| response_stats | teams | 200 | PASS | 5 | 532 | 107 |
| response_stats | tournaments | 200 | PASS | 5 | 115 | 23 |
| response_stats | search | 200 | PASS | 1 | 1 | 1 |
| response_stats | team roster (no pagination expected) | 200 | PASS | 53 | — | — |
| response_stats | standings total (no pagination expected) | 200 | PASS | 1 | — | — |
| response_stats | incidents | 200 | PASS | 5 | 26 | 6 |
| response_stats | player-statistics | 200 | PASS | 5 | 22 | 5 |
| response_stats | team media | 200 | PASS | 5 | 10 | 2 |
| response_stats | team unique-tournaments | 200 | PASS | 2 | 2 | 1 |
| response_stats | ut seasons | 200 | PASS | 5 | 20 | 4 |
| list_vs_detail | same event list vs detail status/score/competition | 200 | PASS | — | — | — |
| list_vs_detail | fixtures/today vs default /events | 200 | PASS | 20 | 33 | 2 |
| list_vs_detail | events list sample | 200 | PASS | 5 | 33 | 7 |
| data_validity | player.team null vs nested copies | 200 | PASS | — | — | — |
| data_validity | team.country on profile | 200 | PASS | — | — | — |
| data_validity | h2h null duels | 200 | PASS | — | — | — |
| data_validity | best-players (optional enrichment) | 200 | PASS | 10 | 10 | 1 |
| data_validity | team rankings (optional enrichment) | 404 | EXPECTED | — | — | — |
| data_validity | off-catalog top-performers | 404 | EXPECTED | — | — | — |
| data_validity | standings total row count | 200 | PASS | 1 | — | — |
| data_validity | standings home row count | 200 | PASS_EMPTY | 1 | — | — |
| data_validity | standings away row count | 200 | PASS_EMPTY | 1 | — | — |
| data_validity | featured-event status | 200 | PASS | — | — | — |
| data_validity | lineup jersey numbers | 200 | PASS | — | — | — |
| data_validity | error message shape (non-numeric event id) | 400 | EXPECTED | — | — | — |
| off_catalog | football-style player season stats (on-catalog for hockey) | 200 | PASS | — | — | — |
| off_catalog | off-catalog player/{id}/statistics | 404 | EXPECTED | — | — | — |
| off_catalog | off-catalog team season statistics | 200 | PASS | — | — | — |
| auth | /events?limit=1 both headers | 200 | PASS | 1 | 33 | 33 |
| auth | /events?limit=1 X-Live-Key only | 200 | PASS | 1 | 33 | 33 |
| auth | /events?limit=1 x-apim-key only | 403 | EXPECTED | — | — | — |
| auth | /events?limit=1 no API keys | 403 | EXPECTED | — | — | — |
| event_state_variation | finished event detail | 200 | PASS | — | — | — |
| event_state_variation | finished event/lineups | 200 | PASS | — | — | — |
| event_state_variation | finished event/statistics | 200 | PASS | 4 | — | — |
| event_state_variation | finished event/incidents | 200 | PASS | 5 | 26 | 6 |
| event_state_variation | finished event/best-players | 200 | PASS | 10 | 10 | 1 |
| event_state_variation | finished event/player-statistics | 200 | PASS | 5 | 22 | 5 |
| event_state_variation | canceled event detail | 200 | PASS | — | — | — |
| event_state_variation | canceled event/lineups | 200 | PASS | — | — | — |
| event_state_variation | canceled event/statistics | 200 | PASS_EMPTY | 0 | — | — |
| event_state_variation | canceled event/incidents | 200 | PASS_EMPTY | 0 | 0 | 0 |
| event_state_variation | canceled event/best-players | 404 | EXPECTED | — | — | — |
| event_state_variation | canceled event/player-statistics | 200 | PASS_EMPTY | 0 | 0 | 0 |
| event_state_variation | notstarted event detail | 200 | PASS | — | — | — |
| event_state_variation | notstarted event/lineups | 200 | PASS | — | — | — |
| event_state_variation | notstarted event/statistics | 200 | PASS_EMPTY | 0 | — | — |
| event_state_variation | notstarted event/incidents | 200 | PASS_EMPTY | 0 | 0 | 0 |
| event_state_variation | notstarted event/best-players | 404 | EXPECTED | — | — | — |
| event_state_variation | notstarted event/player-statistics | 200 | PASS_EMPTY | 0 | 0 | 0 |
| event_state_variation | inprogress event detail | 200 | PASS | — | — | — |
| event_state_variation | inprogress event/lineups | 200 | PASS | — | — | — |
| event_state_variation | inprogress event/statistics | 200 | PASS_EMPTY | 0 | — | — |
| event_state_variation | inprogress event/incidents | 200 | PASS_EMPTY | 0 | 0 | 0 |
| event_state_variation | inprogress event/best-players | 404 | EXPECTED | — | — | — |
| event_state_variation | inprogress event/player-statistics | 200 | PASS_EMPTY | 0 | 0 | 0 |
| entity_variation | team events last (Maple Leafs) | 200 | PASS | 3 | 1106 | 369 |
| entity_variation | team events last (Montréal Canadiens) | 200 | PASS | 3 | 1111 | 371 |
| entity_variation | player events last (McDavid) | 200 | PASS | 3 | 961 | 321 |
| entity_variation | player events last (Sidney Crosby) | 200 | PASS | 3 | 991 | 331 |
| enrichment_type_variation | event enrichments index | 200 | PASS | 8 | — | — |
| enrichment_type_variation | event enrichments/best_players | 200 | PASS | 10 | 10 | 1 |
| enrichment_type_variation | event enrichments/best_players_summary | 200 | PASS | 10 | 10 | 1 |
| enrichment_type_variation | event enrichments/h2h_events | 200 | PASS | 10 | 38 | 4 |
| enrichment_type_variation | event enrichments/highlights | 200 | PASS | — | — | — |
| enrichment_type_variation | event enrichments/series | 200 | PASS_EMPTY | 0 | 0 | 0 |
| enrichment_type_variation | event enrichments/shotmap | 200 | PASS | — | — | — |
| enrichment_type_variation | event enrichments/team_streaks | 200 | PASS | — | — | — |
| enrichment_type_variation | event enrichments/votes | 200 | PASS | — | — | — |

## Interpretation

- Page 2 is a **new slice** on the lists that were compared (events, players, teams, team history, competition events, incidents).
- Pages beyond `totalPages` (including **9999** and **2000** on short lists) return **HTTP 200 + empty arrays**, not 404 and not fabricated rows. **`total` / `totalPages` stay set** — leftover pagination totals.
- Invalid status token `ended` returned HTTP 400 (EXPECTED).
- `/events?status=finished` returned rows (total=8). Global `/events` is a **windowed** feed, not full team history.
- `/events?status=inprogress` HTTP 200, total=3, count=3.
- invalid standings type: HTTP 400 (EXPECTED) — `unique-tournament/40307999/season/12009093/standings/nope`.
- invalid events direction: HTTP 400 (EXPECTED) — `team/58336109/events/sideways`.
- invalid calendar date: HTTP 400 (EXPECTED) — `unique-tournament/40307999/scheduled-events/not-a-date`.
- Families that **omit pagination**: `team roster (no pagination expected)`, `standings total (no pagination expected)`.
- List vs detail: `/events` items use `status` as a **string** (`finished`); `/event/{id}` uses an object `{'code': 110, 'type': 'finished', 'description': 'AET'}`. List `competitionName`='NHL'; detail has nested `tournament`. Detail `homeScore` keys=['current', 'display', 'period1', 'period2', 'period3', 'overtime', 'normaltime'] (periods + overtime, not a baseball innings box).
- `/fixtures/today` vs default `/events`: first-page ids **match**; byte size **differs** (events 2240 bytes, fixtures 7023 bytes). Fixtures used a larger default page than `limit=5` on `/events`.
- `/h2h` HTTP 200 with populated `teamDuel`={'homeWins': 6, 'awayWins': 4, 'draws': 0} and managerDuel=None.
- Team rankings: HTTP 404 (EXPECTED).
- Finished-event `/best-players`: HTTP 200 (PASS).
- Standings: total HTTP 200 (tables=1 rows=96); home tables=1 rows=0.
- **Featured-event is a finished game** (id=92441270, status=finished).
- Lineup jersey numbers: filled=39 null=0 (no null shirts on the finished sample).
- Error `message` on non-numeric event id is a **str** (error='Bad Request'); details type=NoneType.
- Auth on `/events?limit=1`: both headers: HTTP 200 json=True; X-Live-Key only: HTTP 200 json=True; x-apim-key only: HTTP 403 json=True; no API keys: HTTP 403 json=False. Live key alone is enough; `x-apim-key` alone and no keys return **403** (JSON vs HTML respectively). Key values not recorded.
- football-style player season stats (on-catalog for hockey): HTTP 200 (PASS).
- off-catalog player/{id}/statistics: HTTP 404 (EXPECTED).
- off-catalog team season statistics: HTTP 200 (PASS).
- Player profile `team` is None and `country` is None (preferred fields null on the player resource).
- Team profile `country` is populated: {'name': 'Canada', 'alpha2': 'CA', 'alpha3': 'CAN'}.

### Leftover pagination totals

- events page 2000: empty 200 on page 2000 but total=33 still set.
- events page 9999: empty 200 on page 9999 but total=33 still set.
- events page 8 beyond totalPages: empty 200 on page 8 but total=33 still set.
- players page 9999: empty 200 on page 9999 but total=15177 still set.
- players page 3037 beyond totalPages: empty 200 on page 3037 but total=15177 still set.
- teams page 2000: empty 200 on page 2000 but total=532 still set.
- teams page 9999: empty 200 on page 9999 but total=532 still set.
- teams page 108 beyond totalPages: empty 200 on page 108 but total=532 still set.
- team events last page 2000: empty 200 on page 2000 but total=1106 still set.
- team events last page 9999: empty 200 on page 9999 but total=1106 still set.
- team events last page 223 beyond totalPages: empty 200 on page 223 but total=1106 still set.
- ut events page 9999: empty 200 on page 9999 but total=16141 still set.
- ut events page 3230 beyond totalPages: empty 200 on page 3230 but total=16141 still set.
- incidents (short list) page 2000: empty 200 on page 2000 but total=26 still set.
- incidents (short list) page 9999: empty 200 on page 9999 but total=26 still set.
- incidents (short list) page 7 beyond totalPages: empty 200 on page 7 but total=26 still set.

## Regenerate

```bash
python3 scripts/probe_variations.py
python3 scripts/generate_variation_report.py
```
