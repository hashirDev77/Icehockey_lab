#!/usr/bin/env python3
"""Ice hockey API-level quality tests: pagination, filters, list vs detail, auth, validity."""
from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
EVIDENCE = ROOT / "data" / "ice-hockey-endpoint-evidence.json"
OUT = ROOT / "data" / "ice-hockey-variation-tests.json"
SPORT = "ice_hockey"


def load_env() -> tuple[str, dict[str, str], dict[str, str]]:
    env: dict[str, str] = {}
    path = ENV_PATH if ENV_PATH.exists() else Path("/Users/apple/Desktop/Baseball_Product/.env")
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    base = (env.get("MSDATA_BASE_URL") or env.get("VITE_MSDATA_BASE_URL") or "https://sports-api.sportsdata365.com/msdata").rstrip("/")
    apim = env.get("MSDATA_API_KEY") or env.get("VITE_MSDATA_API_KEY") or ""
    live = env.get("MSDATA_LIVE_KEY") or env.get("VITE_MSDATA_LIVE_KEY") or ""
    headers = {"accept": "application/json", "x-apim-key": apim, "X-Live-Key": live}
    keys = {"apim": apim, "live": live}
    return base, headers, keys


def _curl_get(url: str, headers: dict[str, str]) -> dict:
    cmd = ["/usr/bin/curl", "-sS", "-w", "\n%{http_code}\n%{content_type}", "--max-time", "60"]
    for k, v in headers.items():
        cmd.extend(["-H", f"{k}: {v}"])
    cmd.append(url)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return {
            "http": 0,
            "url": url,
            "body": None,
            "bytes": 0,
            "error": (proc.stderr or "").strip() or f"curl exit {proc.returncode}",
            "json": False,
            "contentType": None,
        }
    text = proc.stdout
    parts = text.rsplit("\n", 2)
    if len(parts) == 3:
        body_text, code_text, content_type = parts
    else:
        body_text, code_text, content_type = text, "0", ""
    try:
        http = int(code_text.strip())
    except Exception:
        http = 0
    json_ok = False
    body = None
    if body_text:
        try:
            body = json.loads(body_text)
            json_ok = True
        except Exception:
            body = {"raw": body_text[:400]}
    return {
        "http": http,
        "url": url,
        "body": body,
        "bytes": len(body_text.encode("utf-8")),
        "contentType": content_type.strip() or None,
        "json": json_ok,
        "error": (body or {}).get("message") if isinstance(body, dict) and http >= 400 else None,
    }


def get(base: str, headers: dict[str, str], path: str, params: dict | None = None) -> dict:
    url = f"{base.rstrip('/')}/v1/{SPORT}/{path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            body = json.loads(raw) if raw else None
            return {
                "http": resp.status,
                "url": url,
                "body": body,
                "bytes": len(raw),
                "contentType": resp.headers.get("Content-Type"),
                "json": True,
            }
    except urllib.error.HTTPError as e:
        raw = e.read() or b""
        json_ok = False
        try:
            body = json.loads(raw) if raw else None
            json_ok = True
        except Exception:
            body = {"raw": raw[:400].decode("utf-8", "replace")}
        return {
            "http": e.code,
            "url": url,
            "body": body,
            "bytes": len(raw),
            "contentType": e.headers.get("Content-Type") if e.headers else None,
            "json": json_ok,
        }
    except Exception as e:
        err = str(e)
        if "CERTIFICATE_VERIFY_FAILED" in err or "SSL" in err:
            curled = _curl_get(url, headers)
            return curled
        return {"http": 0, "url": url, "body": None, "bytes": 0, "error": err, "json": False}


