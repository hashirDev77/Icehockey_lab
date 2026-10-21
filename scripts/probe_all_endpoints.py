#!/usr/bin/env python3
"""Probe all ice_hockey msdata catalog routes; write JSON evidence for docs."""
from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
OUT_JSON = ROOT / "data" / "ice-hockey-endpoint-evidence.json"
ROUTES_JSON = ROOT / "data" / "ice-hockey-routes.json"
SPORT = "ice_hockey"


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        alt = Path("/Users/apple/Desktop/Baseball_Product/.env")
        path = alt if alt.exists() else path
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _curl_get(url: str, headers: dict[str, str]) -> dict:
    cmd = ["/usr/bin/curl", "-sS", "-w", "\n%{http_code}", "--max-time", "60"]
    for k, v in headers.items():
        cmd.extend(["-H", f"{k}: {v}"])
    cmd.append(url)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return {
            "url": url,
            "http": 0,
            "bytes": 0,
            "body": None,
            "error": proc.stderr.strip() or f"curl exit {proc.returncode}",
        }
    text = proc.stdout
    nl = text.rfind("\n")
    body_text = text[:nl] if nl >= 0 else ""
    code_text = text[nl + 1 :] if nl >= 0 else text
    try:
        http = int(code_text.strip())
    except Exception:
        http = 0
    parsed = None
    if body_text:
        try:
            parsed = json.loads(body_text)
        except Exception:
            parsed = {"raw": body_text[:800]}
    return {
        "url": url,
        "http": http,
        "bytes": len(body_text.encode("utf-8")),
        "body": parsed,
        "error": (parsed or {}).get("message") if isinstance(parsed, dict) and http >= 400 else None,
    }


def get(base: str, headers: dict[str, str], path: str, params: dict | None = None) -> dict:
    url = f"{base.rstrip('/')}/v1/{SPORT}/{path.lstrip('/')}"
    if params:
        q = {k: v for k, v in params.items() if v is not None}
        url += "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
            parsed = json.loads(body) if body else None
            return {"path": path, "url": url, "http": resp.status, "bytes": len(body), "body": parsed}
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            parsed = json.loads(body) if body else None
        except Exception:
            parsed = {"raw": body[:800].decode("utf-8", "replace")}
        return {
            "path": path,
            "url": url,
            "http": e.code,
            "bytes": len(body or b""),
            "body": parsed,
            "error": (parsed or {}).get("message") if isinstance(parsed, dict) else str(e),
        }
    except Exception as e:
        err = str(e)
        if "CERTIFICATE_VERIFY_FAILED" in err or "SSL" in err:
            curled = _curl_get(url, headers)
            curled["path"] = path
            return curled
        return {"path": path, "url": url, "http": 0, "bytes": 0, "body": None, "error": err}


def id_from_search_item(item: dict) -> int | None:
    if not isinstance(item, dict):
        return None
    try:
        return int(item["id"])
    except Exception:
        return None


def first_id_of_type(items: list, wanted: str) -> int | None:
    for item in items or []:
        if not isinstance(item, dict):
            continue
        itype = (item.get("type") or "").lower()
        if wanted in itype:
            found = id_from_search_item(item)
            if found:
                return found
    return None


