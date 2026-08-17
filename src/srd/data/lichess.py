"""Streaming, sampled acquisition of Lichess games.

Monthly dumps are tens of GB compressed. We never materialise one. We
stream-decompress and reservoir-sample stratified by rating band, so the sample
is unbiased with respect to position in the file (games are roughly time-ordered
within a month, so head-truncation would bias by date).

Source: https://database.lichess.org  (CC0)
"""
from __future__ import annotations
import io, os, random, re
from dataclasses import dataclass
from typing import Iterator, Optional

import zstandard as zstd

BASE = "https://database.lichess.org/standard"


def month_url(year: int, month: int) -> str:
    return f"{BASE}/lichess_db_standard_rated_{year}-{month:02d}.pgn.zst"


def stream_pgn_text(path_or_url: str, chunk: int = 1 << 22) -> Iterator[str]:
    dctx = zstd.ZstdDecompressor(max_window_size=2 ** 31)
    with open(path_or_url, "rb") as fh:
        with dctx.stream_reader(fh) as reader:
            wrapper = io.TextIOWrapper(reader, encoding="utf-8", errors="replace")
            while True:
                data = wrapper.read(chunk)
                if not data:
                    break
                yield data


def iter_games_text(path: str) -> Iterator[str]:
    buf = ""
    for chunk in stream_pgn_text(path):
        buf += chunk
        parts = re.split(r"\n\n(?=\[Event )", buf)
        for g in parts[:-1]:
            if g.strip():
                yield g.strip()
        buf = parts[-1]
    if buf.strip():
        yield buf.strip()


HEADER_RE = re.compile(r'^\[(\w+)\s+"(.*)"\]$', re.M)


def parse_headers(block: str) -> dict:
    return {m.group(1): m.group(2) for m in HEADER_RE.finditer(block)}


def rating_band(elo: Optional[int], edges=(1400, 1800, 2200)) -> Optional[str]:
    if elo is None:
        return None
    if elo < edges[0]:
        return "u1400"
    if elo < edges[1]:
        return "1400-1799"
    if elo < edges[2]:
        return "1800-2199"
    return "2200+"


@dataclass
class SampleSpec:
    per_band: int = 500
    min_moves: int = 20
    time_controls: tuple = ("classical", "rapid")
    seed: int = 0


def reservoir_sample(path: str, spec: SampleSpec) -> dict:
    """Stratified reservoir sample. One pass, bounded memory."""
    rng = random.Random(spec.seed)
    keep, seen = {}, {}
    for block in iter_games_text(path):
        h = parse_headers(block)
        try:
            welo = int(h.get("WhiteElo", "0"))
            belo = int(h.get("BlackElo", "0"))
        except ValueError:
            continue
        if welo == 0 or belo == 0:
            continue
        ev = h.get("Event", "").lower()
        if not any(tc in ev for tc in spec.time_controls):
            continue
        if block.count(".") < spec.min_moves:
            continue
        band = rating_band(min(welo, belo))
        if band is None:
            continue
        seen[band] = seen.get(band, 0) + 1
        bucket = keep.setdefault(band, [])
        if len(bucket) < spec.per_band:
            bucket.append(block)
        else:
            j = rng.randrange(seen[band])
            if j < spec.per_band:
                bucket[j] = block
    return keep