def list_meta(body: dict | None) -> dict:
    if not isinstance(body, dict):
        return {}
    keys = (
        "items",
        "events",
        "players",
        "incidents",
        "playerStatistics",
        "leaderboard",
        "seasons",
        "media",
        "standings",
        "uniqueTournaments",
        "types",
        "statistics",
    )
    out: dict = {}
    for key in keys:
        if isinstance(body.get(key), list):
            lst = body[key]
            first_id = None
            if lst and isinstance(lst[0], dict):
                first_id = lst[0].get("id")
                if first_id is None and isinstance(lst[0].get("player"), dict):
                    first_id = lst[0]["player"].get("id")
            out = {
                "listKey": key,
                "count": len(lst),
                "firstId": first_id,
                "page": body.get("page"),
                "limit": body.get("limit"),
                "total": body.get("total"),
                "totalPages": body.get("totalPages"),
                "hasMore": body.get("hasMore"),
                "lengthVsLimit": None,
            }
            if body.get("limit") is not None:
                out["lengthVsLimit"] = f"{len(lst)} vs limit {body.get('limit')}"
            break
    if not out:
        out = {"topKeys": list(body.keys())[:15]}
        if body.get("error"):
            out["error"] = body.get("error")
            out["messageType"] = type(body.get("message")).__name__
    return out


def status_type(ev: dict | None) -> str:
    if not isinstance(ev, dict):
        return ""
    st = ev.get("status")
    if isinstance(st, dict):
        return str(st.get("type") or st.get("description") or "")
    if ev.get("statusType"):
        return str(ev.get("statusType"))
    return str(st or "")


def first_id(items) -> int | None:
    for it in items or []:
        if isinstance(it, dict) and it.get("id") is not None:
            try:
                return int(it["id"])
            except Exception:
                return None
    return None


def search_id(base, headers, q: str, wanted: str) -> tuple[int | None, str]:
    r = get(base, headers, "search", {"q": q, "page": 1, "limit": 10})
    items = ((r.get("body") or {}) if isinstance(r.get("body"), dict) else {}).get("items") or []
    for item in items:
        if not isinstance(item, dict):
            continue
        itype = (item.get("type") or "").lower()
        if wanted in itype and item.get("id") is not None:
            return int(item["id"]), item.get("name") or q
    if items and isinstance(items[0], dict) and items[0].get("id") is not None:
        return int(items[0]["id"]), items[0].get("name") or q
    return None, q