def classify_response(path: str, result: dict) -> dict:
    http = result.get("http")
    body = result.get("body")
    out: dict = {
        "http": http,
        "bytes": result.get("bytes"),
        "responseKind": "unknown",
        "topLevelKeys": [],
        "listKey": None,
        "listCount": None,
        "pagination": None,
        "nestedObjectKeys": None,
        "sampleRowKeys": None,
        "apiError": None,
        "notes": [],
    }
    if not isinstance(body, dict):
        out["responseKind"] = "non-object or empty"
        return out

    out["topLevelKeys"] = list(body.keys())

    if body.get("statusCode") or body.get("error") in ("NotFound", "BadRequest"):
        out["responseKind"] = "error envelope"
        out["apiError"] = {
            "statusCode": body.get("statusCode"),
            "message": body.get("message"),
            "error": body.get("error"),
            "details": body.get("details"),
        }
        return out

    pag_keys = ("page", "limit", "total", "totalPages", "hasMore")
    if any(k in body for k in pag_keys):
        out["pagination"] = {k: body.get(k) for k in pag_keys if k in body}

    list_candidates = [
        "items",
        "events",
        "players",
        "seasons",
        "media",
        "rankings",
        "types",
        "incidents",
        "playerStatistics",
        "leaderboard",
        "topPerformers",
        "bestPlayers",
        "standings",
        "uniqueTournaments",
        "uniqueTournamentSeasons",
        "tournamentSeasons",
        "statistics",
        "groups",
    ]
    for key in list_candidates:
        if isinstance(body.get(key), list):
            lst = body[key]
            out["listKey"] = key
            out["listCount"] = len(lst)
            out["responseKind"] = "paginated list" if out["pagination"] else "list envelope"
            if lst and isinstance(lst[0], dict):
                out["sampleRowKeys"] = list(lst[0].keys())[:30]
            break

    object_wrappers = {
        "event": "match object",
        "player": "player object",
        "team": "team object",
        "uniqueTournament": "competition object",
        "manager": "manager object",
        "statistics": "statistics object",
    }
    if out["responseKind"] == "unknown" or (
        out["responseKind"] in ("list envelope", "paginated list") and not out["listKey"]
    ):
        for key, kind in object_wrappers.items():
            if isinstance(body.get(key), dict):
                out["responseKind"] = kind
                out["nestedObjectKeys"] = list(body[key].keys())[:35]
                break

    if out["responseKind"] == "unknown":
        if body.get("home") and body.get("away"):
            out["responseKind"] = "home/away split (lineups or similar)"
            for side in ("home", "away"):
                s = body.get(side)
                if isinstance(s, dict):
                    out.setdefault("sideKeys", {})[side] = list(s.keys())[:25]
        elif body.get("homeTeam") and body.get("awayTeam"):
            out["responseKind"] = "pregame form envelope"
        elif body.get("previousEvent") is not None or body.get("nextEvent") is not None:
            out["responseKind"] = "previous/next event envelope"
        elif "teamDuel" in body or "managerDuel" in body:
            out["responseKind"] = "object (teamDuel, managerDuel)"
        else:
            out["responseKind"] = f"object ({', '.join(list(body.keys())[:8])})"

    return out


def list_params_for(path: str, ids: dict) -> dict | None:
    p = path.split("?")[0]
    if p in ("events", "fixtures/today", "teams", "players", "tournaments", "search"):
        params = {"page": 1, "limit": 5}
        if p == "search":
            params["q"] = ids.get("searchQuery", "Maple Leafs")
        return params
    paginated_suffixes = (
        "/events/last",
        "/events/next",
        "/player-statistics",
        "/incidents",
        "/media",
        "/performance",
        "/rankings",
        "/unique-tournaments",
        "/standings-seasons",
        "/seasons",
        "/statistics",
    )
    if any(p.endswith(s) for s in paginated_suffixes):
        if p.endswith("/event/" + str(ids.get("eventId", "")) + "/statistics"):
            return None
        if re.search(r"^event/\d+/statistics$", p):
            return None
        if re.search(r"^event/\d+/player/\d+/statistics$", p):
            return None
        return {"page": 1, "limit": 5}
    if re.search(r"unique-tournament/\d+/events$", p):
        return {"page": 1, "limit": 5}
    if re.search(r"unique-tournament/\d+/scheduled-events/", p):
        return {"page": 1, "limit": 5}
    if re.search(r"/season/\d+/round/", p):
        return {"page": 1, "limit": 5}
    return None


def substitute_path(template: str, ids: dict) -> tuple[str, dict | None]:
    p = template.replace(f"/v1/{SPORT}/", "")
    if "{eventId}" in p:
        p = p.replace("{eventId}", str(ids["eventId"]))
    if "{playerId}" in p:
        player_for_path = ids.get("lineupPlayerId") if "/player/{playerId}/statistics" in template else ids["playerId"]
        if "/player/{playerId}/statistics" in template and "event/" in template:
            p = p.replace("{playerId}", str(ids.get("playerIdForEventStats") or ids.get("lineupPlayerId") or ids["playerId"]))
        else:
            p = p.replace("{playerId}", str(player_for_path if player_for_path else ids["playerId"]))
    if "{teamId}" in p:
        p = p.replace("{teamId}", str(ids["teamId"]))
    if "{managerId}" in p:
        p = p.replace("{managerId}", str(ids.get("managerId") or ""))
    if "{tournamentId}" in p:
        p = p.replace("{tournamentId}", str(ids["tournamentId"]))
    if "{seasonId}" in p:
        p = p.replace("{seasonId}", str(ids["seasonId"]))
    if "{direction}" in p:
        p = p.replace("{direction}", "last")
    if "{date}" in p:
        p = p.replace("{date}", ids["date"])
    if "{round}" in p:
        p = p.replace("{round}", str(ids.get("round") or "1"))
    if "{type}" in p:
        if "/standings/" in p:
            p = p.replace("{type}", "total")
        elif "/team/" in p and "/enrichments/" in p:
            p = p.replace("{type}", ids.get("teamEnrichmentType") or "events_last")
        else:
            p = p.replace("{type}", ids.get("enrichmentType") or "best_players")
    return p, list_params_for(p, ids)


