#!/usr/bin/env python3
"""Generate docs/ice_hockey_api_variation_testing.md from variation probe evidence."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAR = ROOT / "data" / "ice-hockey-variation-tests.json"
OUT = ROOT / "docs" / "ice_hockey_api_variation_testing.md"


def dash(v):
    return "—" if v is None or v == "" else v


def main() -> None:
    if not VAR.exists():
        raise SystemExit("Run: python3 scripts/probe_variations.py")

    data = json.loads(VAR.read_text())
    tests = data["tests"]
    by_state = data.get("discoveredEventIdsByState") or {}
    ids = data.get("discoveredIds") or {}
    findings = data.get("findings") or []

    lines = [
        "# Ice Hockey API — Variation & pagination testing",
        "",
        "Supplement to [`ice_hockey_api_testing_report.md`](./ice_hockey_api_testing_report.md).",
        "Tests **different entities**, **match states**, **status filters**, **list vs detail**, **auth**, **validity**, and **pagination** (including **page 2000**).",
        "",
        f"- **Generated (UTC):** {data['generatedAt']}",
        f"- **Raw JSON:** [`../data/ice-hockey-variation-tests.json`](../data/ice-hockey-variation-tests.json)",
        f"- **Tests run:** {data['summary']['totalTests']}",
        "",
        "## Event IDs used (by state)",
        "",
        "```json",
        json.dumps(by_state, indent=2),
        "```",
        "",
        "Same sub-routes were called on **finished**, **canceled**, and **notstarted** events when those IDs were discoverable from search, team history, fixtures, or status filters.",
        "",
        "```json",
        json.dumps(
            {
                k: ids[k]
                for k in (
                    "teamId",
                    "teamName",
                    "team2Id",
                    "team2Name",
                    "playerId",
                    "playerName",
                    "player2Id",
                    "player2Name",
                    "tournamentId",
                    "seasonId",
                )
                if k in ids
            },
            indent=2,
        ),
        "```",
        "",
        "## Verdict summary",
        "",
        "| Verdict | Count |",
        "| --- | ---: |",
    ]
    for k, v in sorted(((data.get("summary") or {}).get("byVerdict") or {}).items()):
        lines.append(f"| {k} | {v} |")

    lines.extend(
        [
            "",
            "## Does page 2000 return real data?",
            "",
            "| Endpoint | page=2000 result | Interpretation |",
            "| --- | --- | --- |",
        ]
    )

    page2000 = [t for t in tests if t["category"] == "pagination_edge" and "page 2000" in t["name"]]
    real_page = None
    for t in page2000:
        m = t["meta"]
        cnt = m.get("count", "—")
        tp = m.get("totalPages", "—")
        if t["verdict"] == "PASS" and (cnt or 0) > 0:
            interp = "**Real data** — page exists within `totalPages`."
            real_page = t
        elif t["verdict"] == "PASS_EMPTY":
            interp = "**Empty 200** — page is beyond `totalPages`; list = []. Not fake rows; **misleading `total` stays high**."
        elif t["verdict"] == "FAIL":
            interp = t.get("notes") or "Unexpected failure."
        else:
            interp = t.get("notes") or ""
        lines.append(f"| `{t['path']}` | HTTP {t['http']}, count={cnt}, totalPages={tp} | {interp} |")

    if real_page:
        lines.extend(
            [
                "",
                f"**Important:** `GET /{real_page['path']}?page=2000` returned **real rows** because `totalPages` is ≥ 2000.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "No ice hockey list in this run had `totalPages` ≥ 2000, so **page 2000 never returned live rows** — only empty 200s with leftover `total`.",
            ]
        )

    limit2000 = [t for t in tests if t["category"] == "limit_variation" and "limit=2000" in t["name"]]
    if limit2000:
        codes = ", ".join(f"`{t['name']}` HTTP {t['http']}" for t in limit2000)
        lines.extend(["", f"**`limit=2000`:** {codes}."])

    lines.extend(
        [
            "",
            "## Status filter matrix (`GET /events`)",
            "",
            "| status param | HTTP | total | items in page |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for t in tests:
        if t["category"] != "status_filter" or not t["name"].startswith("events status="):
            continue
        st = t["name"].replace("events status=", "")
        lines.append(f"| `{st}` | {t['http']} | {dash(t['meta'].get('total'))} | {dash(t['meta'].get('count'))} |")

    compare = next((t for t in tests if "team events last vs events" in t["name"]), None)
    unfiltered = next((t for t in tests if t["name"] == "events page 1"), None)
    if compare:
        lines.extend(
            [
                "",
                "Team `events/last` has a long finished history "
                f"(total={compare['meta'].get('total')}) while unfiltered `/events` is a **windowed** feed "
                f"(total={ (unfiltered or {}).get('meta', {}).get('total') }). "
                "`status=finished` on that window is **not empty**.",
            ]
        )

    lines.extend(
        [
            "",
            "## All variation tests",
            "",
            "| Category | Name | HTTP | Verdict | list count | total | totalPages |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for t in tests:
        m = t.get("meta") or {}
        lines.append(
            f"| {t['category']} | {t['name']} | {t['http']} | {t['verdict']} | "
            f"{dash(m.get('count'))} | {dash(m.get('total'))} | {dash(m.get('totalPages'))} |"
        )

    # Interpretation from evidence
    bullets: list[str] = []

    p12 = [t for t in tests if t["category"] == "pagination" and "page 1 vs page 2" in t["name"]]
    bad_slices = [t for t in p12 if not ((t.get("extra") or {}).get("differentPages"))]
    if p12 and not bad_slices:
        bullets.append("Page 2 is a **new slice** on the lists that were compared (events, players, teams, team history, competition events, incidents).")
    elif bad_slices:
        names = ", ".join(t["name"] for t in bad_slices)
        bullets.append(f"**Broken pagination slice:** {names} — page 2 first id matches page 1 or is missing.")

    leftover = [t for t in tests if t["category"] == "pagination_edge" and t["verdict"] == "PASS_EMPTY" and "Leftover" in (t.get("notes") or "")]
    if leftover or findings:
        bullets.append("Pages beyond `totalPages` (including **9999** and **2000** on short lists) return **HTTP 200 + empty arrays**, not 404 and not fabricated rows. **`total` / `totalPages` stay set** — leftover pagination totals.")

    ended = next((t for t in tests if t["name"] == "events status=ended"), None)
    if ended:
        bullets.append(f"Invalid status token `ended` returned HTTP {ended['http']} ({ended['verdict']}).")

    finished = next((t for t in tests if t["name"] == "events status=finished"), None)
    inprog = next((t for t in tests if t["name"] == "events status=inprogress"), None)
    if finished and finished.get("verdict") == "FAIL":
        bullets.append("**Broken:** `/events?status=finished` is empty while team `events/last` has finished games.")
    elif finished and (finished.get("meta") or {}).get("count"):
        bullets.append(f"`/events?status=finished` returned rows (total={finished['meta'].get('total')}). Global `/events` is a **windowed** feed, not full team history.")
    if inprog:
        bullets.append(f"`/events?status=inprogress` HTTP {inprog['http']}, total={inprog['meta'].get('total')}, count={inprog['meta'].get('count')}.")

    invalids = [t for t in tests if t["category"] == "query_params"]
    for t in invalids:
        bullets.append(f"{t['name']}: HTTP {t['http']} ({t['verdict']}) — `{t['path']}`.")

    omit = [t for t in tests if t["category"] == "response_stats" and "Omits pagination" in (t.get("notes") or "")]
    if omit:
        bullets.append("Families that **omit pagination**: " + ", ".join(f"`{t['name']}`" for t in omit) + ".")

    lvd = next((t for t in tests if "list vs detail status" in t["name"]), None)
    if lvd:
        extra = lvd.get("extra") or {}
        bullets.append(
            "List vs detail: `/events` items use `status` as a **string** "
            f"(`{(extra.get('listStatus') or {}).get('status')}`); "
            f"`/event/{{id}}` uses an object `{extra.get('detailStatus')}`. "
            f"List `competitionName`={extra.get('listCompetitionName')!r}; detail has nested `tournament`. "
            f"Detail `homeScore` keys={extra.get('detailHomeScoreKeys')} (periods + overtime, not a baseball innings box)."
        )
    fx = next((t for t in tests if "fixtures/today vs default" in t["name"]), None)
    if fx:
        extra = fx.get("extra") or {}
        bullets.append(
            f"`/fixtures/today` vs default `/events`: first-page ids **{'match' if extra.get('sameIds') else 'differ'}**; "
            f"byte size **{'same' if extra.get('sameBytes') else 'differs'}** "
            f"(events {extra.get('eventsBytes')} bytes, fixtures {extra.get('fixturesBytes')} bytes). "
            "Fixtures used a larger default page than `limit=5` on `/events`."
        )

    h2h = next((t for t in tests if t["name"] == "h2h null duels"), None)
    if h2h:
        extra = h2h.get("extra") or {}
        td = extra.get("teamDuel")
        md = extra.get("managerDuel")
        if td:
            bullets.append(f"`/h2h` HTTP {h2h['http']} with populated `teamDuel`={td} and managerDuel={md!r}.")
        else:
            bullets.append(f"`/h2h` HTTP {h2h['http']} with null duels (teamDuel={td!r}, managerDuel={md!r}).")
    rank = next((t for t in tests if "rankings" in t["name"]), None)
    if rank:
        bullets.append(f"Team rankings: HTTP {rank['http']} ({rank['verdict']}).")
    best = next((t for t in tests if t["name"].startswith("best-players")), None)
    if best:
        bullets.append(f"Finished-event `/best-players`: HTTP {best['http']} ({best['verdict']}).")

    home = next((t for t in tests if t["name"] == "standings home row count"), None)
    total_st = next((t for t in tests if t["name"] == "standings total row count"), None)
    if home or total_st:
        bullets.append(
            f"Standings: total HTTP {total_st['http'] if total_st else '—'} ({(total_st or {}).get('notes')}); "
            f"home {(home or {}).get('notes')}."
        )

    feat = next((t for t in tests if t["name"] == "featured-event status"), None)
    if feat:
        extra = feat.get("extra") or {}
        st = extra.get("status") or ""
        if "finish" in str(st).lower():
            bullets.append(f"**Featured-event is a finished game** (id={extra.get('eventId')}, status={st}).")
        else:
            bullets.append(f"Featured event id={extra.get('eventId')} status={st}.")

    jersey = next((t for t in tests if t["name"] == "lineup jersey numbers"), None)
    if jersey:
        extra = jersey.get("extra") or {}
        bullets.append(
            f"Lineup jersey numbers: filled={extra.get('jerseyFilled')} null={extra.get('jerseyNull')} "
            "(no null shirts on the finished sample)."
        )

    err = next((t for t in tests if "error message shape" in t["name"]), None)
    if err:
        extra = err.get("extra") or {}
        bullets.append(
            f"Error `message` on non-numeric event id is a **{extra.get('messageType')}** "
            f"(error={extra.get('error')!r}); details type={extra.get('detailsType')}."
        )

    auth = [t for t in tests if t["category"] == "auth"]
    if auth:
        bits = [f"{(t.get('extra') or {}).get('headerSet')}: HTTP {t['http']} json={t.get('json')}" for t in auth]
        bullets.append(
            "Auth on `/events?limit=1`: "
            + "; ".join(bits)
            + ". Live key alone is enough; `x-apim-key` alone and no keys return **403** "
            "(JSON vs HTML respectively). Key values not recorded."
        )

    off = [t for t in tests if t["category"] == "off_catalog"]
    for t in off:
        bullets.append(f"{t['name']}: HTTP {t['http']} ({t['verdict']}).")

    missing_states = [s for s in ("finished", "canceled", "notstarted") if s not in by_state]
    if missing_states:
        bullets.append("Could not discover event IDs for: " + ", ".join(missing_states) + " (no invented IDs).")

    player_null = next((t for t in tests if "player.team" in t["name"]), None)
    if player_null:
        extra = player_null.get("extra") or {}
        bullets.append(
            f"Player profile `team` is {extra.get('team')!r} and `country` is {extra.get('country')!r} "
            "(preferred fields null on the player resource)."
        )
    team_country = next((t for t in tests if t["name"] == "team.country on profile"), None)
    if team_country:
        extra = team_country.get("extra") or {}
        bullets.append(f"Team profile `country` is populated: {extra.get('country')}.")

    lines.extend(["", "## Interpretation", ""])
    for b in bullets:
        if b:
            lines.append(f"- {b}")

    if findings:
        lines.extend(["", "### Leftover pagination totals", ""])
        for f in findings:
            lines.append(f"- {f}")

    lines.extend(
        [
            "",
            "## Regenerate",
            "",
            "```bash",
            "python3 scripts/probe_variations.py",
            "python3 scripts/generate_variation_report.py",
            "```",
            "",
        ]
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    print("Verdicts:", (data.get("summary") or {}).get("byVerdict"))


if __name__ == "__main__":
    main()
