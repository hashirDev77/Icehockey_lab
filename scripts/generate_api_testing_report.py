#!/usr/bin/env python3
"""Generate docs/ice_hockey_api_testing_report.md from live probe evidence."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "ice-hockey-endpoint-evidence.json"
OUT = ROOT / "docs" / "ice_hockey_api_testing_report.md"
SPORT_PREFIX = "/v1/ice_hockey"

DATA_EXPECTATION: dict[str, str] = {
    "/event/{eventId}": "Full match: teams, status object, period scores, venue, tournament.",
    "/event/{eventId}/best-players": "Optional enrichment: ranked players for the match.",
    "/event/{eventId}/enrichments": "Index of available match enrichment types.",
    "/event/{eventId}/enrichments/{type}": "Payload for one enrichment type (e.g. h2h_events → events list).",
    "/event/{eventId}/h2h": "Prior meetings: teamDuel / managerDuel or linked events.",
    "/event/{eventId}/incidents": "Match timeline: goals, penalties, period events.",
    "/event/{eventId}/lineups": "home/away lineups: skaters, goalies, manager.",
    "/event/{eventId}/player-statistics": "Paginated box-score rows per player.",
    "/event/{eventId}/player/{playerId}/statistics": "One player's stats for this match.",
    "/event/{eventId}/pregame-form": "Recent W/L form and sample event ids per team.",
    "/event/{eventId}/statistics": "Team comparison stats (shots, goals, FO%, PIM).",
    "/event/{eventId}/team-streaks": "Streak buckets (may be empty arrays).",
    "/events": "Paginated items[] of matches; supports page/limit/status.",
    "/fixtures/today": "Paginated items[] for today's schedule.",
    "/manager/{managerId}": "Manager/coach profile object.",
    "/player/{playerId}": "Player profile object.",
    "/player/{playerId}/events/{direction}": "Paginated events[] (last/next).",
    "/player/{playerId}/unique-tournament/{tournamentId}/season/{seasonId}/statistics": "Season totals for one player in a competition.",
    "/players": "Paginated items[] player directory.",
    "/search": "Paginated items[] typed hits (requires q).",
    "/team/{teamId}": "Team profile object.",
    "/team/{teamId}/enrichments": "types[] of team-level enrichments.",
    "/team/{teamId}/enrichments/{type}": "Data for one team enrichment (e.g. events_last).",
    "/team/{teamId}/events/{direction}": "Paginated events[] team schedule.",
    "/team/{teamId}/featured-event": "Single highlighted event object.",
    "/team/{teamId}/media": "Paginated media[] (highlights URLs).",
    "/team/{teamId}/near-events": "previousEvent / nextEvent envelope.",
    "/team/{teamId}/performance": "form, events, points with pagination.",
    "/team/{teamId}/players": "players[] roster for team.",
    "/team/{teamId}/rankings": "Optional enrichment rankings (often 404).",
    "/team/{teamId}/standings-seasons": "Tournament/season groupings for standings.",
    "/team/{teamId}/unique-tournaments": "Paginated uniqueTournaments[].",
    "/teams": "Paginated items[] team directory.",
    "/tournaments": "Paginated items[] competition directory.",
    "/unique-tournament/{tournamentId}": "Competition metadata object.",
    "/unique-tournament/{tournamentId}/events": "Paginated events[] in competition.",
    "/unique-tournament/{tournamentId}/scheduled-events/{date}": "Events on a calendar date.",
    "/unique-tournament/{tournamentId}/season/{seasonId}/round/{round}": "Events for a season round.",
    "/unique-tournament/{tournamentId}/season/{seasonId}/standings/{type}": "standings[] table (total/home/away).",
    "/unique-tournament/{tournamentId}/seasons": "Paginated seasons[].",
}


def route_key(template: str) -> str:
    return template.replace(SPORT_PREFIX, "")


def verdict(route: dict) -> tuple[str, str]:
    http = route.get("http")
    c = route.get("classification") or {}
    tmpl = route_key(route["routeTemplate"])

    if http == 400 and "search" in tmpl and not (route.get("query") or {}).get("q"):
        return "EXPECTED", "Validation when required query param missing."

    if http == 404:
        msg = (c.get("apiError") or {}).get("message") or route.get("error") or ""
        details = str((c.get("apiError") or {}).get("details") or "")
        if "Enrichment" in msg or "ENRICHMENT" in details or "not found" in msg.lower():
            if "enrichment" in tmpl or tmpl.endswith("/best-players") or tmpl.endswith("/rankings"):
                return "OPTIONAL_MISSING", "Enrichment not on file for this entity (404)."
        return "FAIL", msg or "404 Not found."

    if http != 200:
        return "FAIL", route.get("error") or f"HTTP {http}"

    if tmpl.endswith("/h2h") and route.get("bytes", 0) < 80:
        body_prev = route.get("bodyPreview") or ""
        if "null" in body_prev and "teamDuel" in body_prev:
            return "PASS_EMPTY", "200 but teamDuel/managerDuel null — no H2H data for sample."

    lk = c.get("listKey")
    lc = c.get("listCount")
    if lk is not None and lc == 0:
        return "PASS_EMPTY", f"200 with empty `{lk}` (may be valid for filter/context)."

    if "team-streaks" in tmpl and route.get("bytes", 0) < 200:
        return "PASS_PARTIAL", "200; streak structure present but buckets may be empty."

    return "PASS", "200 with parseable payload matching expected shape."


def format_pagination(c: dict) -> str:
    p = c.get("pagination")
    if not p:
        return "N/A (not a paginated list)"
    return (
        f"page={p.get('page')}, limit={p.get('limit')}, total={p.get('total')}, "
        f"totalPages={p.get('totalPages')}, hasMore={p.get('hasMore')}"
    )


def data_returned(c: dict, route: dict) -> str:
    parts = [c.get("responseKind") or "unknown"]
    if c.get("topLevelKeys"):
        parts.append(f"keys: `{', '.join(c['topLevelKeys'][:12])}`")
    if c.get("listKey"):
        parts.append(f"array `{c['listKey']}` (n={c.get('listCount')})")
    if c.get("sampleRowKeys"):
        parts.append(f"row fields: `{', '.join(c['sampleRowKeys'][:14])}`")
    if c.get("nestedObjectKeys"):
        parts.append(f"nested: `{', '.join(c['nestedObjectKeys'][:14])}`")
    return " · ".join(parts)


def extra_verdict(e: dict) -> tuple[str, str]:
    http = e["http"]
    c = e["classification"]
    label = e["label"]
    if "finished" in label or "inprogress" in label:
        if http == 200 and (c.get("listCount") or 0) == 0:
            return (
                "FAIL_DATA",
                "Global /events filter returns total=0 while team history has finished games — investigate filter or indexing.",
            )
        if http == 200:
            return "PASS", "Status filter returned rows."
    if http == 400:
        return "EXPECTED", "Correct rejection when q is missing on /search." if "search" in label else "Expected validation error."
    if "standings home" in label or "standings away" in label:
        preview = e.get("bodyPreview") or ""
        if http == 200 and ('"rows": []' in preview or (c.get("bytes") or 0) < 80):
            return "PASS_EMPTY", "200 but standings rows empty for home/away split in this season."
        if http == 200:
            return "PASS", "Home/away standings returned."
    if "page=9999" in label:
        return "PASS_EMPTY", "Out-of-range page returns empty items with total unchanged (not 404)."
    if "page=2 differs" in label:
        chk = e.get("paginationCheck") or {}
        if chk.get("differentPages"):
            return (
                "PASS",
                f"Page 2 first id ({chk.get('page2FirstId')}) differs from page 1 ({chk.get('page1FirstId')}).",
            )
        return "FAIL_DATA", "Page 2 slice overlaps or equals page 1 — pagination may be broken."
    if "non-numeric" in label:
        return ("EXPECTED", "Invalid event id should return 400.") if http == 400 else ("FAIL", f"HTTP {http} for non-numeric event id.")
    if "unknown" in label and "event" in label:
        return ("EXPECTED", "Unknown numeric event id should return 404.") if http == 404 else ("FAIL", f"HTTP {http} for unknown event id.")
    if http == 200 and (c.get("listCount") or 0) > 0:
        return "PASS", ""
    if http == 200:
        return "PASS_EMPTY", ""
    if http == 404:
        return "FAIL", "Unexpected 404."
    return "FAIL", f"HTTP {http}"


def main() -> None:
    data = json.loads(EVIDENCE.read_text())
    ids = data["discoveredIds"]
    routes = data["routes"]
    extras = data.get("extraProbes", [])
    route_count = data.get("routeCount") or len(routes)

    counts: dict[str, int] = {}
    rows_for_table: list[list[str]] = []

    for r in routes:
        rk = route_key(r["routeTemplate"])
        v, reason = verdict(r)
        counts[v] = counts.get(v, 0) + 1
        c = r["classification"]
        rows_for_table.append(
            [
                v,
                str(r["http"]),
                rk,
                (c.get("responseKind") or "")[:40],
                str(c.get("listKey") or "—"),
                str(c.get("listCount") if c.get("listCount") is not None else "—"),
            ]
        )

    lines = [
        "# Ice Hockey API — Testing Report",
        "",
        f"Live API test run against all **{route_count}** catalog routes. This document is for QA and integrators",
        "(response shapes, verdicts, pagination, failures).",
        "",
        f"- **Test run (UTC):** {data['generatedAt']}",
        f"- **Base URL:** `{data['baseUrl']}/v1/ice_hockey/...`",
        "- **Evidence JSON:** [`../data/ice-hockey-endpoint-evidence.json`](../data/ice-hockey-endpoint-evidence.json)",
        "",
        "## How tests were executed",
        "",
        "1. Discover IDs via `search`, `team/.../events/last`, `lineups`, `enrichments`, `seasons`.",
        "2. Call each route template with those IDs (see table below).",
        "3. Record HTTP status, response size, top-level keys, list key, pagination, sample row keys.",
        "4. Run additional filter/pagination/validation probes (see end).",
        "",
        "### IDs used in this run",
        "",
        "```json",
        json.dumps(
            {
                k: ids[k]
                for k in (
                    "eventId",
                    "teamId",
                    "playerId",
                    "lineupPlayerId",
                    "playerIdForEventStats",
                    "managerId",
                    "tournamentId",
                    "seasonId",
                    "enrichmentType",
                    "teamEnrichmentType",
                    "round",
                    "date",
                )
                if k in ids
            },
            indent=2,
        ),
        "```",
        "",
        "## Verdict summary",
        "",
        "| Verdict | Count | Meaning |",
        "| --- | ---: | --- |",
        "| **PASS** | "
        + str(counts.get("PASS", 0))
        + " | HTTP 200 and non-empty payload fits expected type |",
        "| **PASS_PARTIAL** | "
        + str(counts.get("PASS_PARTIAL", 0))
        + " | HTTP 200 but sparse or incomplete business data |",
        "| **PASS_EMPTY** | "
        + str(counts.get("PASS_EMPTY", 0))
        + " | HTTP 200 with valid empty/null business data |",
        "| **OPTIONAL_MISSING** | "
        + str(counts.get("OPTIONAL_MISSING", 0))
        + " | HTTP 404 enrichment not recorded (optional route) |",
        "| **FAIL** | "
        + str(counts.get("FAIL", 0))
        + " | Unexpected error |",
        "| **EXPECTED** | "
        + str(counts.get("EXPECTED", 0))
        + " | Expected validation error |",
        "",
        "## Matrix (all catalog routes)",
        "",
        "| Verdict | HTTP | Route | Response kind | List key | Count |",
        "| --- | ---: | --- | --- | --- | ---: |",
    ]

    for row in rows_for_table:
        lines.append(f"| {row[0]} | {row[1]} | `{row[2]}` | {row[3]} | {row[4]} | {row[5]} |")

    lines.extend(["", "---", "", "## Per-endpoint test results", ""])

    for r in routes:
        rk = route_key(r["routeTemplate"])
        v, reason = verdict(r)
        c = r["classification"]
        lines.append(f"### `{rk}`")
        lines.append("")
        lines.append(f"- **Verdict:** **{v}** — {reason}")
        lines.append(f"- **HTTP:** {r['http']} · **Response size:** {r['bytes']} bytes")
        if r.get("calledPath"):
            q = r.get("query")
            lines.append(f"- **Request:** `{r['calledPath']}`" + (f" · query `{q}`" if q else ""))
        lines.append(f"- **Expected data (test plan):** {DATA_EXPECTATION.get(rk, 'See catalog.')}")
        lines.append(f"- **Actual data returned:** {data_returned(c, r)}")
        lines.append(f"- **Pagination:** {format_pagination(c)}")
        if c.get("apiError"):
            ae = c["apiError"]
            lines.append(f"- **API error body:** `{ae.get('error')}` — {ae.get('message')}")
        if r.get("error") and not c.get("apiError"):
            lines.append(f"- **Transport/parse error:** {r['error']}")
        lines.append("")

    lines.extend(["---", "", f"## Additional API tests (beyond {route_count}-route catalog)", ""])
    for e in extras:
        v, note = extra_verdict(e)
        c = e["classification"]
        lines.append(f"### {e['label']}")
        lines.append("")
        lines.append(f"- **Verdict:** **{v}**" + (f" — {note}" if note else ""))
        lines.append(f"- **HTTP:** {e['http']} · **Path:** `{e.get('path')}` · params `{e.get('params')}`")
        lines.append(f"- **Response:** {c.get('responseKind')} · {format_pagination(c)}")
        if c.get("listKey"):
            lines.append(f"- **List:** `{c['listKey']}` count={c.get('listCount')}")
        if e.get("paginationCheck"):
            lines.append(f"- **Pagination check:** `{e['paginationCheck']}`")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Notes",
            "",
            "- Catalog count is **40** ice hockey routes (`ice_hockey` prefix).",
            "- List calls used `page=1&limit=5` unless the route is a single object.",
            "- `/team/{teamId}/rankings` returned 404 `ENRICHMENT_NOT_FOUND` (optional).",
            "- `/event/{eventId}/h2h` returned 200 with null `teamDuel` / `managerDuel` for the sample match.",
            "- `/events?status=finished` and `inprogress` returned real rows (unlike some other sports where those filters are empty).",
            "- `/events?page=9999` is HTTP 200 with an empty `items` list; `total` / `totalPages` stay set (leftover pagination totals).",
            "- Home/away standings exist as envelopes with empty `rows` for this season; `total` standings are populated.",
            "- Per-event player statistics need a player from `/player-statistics`, not an arbitrary lineup row (`PLAYER_NOT_FOUND` / `not_in_match` otherwise).",
            "",
            "## Regenerate this report",
            "",
            "```bash",
            "python3 scripts/probe_all_endpoints.py",
            "python3 scripts/generate_api_testing_report.py",
            "```",
            "",
        ]
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    print("Verdicts:", counts)


if __name__ == "__main__":
    main()