def _items(body) -> list:
    if not isinstance(body, dict):
        return []
    for key in ("items", "events", "players", "seasons", "types"):
        val = body.get(key)
        if isinstance(val, list):
            return val
    return []


def discover_ids(base: str, headers: dict[str, str]) -> dict:
    ids: dict = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "enrichmentType": None,
        "teamEnrichmentType": None,
        "managerId": None,
        "lineupPlayerId": None,
        "round": "1",
        "searchQuery": "Maple Leafs",
    }

    searches = [
        ("Maple Leafs", "team"),
        ("Canadiens", "team"),
        ("Bruins", "team"),
        ("Connor McDavid", "player"),
        ("Sidney Crosby", "player"),
        ("NHL", "uniquetournament"),
        ("Stanley Cup", "uniquetournament"),
    ]
    for q, wanted in searches:
        result = get(base, headers, "search", {"q": q, "page": 1, "limit": 10})
        items = _items(result.get("body"))
        found = first_id_of_type(items, wanted)
        if not found and items:
            found = id_from_search_item(items[0])
        if wanted == "team" and found and not ids.get("teamId"):
            ids["teamId"] = found
            ids["searchQuery"] = q
        elif wanted == "player" and found and not ids.get("playerId"):
            ids["playerId"] = found
        elif wanted == "uniquetournament" and found and not ids.get("tournamentId"):
            ids["tournamentId"] = found

    if not ids.get("teamId"):
        teams = get(base, headers, "teams", {"page": 1, "limit": 5})
        row = (_items(teams.get("body")) or [None])[0]
        ids["teamId"] = id_from_search_item(row) if row else None
    if not ids.get("playerId"):
        players = get(base, headers, "players", {"page": 1, "limit": 5})
        row = (_items(players.get("body")) or [None])[0]
        ids["playerId"] = id_from_search_item(row) if row else None
    if not ids.get("tournamentId"):
        tournaments = get(base, headers, "tournaments", {"page": 1, "limit": 5})
        row = (_items(tournaments.get("body")) or [None])[0]
        ids["tournamentId"] = id_from_search_item(row) if row else None

    team_last = get(base, headers, f"team/{ids['teamId']}/events/last", {"page": 1, "limit": 15})
    finished = None
    sample_event = None
    for ev in (team_last.get("body") or {}).get("events") or []:
        if not isinstance(ev, dict):
            continue
        if sample_event is None:
            sample_event = ev
        st = ev.get("status") or {}
        stype = st.get("type") if isinstance(st, dict) else ev.get("statusType")
        if stype == "finished":
            finished = ev.get("id")
            sample_event = ev
            break
    ids["eventId"] = finished or (sample_event or {}).get("id")

    if sample_event:
        round_info = sample_event.get("roundInfo") or {}
        if isinstance(round_info, dict) and round_info.get("round") is not None:
            ids["round"] = str(round_info["round"])
        tour = sample_event.get("tournament") or sample_event.get("uniqueTournament") or {}
        if isinstance(tour, dict):
            ut = tour.get("uniqueTournament") if isinstance(tour.get("uniqueTournament"), dict) else tour
            if isinstance(ut, dict) and ut.get("id") and not ids.get("tournamentId"):
                ids["tournamentId"] = ut["id"]
        season = sample_event.get("season") or {}
        if isinstance(season, dict) and season.get("id"):
            ids["seasonId"] = season["id"]

    event_detail = get(base, headers, f"event/{ids['eventId']}")
    ev_obj = (event_detail.get("body") or {}).get("event") or event_detail.get("body") or {}
    if isinstance(ev_obj, dict):
        if not ids.get("seasonId"):
            season = ev_obj.get("season") or {}
            if isinstance(season, dict) and season.get("id"):
                ids["seasonId"] = season["id"]
        round_info = ev_obj.get("roundInfo") or {}
        if isinstance(round_info, dict) and round_info.get("round") is not None:
            ids["round"] = str(round_info["round"])
        tour = ev_obj.get("tournament") or {}
        ut = tour.get("uniqueTournament") if isinstance(tour, dict) else None
        if isinstance(ut, dict) and ut.get("id"):
            ids["tournamentId"] = ut["id"]
        elif isinstance(tour, dict) and tour.get("id") and not ids.get("tournamentId"):
            ids["tournamentId"] = tour["id"]

    seasons = get(base, headers, f"unique-tournament/{ids['tournamentId']}/seasons", {"page": 1, "limit": 5})
    sbody = seasons.get("body") or {}
    season_list = sbody.get("seasons") or sbody.get("items") or []
    if not ids.get("seasonId") and season_list:
        ids["seasonId"] = season_list[0].get("id")
    if sbody.get("currentSeasonId") and not ids.get("seasonId"):
        ids["seasonId"] = sbody["currentSeasonId"]

    lineups = get(base, headers, f"event/{ids['eventId']}/lineups")
    lbody = lineups.get("body") or {}
    for side in ("home", "away"):
        s = lbody.get(side) or {}
        mgr = s.get("manager") or s.get("coach")
        if isinstance(mgr, dict) and mgr.get("id") and not ids.get("managerId"):
            ids["managerId"] = mgr["id"]
        for p in s.get("players") or []:
            pl = (p.get("player") or p) if isinstance(p, dict) else None
            if isinstance(pl, dict) and pl.get("id"):
                ids["lineupPlayerId"] = pl["id"]
                break
        if ids.get("lineupPlayerId") and ids.get("managerId"):
            break

    if not ids.get("managerId"):
        team = get(base, headers, f"team/{ids['teamId']}")
        t = (team.get("body") or {}).get("team") or {}
        mgr = t.get("manager") or t.get("coach")
        if isinstance(mgr, dict) and mgr.get("id"):
            ids["managerId"] = mgr["id"]

    if not ids.get("playerId") and ids.get("lineupPlayerId"):
        ids["playerId"] = ids["lineupPlayerId"]

    stats = get(base, headers, f"event/{ids['eventId']}/player-statistics", {"page": 1, "limit": 5})
    stats_player = None
    for row in (stats.get("body") or {}).get("playerStatistics") or []:
        pl = (row.get("player") or row) if isinstance(row, dict) else None
        if isinstance(pl, dict) and pl.get("id"):
            stats_player = pl["id"]
            break
    ids["playerIdForEventStats"] = stats_player or ids.get("lineupPlayerId") or ids.get("playerId")

    enr = get(base, headers, f"event/{ids['eventId']}/enrichments")
    types = []
    for t in (enr.get("body") or {}).get("types") or []:
        if isinstance(t, dict):
            types.append(t.get("type"))
        elif isinstance(t, str):
            types.append(t)
    if types:
        ids["enrichmentType"] = types[0]

    tenr = get(base, headers, f"team/{ids['teamId']}/enrichments")
    ttypes = []
    for t in (tenr.get("body") or {}).get("types") or []:
        if isinstance(t, dict):
            ttypes.append(t.get("type"))
        elif isinstance(t, str):
            ttypes.append(t)
    ids["teamEnrichmentType"] = ttypes[0] if ttypes else "events_last"

    missing = [k for k in ("eventId", "teamId", "playerId", "tournamentId", "seasonId") if not ids.get(k)]
    if missing:
        raise SystemExit(f"Failed to discover required IDs: {missing}. Partial map: {ids}")
    return ids