def main() -> None:
    base, headers, keys = load_env()
    catalog_ids = {}
    if EVIDENCE.exists():
        catalog_ids = json.loads(EVIDENCE.read_text()).get("discoveredIds") or {}

    team_id = catalog_ids.get("teamId")
    player_id = catalog_ids.get("playerId")
    tournament_id = catalog_ids.get("tournamentId")
    season_id = catalog_ids.get("seasonId")
    finished_id = catalog_ids.get("eventId")
    stats_player = catalog_ids.get("playerIdForEventStats")

    tests: list[dict] = []
    findings: list[str] = []

    def record(category: str, name: str, path: str, params: dict | None, result: dict, notes: str = "", extra: dict | None = None, expect: str | None = None):
        body = result.get("body") if isinstance(result.get("body"), dict) else None
        meta = list_meta(body)
        http = result.get("http") or 0
        verdict = "PASS"
        count = meta.get("count")

        if expect == "auth_ok":
            verdict = "PASS" if http == 200 else "FAIL"
            notes = (notes + " " if notes else "") + f"json={result.get('json')}"
        elif expect == "auth_reject":
            verdict = "EXPECTED" if http in (401, 403) else ("FAIL" if http == 200 else "FAIL")
            notes = (notes + " " if notes else "") + f"json={result.get('json')} contentType={result.get('contentType')}"
        elif expect == "validation":
            verdict = "EXPECTED" if http in (400, 404) else "FAIL"
        elif expect == "not_found":
            verdict = "EXPECTED" if http == 404 else ("PASS" if http == 200 else "FAIL")
        elif expect == "optional_404":
            verdict = "EXPECTED" if http == 404 else ("PASS" if http == 200 else "FAIL")
        elif http >= 500 or http == 0:
            verdict = "FAIL"
        elif http >= 400:
            verdict = "FAIL"
        elif expect == "must_have_rows" and (count == 0 or count is None):
            verdict = "FAIL"
            notes = (notes + " " if notes else "") + "Unexpected empty — other endpoints show this data exists."
        elif expect == "page_slice" and extra:
            verdict = "PASS" if extra.get("differentPages") else "FAIL"
        elif count == 0 and meta.get("listKey"):
            page = meta.get("page")
            total_pages = meta.get("totalPages")
            if page and total_pages and page > total_pages:
                verdict = "PASS_EMPTY"
                notes = (notes + " " if notes else "") + "Empty page beyond totalPages (200 OK, not 404)."
                if meta.get("total"):
                    notes += " Leftover high total is a defect."
                    findings.append(f"{name}: empty 200 on page {page} but total={meta.get('total')} still set.")
            else:
                verdict = "PASS_EMPTY"
        elif extra and extra.get("force_verdict"):
            verdict = extra["force_verdict"]

        row = {
            "category": category,
            "name": name,
            "path": path,
            "params": params,
            "http": http,
            "bytes": result.get("bytes"),
            "meta": meta,
            "verdict": verdict,
            "notes": notes.strip(),
            "json": result.get("json"),
        }
        if extra:
            row["extra"] = extra
        tests.append(row)

    # --- Discover IDs (no invented entities) ---
    if not team_id:
        team_id, _ = search_id(base, headers, "Maple Leafs", "team")
    team_name = "Maple Leafs"
    team2_id, team2_name = search_id(base, headers, "Canadiens", "team")
    if not player_id:
        player_id, _ = search_id(base, headers, "Connor McDavid", "player")
    player_name = "McDavid"
    player2_id, player2_name = search_id(base, headers, "Sidney Crosby", "player")
    if not tournament_id:
        tournament_id, _ = search_id(base, headers, "NHL", "uniquetournament")

    by_type: dict[str, int] = {}
    if finished_id:
        by_type["finished"] = finished_id

    team_last = get(base, headers, f"team/{team_id}/events/last", {"page": 1, "limit": 30})
    team_last_events = ((team_last.get("body") or {}) if isinstance(team_last.get("body"), dict) else {}).get("events") or []
    team_last_finished = 0
    for ev in team_last_events:
        t = status_type(ev).lower()
        if "finish" in t:
            team_last_finished += 1
            by_type.setdefault("finished", ev["id"])
        if "cancel" in t:
            by_type.setdefault("canceled", ev["id"])
        if "notstart" in t:
            by_type.setdefault("notstarted", ev["id"])

    if team2_id and "canceled" not in by_type:
        last2 = get(base, headers, f"team/{team2_id}/events/last", {"page": 1, "limit": 30})
        for ev in ((last2.get("body") or {}) if isinstance(last2.get("body"), dict) else {}).get("events") or []:
            t = status_type(ev).lower()
            if "cancel" in t:
                by_type.setdefault("canceled", ev["id"])
                break

    team_next = get(base, headers, f"team/{team_id}/events/next", {"page": 1, "limit": 15})
    for ev in ((team_next.get("body") or {}) if isinstance(team_next.get("body"), dict) else {}).get("events") or []:
        t = status_type(ev).lower()
        if "notstart" in t:
            by_type.setdefault("notstarted", ev["id"])
            break

    for st in ("canceled", "notstarted", "finished"):
        if st in by_type:
            continue
        r = get(base, headers, "events", {"page": 1, "limit": 15, "status": st})
        items = ((r.get("body") or {}) if isinstance(r.get("body"), dict) else {}).get("items") or []
        eid = first_id(items)
        if eid:
            by_type[st] = eid

    fixtures = get(base, headers, "fixtures/today", {"page": 1, "limit": 20})
    fixture_items = ((fixtures.get("body") or {}) if isinstance(fixtures.get("body"), dict) else {}).get("items") or []
    for ev in fixture_items:
        st = str(ev.get("status") or "").lower()
        if "notstart" in st:
            by_type.setdefault("notstarted", ev["id"])
        if "progress" in st:
            by_type.setdefault("inprogress", ev["id"])
        if "finish" in st:
            by_type.setdefault("finished", ev["id"])

    if not season_id and tournament_id:
        seasons = get(base, headers, f"unique-tournament/{tournament_id}/seasons", {"page": 1, "limit": 5})
        sl = ((seasons.get("body") or {}) if isinstance(seasons.get("body"), dict) else {}).get("seasons") or []
        if sl:
            season_id = sl[0].get("id")

    if not stats_player and by_type.get("finished"):
        pst = get(base, headers, f"event/{by_type['finished']}/player-statistics", {"page": 1, "limit": 5})
        rows = ((pst.get("body") or {}) if isinstance(pst.get("body"), dict) else {}).get("playerStatistics") or []
        if rows and isinstance(rows[0].get("player"), dict):
            stats_player = rows[0]["player"].get("id")

    finished_id = by_type.get("finished")

    # --- Pagination: page 1 vs 2 ---
    for label, path, params_base in [
        ("events", "events", {"limit": 5}),
        ("players", "players", {"limit": 5}),
        ("teams", "teams", {"limit": 5}),
        ("team events last", f"team/{team_id}/events/last", {"limit": 5}),
        ("ut events", f"unique-tournament/{tournament_id}/events", {"limit": 5}),
        ("incidents", f"event/{finished_id}/incidents", {"limit": 5}),
    ]:
        p1 = get(base, headers, path, {**params_base, "page": 1})
        p2 = get(base, headers, path, {**params_base, "page": 2})
        id1 = list_meta(p1.get("body") if isinstance(p1.get("body"), dict) else None).get("firstId")
        id2 = list_meta(p2.get("body") if isinstance(p2.get("body"), dict) else None).get("firstId")
        different = bool(id1 and id2 and id1 != id2)
        record(
            "pagination",
            f"{label} page 1 vs page 2",
            path,
            {"page": "1 then 2", **params_base},
            p2,
            notes=f"page1FirstId={id1} page2FirstId={id2} different={different}",
            extra={"page1FirstId": id1, "page2FirstId": id2, "differentPages": different},
            expect="page_slice",
        )
        record("pagination", f"{label} page 1", path, {**params_base, "page": 1}, p1)

    # --- page 9999 and 2000 ---
    pagination_targets = [
        ("events", "events", {}),
        ("players", "players", {}),
        ("teams", "teams", {}),
        ("team events last", f"team/{team_id}/events/last", {}),
        ("ut events", f"unique-tournament/{tournament_id}/events", {}),
        ("incidents (short list)", f"event/{finished_id}/incidents", {}),
    ]
    # Probe page 1 first to learn totalPages for last-page / beyond cases
    totals: dict[str, dict] = {}
    for name, path, _ in pagination_targets:
        r0 = get(base, headers, path, {"page": 1, "limit": 5})
        totals[name] = list_meta(r0.get("body") if isinstance(r0.get("body"), dict) else None)

    for name, path, _ in pagination_targets:
        for page in (2000, 9999):
            r = get(base, headers, path, {"page": page, "limit": 5})
            record("pagination_edge", f"{name} page {page}", path, {"page": page, "limit": 5}, r)
        tp = totals[name].get("totalPages")
        if isinstance(tp, int) and tp > 0:
            r_last = get(base, headers, path, {"page": tp, "limit": 5})
            record("pagination_edge", f"{name} last page ({tp})", path, {"page": tp, "limit": 5}, r_last)
            r_beyond = get(base, headers, path, {"page": tp + 1, "limit": 5},)
            record("pagination_edge", f"{name} page {tp + 1} beyond totalPages", path, {"page": tp + 1, "limit": 5}, r_beyond)

    # --- limit extremes ---
    for name, path, params in [
        ("events limit=1", "events", {"page": 1, "limit": 1}),
        ("events limit=100", "events", {"page": 1, "limit": 100}),
        ("events limit=2000", "events", {"page": 1, "limit": 2000}),
        ("search limit=1", "search", {"q": "Maple Leafs", "page": 1, "limit": 1}),
        ("search limit=100", "search", {"q": "Maple Leafs", "page": 1, "limit": 100}),
        ("search limit=2000", "search", {"q": "Maple Leafs", "page": 1, "limit": 2000}),
    ]:
        r = get(base, headers, path, params)
        expect = "validation" if params.get("limit") == 2000 else None
        record("limit_variation", name, path, params, r, expect=expect)

    # --- status filters ---
    unfiltered = get(base, headers, "events", {"page": 1, "limit": 5})
    unfiltered_meta = list_meta(unfiltered.get("body") if isinstance(unfiltered.get("body"), dict) else None)
    status_rows = {}
    for st in ("finished", "inprogress", "notstarted", "canceled", "postponed", "ended"):
        r = get(base, headers, "events", {"page": 1, "limit": 5, "status": st})
        expect = "validation" if st == "ended" else None
        if st in ("finished", "inprogress") and team_last_finished > 0:
            meta = list_meta(r.get("body") if isinstance(r.get("body"), dict) else None)
            # Windowed /events may be small; FAIL only if this filter is empty while unfiltered feed has that status
            if st == "finished" and (meta.get("count") or 0) == 0 and team_last_finished > 0:
                expect = "must_have_rows"
        record("status_filter", f"events status={st}", "events", {"page": 1, "limit": 5, "status": st}, r, expect=expect)
        status_rows[st] = list_meta(r.get("body") if isinstance(r.get("body"), dict) else None)

    record(
        "status_filter",
        "team events last vs events?status=finished",
        f"team/{team_id}/events/last",
        {"page": 1, "limit": 30},
        team_last,
        notes=f"teamLastFinishedOnPage={team_last_finished} eventsFinishedTotal={status_rows.get('finished', {}).get('total')} unfilteredTotal={unfiltered_meta.get('total')}",
    )

    # --- invalid query params ---
    invalid_cases = [
        ("invalid standings type", f"unique-tournament/{tournament_id}/season/{season_id}/standings/nope", None, "validation"),
        ("invalid events direction", f"team/{team_id}/events/sideways", {"page": 1, "limit": 5}, "validation"),
        ("invalid calendar date", f"unique-tournament/{tournament_id}/scheduled-events/not-a-date", None, "validation"),
    ]
    for name, path, params, expect in invalid_cases:
        r = get(base, headers, path, params)
        record("query_params", name, path, params, r, expect=expect)

    # --- response stats on list families ---
    list_families = [
        ("events", "events", {"page": 1, "limit": 5}),
        ("players", "players", {"page": 1, "limit": 5}),
        ("teams", "teams", {"page": 1, "limit": 5}),
        ("tournaments", "tournaments", {"page": 1, "limit": 5}),
        ("search", "search", {"q": "Maple Leafs", "page": 1, "limit": 5}),
        ("team roster (no pagination expected)", f"team/{team_id}/players", None),
        ("standings total (no pagination expected)", f"unique-tournament/{tournament_id}/season/{season_id}/standings/total", None),
        ("incidents", f"event/{finished_id}/incidents", {"page": 1, "limit": 5}),
        ("player-statistics", f"event/{finished_id}/player-statistics", {"page": 1, "limit": 5}),
        ("team media", f"team/{team_id}/media", {"page": 1, "limit": 5}),
        ("team unique-tournaments", f"team/{team_id}/unique-tournaments", {"page": 1, "limit": 5}),
        ("ut seasons", f"unique-tournament/{tournament_id}/seasons", {"page": 1, "limit": 5}),
    ]
    for name, path, params in list_families:
        r = get(base, headers, path, params)
        meta = list_meta(r.get("body") if isinstance(r.get("body"), dict) else None)
        omit = "page" not in (r.get("body") or {}) if isinstance(r.get("body"), dict) else True
        record(
            "response_stats",
            name,
            path,
            params,
            r,
            notes=("Omits pagination keys." if omit else f"Pagination present; {meta.get('lengthVsLimit')}."),
        )

    # --- list vs detail ---
    events_list = get(base, headers, "events", {"page": 1, "limit": 5})
    list_items = ((events_list.get("body") or {}) if isinstance(events_list.get("body"), dict) else {}).get("items") or []
    list_event = list_items[0] if list_items else None
    detail_id = (list_event or {}).get("id") or finished_id
    detail = get(base, headers, f"event/{detail_id}")
    detail_ev = ((detail.get("body") or {}) if isinstance(detail.get("body"), dict) else {}).get("event") or {}

    list_status = None
    if isinstance(list_event, dict):
        list_status = {"status": list_event.get("status"), "statusType": type(list_event.get("status")).__name__}
    detail_status = detail_ev.get("status")
    list_score = {k: list_event.get(k) for k in ("homeScore", "awayScore") if isinstance(list_event, dict)}
    detail_home = detail_ev.get("homeScore") if isinstance(detail_ev.get("homeScore"), dict) else {}
    score_box_keys = list(detail_home.keys())[:20] if isinstance(detail_home, dict) else []

    fixtures_vs_events = {
        "eventsBytes": events_list.get("bytes"),
        "fixturesBytes": fixtures.get("bytes"),
        "eventsIds": [it.get("id") for it in list_items[:5] if isinstance(it, dict)],
        "fixturesIds": [it.get("id") for it in fixture_items[:5] if isinstance(it, dict)],
    }
    fixtures_vs_events["sameIds"] = fixtures_vs_events["eventsIds"] == fixtures_vs_events["fixturesIds"]
    fixtures_vs_events["sameBytes"] = fixtures_vs_events["eventsBytes"] == fixtures_vs_events["fixturesBytes"]

    record(
        "list_vs_detail",
        "same event list vs detail status/score/competition",
        f"event/{detail_id}",
        None,
        detail,
        notes=(
            f"list.status type={list_status}; detail.status={detail_status}; "
            f"list.competitionName={None if not list_event else list_event.get('competitionName')}; "
            f"detail.tournament={type(detail_ev.get('tournament')).__name__}; "
            f"detail.homeScore keys={score_box_keys}; list scores={list_score}"
        ),
        extra={
            "listStatus": list_status,
            "detailStatus": detail_status,
            "listCompetitionName": None if not list_event else list_event.get("competitionName"),
            "detailTournamentKeys": list((detail_ev.get("tournament") or {}).keys())[:12] if isinstance(detail_ev.get("tournament"), dict) else None,
            "detailHomeScoreKeys": score_box_keys,
            "listScores": list_score,
        },
    )
    record(
        "list_vs_detail",
        "fixtures/today vs default /events",
        "fixtures/today",
        {"page": 1, "limit": 5},
        fixtures,
        notes=f"sameIds={fixtures_vs_events['sameIds']} sameBytes={fixtures_vs_events['sameBytes']} eventsBytes={fixtures_vs_events['eventsBytes']} fixturesBytes={fixtures_vs_events['fixturesBytes']}",
        extra=fixtures_vs_events,
    )
    record("list_vs_detail", "events list sample", "events", {"page": 1, "limit": 5}, events_list)

    # --- data validity ---
    player = get(base, headers, f"player/{player_id}")
    team = get(base, headers, f"team/{team_id}")
    pobj = ((player.get("body") or {}) if isinstance(player.get("body"), dict) else {}).get("player") or {}
    tobj = ((team.get("body") or {}) if isinstance(team.get("body"), dict) else {}).get("team") or {}
    record(
        "data_validity",
        "player.team null vs nested copies",
        f"player/{player_id}",
        None,
        player,
        notes=f"player.team={pobj.get('team')!r} player.country={pobj.get('country')!r} keys={list(pobj.keys())[:18]}",
        extra={"team": pobj.get("team"), "country": pobj.get("country"), "teamId": pobj.get("teamId")},
    )
    record(
        "data_validity",
        "team.country on profile",
        f"team/{team_id}",
        None,
        team,
        notes=f"team.country={tobj.get('country')!r} national={tobj.get('national')}",
        extra={"country": tobj.get("country")},
    )

    h2h = get(base, headers, f"event/{finished_id}/h2h")
    h2h_body = h2h.get("body") if isinstance(h2h.get("body"), dict) else {}
    record(
        "data_validity",
        "h2h null duels",
        f"event/{finished_id}/h2h",
        None,
        h2h,
        notes=f"teamDuel={h2h_body.get('teamDuel')!r} managerDuel={h2h_body.get('managerDuel')!r}",
        extra={"teamDuel": h2h_body.get("teamDuel"), "managerDuel": h2h_body.get("managerDuel")},
    )
    best = get(base, headers, f"event/{finished_id}/best-players")
    record("data_validity", "best-players (optional enrichment)", f"event/{finished_id}/best-players", None, best, expect="optional_404")
    rankings = get(base, headers, f"team/{team_id}/rankings", {"page": 1, "limit": 5})
    record("data_validity", "team rankings (optional enrichment)", f"team/{team_id}/rankings", {"page": 1, "limit": 5}, rankings, expect="optional_404")
    top = get(base, headers, f"event/{finished_id}/top-performers")
    record("data_validity", "off-catalog top-performers", f"event/{finished_id}/top-performers", None, top, expect="not_found")

    for st_type in ("total", "home", "away"):
        r = get(base, headers, f"unique-tournament/{tournament_id}/season/{season_id}/standings/{st_type}")
        body = r.get("body") if isinstance(r.get("body"), dict) else {}
        tables = body.get("standings") or []
        rows_n = 0
        if tables and isinstance(tables[0], dict):
            rows_n = len(tables[0].get("rows") or [])
        extra_v = {"force_verdict": "PASS_EMPTY"} if st_type in ("home", "away") and rows_n == 0 and r.get("http") == 200 else None
        record(
            "data_validity",
            f"standings {st_type} row count",
            f"unique-tournament/{tournament_id}/season/{season_id}/standings/{st_type}",
            None,
            r,
            notes=f"tables={len(tables) if isinstance(tables, list) else 0} rows={rows_n}",
            extra=extra_v,
        )

    featured = get(base, headers, f"team/{team_id}/featured-event")
    feat_ev = ((featured.get("body") or {}) if isinstance(featured.get("body"), dict) else {}).get("event") or {}
    feat_status = status_type(feat_ev)
    record(
        "data_validity",
        "featured-event status",
        f"team/{team_id}/featured-event",
        None,
        featured,
        notes=f"featuredEventId={feat_ev.get('id')} status={feat_status}",
        extra={"status": feat_status, "eventId": feat_ev.get("id")},
    )

    lineups = get(base, headers, f"event/{finished_id}/lineups")
    jersey_null = 0
    jersey_filled = 0
    lbody = lineups.get("body") if isinstance(lineups.get("body"), dict) else {}
    for side in ("home", "away"):
        for row in ((lbody.get(side) or {}).get("players") or []):
            pl = row.get("player") if isinstance(row, dict) else None
            num = None
            if isinstance(row, dict):
                num = row.get("jerseyNumber") or row.get("shirtNumber")
            if isinstance(pl, dict) and num is None:
                num = pl.get("jerseyNumber") or pl.get("shirtNumber")
            if num in (None, "", 0):
                jersey_null += 1
            else:
                jersey_filled += 1
    record(
        "data_validity",
        "lineup jersey numbers",
        f"event/{finished_id}/lineups",
        None,
        lineups,
        notes=f"jerseyFilled={jersey_filled} jerseyNull={jersey_null}",
        extra={"jerseyFilled": jersey_filled, "jerseyNull": jersey_null},
    )

    err = get(base, headers, "event/abc")
    ebody = err.get("body") if isinstance(err.get("body"), dict) else {}
    record(
        "data_validity",
        "error message shape (non-numeric event id)",
        "event/abc",
        None,
        err,
        notes=f"message type={type(ebody.get('message')).__name__} error={ebody.get('error')!r} detailsType={type(ebody.get('details')).__name__}",
        extra={
            "messageType": type(ebody.get("message")).__name__,
            "error": ebody.get("error"),
            "detailsType": type(ebody.get("details")).__name__,
            "details": ebody.get("details") if not isinstance(ebody.get("details"), (dict, list)) else ebody.get("details"),
        },
        expect="validation",
    )

    off_paths = [
        ("football-style player season stats (on-catalog for hockey)", f"player/{player_id}/unique-tournament/{tournament_id}/season/{season_id}/statistics"),
        ("off-catalog player/{id}/statistics", f"player/{player_id}/statistics"),
        ("off-catalog team season statistics", f"team/{team_id}/unique-tournament/{tournament_id}/season/{season_id}/statistics"),
    ]
    for name, path in off_paths:
        r = get(base, headers, path)
        expect = None if "on-catalog" in name else "not_found"
        record("off_catalog", name, path, None, r, expect=expect)

    # --- auth ---
    both = {"accept": "application/json", "x-apim-key": keys["apim"], "X-Live-Key": keys["live"]}
    live_only = {"accept": "application/json", "X-Live-Key": keys["live"]}
    apim_only = {"accept": "application/json", "x-apim-key": keys["apim"]}
    none = {"accept": "application/json"}
    for label, hdrs, expect in [
        ("both headers", both, "auth_ok"),
        ("X-Live-Key only", live_only, "auth_ok"),
        ("x-apim-key only", apim_only, "auth_reject"),
        ("no API keys", none, "auth_reject"),
    ]:
        r = get(base, hdrs, "events", {"page": 1, "limit": 1})
        record(
            "auth",
            f"/events?limit=1 {label}",
            "events",
            {"page": 1, "limit": 1},
            r,
            notes=f"http={r.get('http')} json={r.get('json')} bytes={r.get('bytes')}",
            extra={"headerSet": label, "jsonBody": bool(r.get("json")), "contentType": r.get("contentType")},
            expect=expect,
        )

    # --- event-state variation ---
    suffixes = [
        (" detail", "", None),
        ("/lineups", "/lineups", None),
        ("/statistics", "/statistics", None),
        ("/incidents", "/incidents", {"page": 1, "limit": 5}),
        ("/best-players", "/best-players", None),
        ("/player-statistics", "/player-statistics", {"page": 1, "limit": 5}),
    ]
    for label, eid in by_type.items():
        for suffix_name, suffix, params in suffixes:
            p = f"event/{eid}{suffix}"
            r = get(base, headers, p, params)
            expect = "optional_404" if suffix == "/best-players" else None
            record("event_state_variation", f"{label} event{suffix_name}", p, params, r, notes=f"eventId={eid}", expect=expect)

    # --- second team / player ---
    record("entity_variation", f"team events last ({team_name})", f"team/{team_id}/events/last", {"page": 1, "limit": 3}, get(base, headers, f"team/{team_id}/events/last", {"page": 1, "limit": 3}))
    if team2_id:
        record("entity_variation", f"team events last ({team2_name})", f"team/{team2_id}/events/last", {"page": 1, "limit": 3}, get(base, headers, f"team/{team2_id}/events/last", {"page": 1, "limit": 3}))
    record("entity_variation", f"player events last ({player_name})", f"player/{player_id}/events/last", {"page": 1, "limit": 3}, get(base, headers, f"player/{player_id}/events/last", {"page": 1, "limit": 3}))
    if player2_id:
        record("entity_variation", f"player events last ({player2_name})", f"player/{player2_id}/events/last", {"page": 1, "limit": 3}, get(base, headers, f"player/{player2_id}/events/last", {"page": 1, "limit": 3}))

    # --- enrichment types ---
    if finished_id:
        enr = get(base, headers, f"event/{finished_id}/enrichments")
        types = []
        for t in ((enr.get("body") or {}) if isinstance(enr.get("body"), dict) else {}).get("types") or []:
            if isinstance(t, dict) and t.get("type"):
                types.append(t["type"])
            elif isinstance(t, str):
                types.append(t)
        record("enrichment_type_variation", "event enrichments index", f"event/{finished_id}/enrichments", None, enr)
        for et in types[:8]:
            r = get(base, headers, f"event/{finished_id}/enrichments/{et}")
            record("enrichment_type_variation", f"event enrichments/{et}", f"event/{finished_id}/enrichments/{et}", None, r)

    by_verdict: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for t in tests:
        by_verdict[t["verdict"]] = by_verdict.get(t["verdict"], 0) + 1
        by_category[t["category"]] = by_category.get(t["category"], 0) + 1

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sport": SPORT,
        "discoveredIds": {
            "teamId": team_id,
            "teamName": team_name,
            "team2Id": team2_id,
            "team2Name": team2_name,
            "playerId": player_id,
            "playerName": player_name,
            "player2Id": player2_id,
            "player2Name": player2_name,
            "tournamentId": tournament_id,
            "seasonId": season_id,
            "statsPlayerId": stats_player,
        },
        "discoveredEventIdsByState": by_type,
        "summary": {
            "totalTests": len(tests),
            "byVerdict": by_verdict,
            "byCategory": by_category,
        },
        "findings": findings,
        "tests": tests,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=str))
    print(f"Wrote {OUT} ({len(tests)} tests) verdicts={by_verdict} states={by_type}")


if __name__ == "__main__":
    main()
