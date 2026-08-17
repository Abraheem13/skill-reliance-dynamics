"""Step 05e - check the sample files are intact.

A truncated write leaves a partial JSON line that silently breaks downstream
parsing. This drops bad lines and reports what it found.
"""
import glob, json, os

for f in sorted(glob.glob("data/interim/sample_*.jsonl")):
    good, bad, players = [], 0, set()
    for line in open(f):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if "pgn" in rec and "[Event " in rec["pgn"]:
                good.append(line)
                players.add(rec.get("player"))
            else:
                bad += 1
        except json.JSONDecodeError:
            bad += 1
    if bad:
        with open(f, "w") as fh:
            fh.write("\n".join(good) + "\n")
    print(f"  {os.path.basename(f)}: {len(good)} games, {len(players)} players"
          + (f"  [dropped {bad} bad lines]" if bad else ""))