def _preview(body, max_len: int = 1200) -> str | None:
    if body is None:
        return None
    text = json.dumps(body, default=str)
    if len(text) > max_len:
        return text[:max_len] + "…"
    return text


def main() -> None:
    env = load_env(ENV_PATH)
    base = (
        env.get("MSDATA_BASE_URL")
        or env.get("VITE_MSDATA_BASE_URL")
        or "https://sports-api.sportsdata365.com/msdata"
    ).rstrip("/")
    headers = {
        "accept": "application/json",
        "x-apim-key": env.get("MSDATA_API_KEY") or env.get("VITE_MSDATA_API_KEY") or "",
        "X-Live-Key": env.get("MSDATA_LIVE_KEY") or env.get("VITE_MSDATA_LIVE_KEY") or "",
    }

    routes_doc = json.loads(ROUTES_JSON.read_text())
    if "ice-hockey" in routes_doc:
        route_templates = routes_doc["ice-hockey"]["routes"]
    elif "ice_hockey" in routes_doc:
        route_templates = routes_doc["ice_hockey"]["routes"]
    else:
        route_templates = routes_doc["routes"]

    ids = discover_ids(base, headers)
    print("Discovered IDs:", json.dumps({k: ids[k] for k in ids if k != "searchQuery"}, default=str))

    results = []
    for template in route_templates:
        rel, params = substitute_path(template, ids)
        if "/enrichments/{type}" in template and "team/" in template:
            rel = re.sub(r"/enrichments/[^/]+$", f"/enrichments/{ids['teamEnrichmentType']}", rel)
        if "/enrichments/{type}" in template and "event/" in template:
            rel = re.sub(r"/enrichments/[^/]+$", f"/enrichments/{ids['enrichmentType']}", rel)
        if "/standings/{type}" in template:
            rel = rel.replace("{type}", "total") if "{type}" in rel else rel
        raw = get(base, headers, rel, params)
        summary = classify_response(template, raw)
        results.append(
            {
                "routeTemplate": template,
                "calledPath": rel,
                "query": params,
                "idsUsed": {
                    k: ids[k]
                    for k in (
                        "eventId",
                        "teamId",
                        "playerId",
                        "tournamentId",
                        "seasonId",
                        "managerId",
                        "date",
                        "round",
                    )
                    if k in ids
                },
                "http": raw.get("http"),
                "bytes": raw.get("bytes"),
                "error": raw.get("error"),
                "classification": summary,
                "bodyPreview": _preview(raw.get("body")),
            }
        )

    extras = []
    events_p1 = get(base, headers, "events", {"page": 1, "limit": 5})
    events_p2 = get(base, headers, "events", {"page": 2, "limit": 5})
    id1 = None
    id2 = None
    try:
        id1 = ((events_p1.get("body") or {}).get("items") or [None])[0].get("id")
        id2 = ((events_p2.get("body") or {}).get("items") or [None])[0].get("id")
    except Exception:
        pass
    pagination_ok = bool(id1 and id2 and id1 != id2)

    extra_calls = [
        ("events status=finished", "events", {"page": 1, "limit": 5, "status": "finished"}),
        ("events status=inprogress", "events", {"page": 1, "limit": 5, "status": "inprogress"}),
        ("events page=9999", "events", {"page": 9999, "limit": 5}),
        ("events page=2 differs from page=1", "events", {"page": 2, "limit": 5}),
        ("search missing q", "search", {"page": 1, "limit": 5}),
        ("event id non-numeric", "event/abc", None),
        ("event id unknown", "event/999999999", None),
        (
            "standings home",
            f"unique-tournament/{ids['tournamentId']}/season/{ids['seasonId']}/standings/home",
            None,
        ),
        (
            "standings away",
            f"unique-tournament/{ids['tournamentId']}/season/{ids['seasonId']}/standings/away",
            None,
        ),
        ("player events next", f"player/{ids['playerId']}/events/next", {"page": 1, "limit": 5}),
        ("team events next", f"team/{ids['teamId']}/events/next", {"page": 1, "limit": 5}),
    ]
    for label, path, params in extra_calls:
        raw = get(base, headers, path, params)
        extra_row = {
            "label": label,
            "path": path,
            "params": params,
            "http": raw.get("http"),
            "classification": classify_response(path, raw),
            "bodyPreview": _preview(raw.get("body")),
        }
        if label == "events page=2 differs from page=1":
            extra_row["paginationCheck"] = {
                "page1FirstId": id1,
                "page2FirstId": id2,
                "differentPages": pagination_ok,
            }
        extras.append(extra_row)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "baseUrl": base,
        "sport": SPORT,
        "routeCount": len(route_templates),
        "discoveredIds": ids,
        "routes": results,
        "extraProbes": extras,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, default=str))
    print(f"Wrote {OUT_JSON} ({len(results)} routes, {len(extras)} extras)")


if __name__ == "__main__":
    main()
