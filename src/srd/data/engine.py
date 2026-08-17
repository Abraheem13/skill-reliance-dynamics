"""Absolute skill measurement via mean centipawn loss (ACPL).

Why not Elo: Elo is zero-sum and inflates with the population. It cannot answer
"did human chess get objectively stronger or weaker across the engine era".
ACPL against a fixed engine at fixed depth can.

Reproducibility rules, fixed in advance and NOT to be changed mid-project:
  * FIXED DEPTH, never fixed time. Time-based analysis is hardware-dependent
    and not reproducible.
  * Engine version and depth recorded in every output row.
  * Opening book moves (ply < BOOK_PLY) excluded: they measure preparation.
  * Decisively won/lost positions excluded via EVAL_CLAMP, because centipawn
    loss is meaningless when any move wins.

Follows the intrinsic-performance-rating approach of Regan & Haworth.
"""
from __future__ import annotations
import io
from dataclasses import dataclass, asdict
from typing import Optional

import chess
import chess.pgn
import chess.engine

BOOK_PLY = 24
EVAL_CLAMP = 300


@dataclass
class EngineConfig:
    path: str = "stockfish"
    depth: int = 16
    threads: int = 1
    hash_mb: int = 256
    multipv: int = 1

    def to_dict(self):
        return asdict(self)


def _cp(score, pov) -> Optional[int]:
    s = score.pov(pov)
    if s.is_mate():
        return None
    return s.score()


def analyse_game(pgn_text: str, engine, cfg: EngineConfig) -> dict:
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        return {}
    board = game.board()
    losses = {chess.WHITE: [], chess.BLACK: []}
    limit = chess.engine.Limit(depth=cfg.depth)

    for ply, move in enumerate(game.mainline_moves()):
        mover = board.turn
        if ply >= BOOK_PLY:
            info = engine.analyse(board, limit)
            best_cp = _cp(info["score"], mover)
            if best_cp is not None and abs(best_cp) <= EVAL_CLAMP:
                board.push(move)
                info2 = engine.analyse(board, limit)
                after_cp = _cp(info2["score"], mover)
                board.pop()
                if after_cp is not None:
                    losses[mover].append(max(0, best_cp - after_cp))
        board.push(move)

    h = game.headers
    out = {
        "white": h.get("White"), "black": h.get("Black"),
        "white_elo": h.get("WhiteElo"), "black_elo": h.get("BlackElo"),
        "date": h.get("UTCDate") or h.get("Date"),
        "event": h.get("Event"),
        "engine_depth": cfg.depth,
    }
    for pov, name in ((chess.WHITE, "white"), (chess.BLACK, "black")):
        L = losses[pov]
        out[f"{name}_acpl"] = (sum(L) / len(L)) if L else None
        out[f"{name}_n_positions"] = len(L)
    return out


def open_engine(cfg: EngineConfig):
    eng = chess.engine.SimpleEngine.popen_uci(cfg.path)
    eng.configure({"Threads": cfg.threads, "Hash": cfg.hash_mb})
    return eng


def engine_identity(cfg: EngineConfig) -> dict:
    """Record exactly which engine produced the numbers. Goes in the paper."""
    eng = open_engine(cfg)
    try:
        return {"id": dict(eng.id), **cfg.to_dict()}
    finally:
        eng.quit()
