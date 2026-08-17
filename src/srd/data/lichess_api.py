"""Player-centric acquisition via the Lichess API.

Why this exists
---------------
The monthly dumps are game-centric. A random sample of games from a pool of
millions of accounts yields almost no repeat players, so it cannot support a
within-player design. Instead we:

  1. harvest candidate usernames from an EARLY dump (accounts active in 2014)
  2. ask the API which are still active years later
  3. download each survivor's games for the target years

Survivorship bias is REAL and must be declared: accounts still playing after a
decade are not typical. This is ordinary panel attrition, reported as such. The
alternative (between-player comparison) is confounded by pool composition,
which is worse and less fixable.

API docs: https://lichess.org/api - free, rate-limited, no key needed.
Be polite: one request at a time, back off on 429.
"""
from __future__ import annotations
import time
from typing import Iterator, Optional

import re

import requests

PGN_SPLIT = re.compile(r"\n\s*\n(?=\[Event )")

API = "https://lichess.org"
UA = "srd-research/0.1 (academic study of skill dynamics)"


class RateLimited(Exception):
    pass


def _get(path: str, params: dict | None = None, accept: str = "application/json",
         timeout: int = 60, max_retries: int = 5):
    url = f"{API}{path}"
    headers = {"Accept": accept, "User-Agent": UA}
    for attempt in range(max_retries):
        r = requests.get(url, params=params, headers=headers,
                         timeout=timeout, stream=(accept != "application/json"))
        if r.status_code == 429:
            wait = 60 * (attempt + 1)
            print(f"    rate limited, sleeping {wait}s")
            time.sleep(wait)
            continue
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r
    raise RateLimited(path)


def user_info(username: str) -> Optional[dict]:
    r = _get(f"/api/user/{username}")
    return r.json() if r is not None else None


def is_active_in(username: str, year: int) -> bool:
    """Cheap filter: does the account's activity window cover this year?"""
    info = user_info(username)
    if not info or info.get("disabled") or info.get("tosViolation"):
        return False
    created = info.get("createdAt", 0) / 1000
    seen = info.get("seenAt", 0) / 1000
    return time.gmtime(created).tm_year <= year <= time.gmtime(seen).tm_year


def ms(year: int, month: int = 1, day: int = 1) -> int:
    return int(time.mktime((year, month, day, 0, 0, 0, 0, 0, 0)) * 1000)


def fetch_user_games(username: str, year: int, max_games: int = 40,
                     perf: str = "blitz,rapid,classical") -> Iterator[str]:
    """Stream one user's rated games for a calendar year as PGN blocks."""
    params = {
        "since": ms(year, 1, 1),
        "until": ms(year + 1, 1, 1),
        "max": max_games,
        "perfType": perf,
        "rated": "true",
        "moves": "true",
        "tags": "true",
        "clocks": "false",
        "evals": "false",
        "opening": "false",
    }
    r = _get(f"/api/games/user/{username}", params=params,
             accept="application/x-chess-pgn")
    if r is None:
        return
    buf = ""
    try:
        for raw in r.iter_content(chunk_size=1 << 16):
            if not raw:
                continue
            buf += raw.decode("utf-8", errors="replace")
            parts = PGN_SPLIT.split(buf)
            for block in parts[:-1]:
                if block.strip():
                    yield block.strip()
            buf = parts[-1]
        if buf.strip():
            yield buf.strip()
    finally:
        r.close()


def harvest_usernames(dump_path: str, limit: int = 4000,
                      min_elo: int = 1400) -> list:
    """Pull candidate usernames from an early dump (no API calls)."""
    from .lichess import iter_games_text, parse_headers
    seen = {}
    for block in iter_games_text(dump_path):
        h = parse_headers(block)
        for side, elo_key in (("White", "WhiteElo"), ("Black", "BlackElo")):
            u = h.get(side)
            try:
                e = int(h.get(elo_key, "0"))
            except ValueError:
                e = 0
            if u and e >= min_elo:
                seen[u] = seen.get(u, 0) + 1
        if len(seen) >= limit * 4:
            break
    # accounts seen more than once in the early month are likelier to persist
    return [u for u, _ in sorted(seen.items(), key=lambda kv: -kv[1])][:limit]
