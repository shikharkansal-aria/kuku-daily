"""Parse Kuku microdrama screenplays into structured JSON.

Usage: python3 -I tools/parse_scripts.py input/scripts outputs/parsed

Writes:
  episodes.jsonl      one JSON object per episode (header, scenes, timed blocks)
  condensed/epNNN.txt dialogue + action + sound only (camera dropped), for cheap reading
  stats.csv           per-episode duration, scene count, block counts
"""
import csv
import json
import re
import sys
from pathlib import Path

TS = r"(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?"
BLOCK_RE = re.compile(r"^\*\*(?P<label>[^*]+?):?\*\*\s*$")
TIME_RE = re.compile(rf"Start:\s*\({TS}\)\s*\|\s*End:\s*\({TS}\)")
SCENE_RE = re.compile(r"^SCENE\s+(\d+)", re.I)
HDR_RE = re.compile(r"^(EPISODE NUMBER|EPISODE LOGLINE|CONTINUITY NOTES):\s*(.*)$")
FIELD_RE = re.compile(r"^(Scene heading|Scene start|Scene end):\s*(.*)$", re.I)
MARKER_RE = re.compile(r"-{3}\s*SCRIPT (START|END)\s*-{3}", re.I)
DELIVERY = {"O.S", "V.O", "CONT'D", "CONT’D", "OS", "VO", "OFF", "ON PHONE"}


def secs(m, i):
    mm, ss, frac = m.group(i), m.group(i + 1), m.group(i + 2) or "0"
    return int(mm) * 60 + int(ss) + float("0." + frac)


def parse_ts(s):
    m = re.search(TS, s)
    return secs(m, 1) if m else None


def parse(path: Path):
    ep = {"file": path.name, "scenes": []}
    m = re.search(r"episode-(\d+)", path.name)
    ep["episode"] = int(m.group(1)) if m else None
    lines = path.read_text(encoding="utf-8").splitlines()
    scene, block = None, None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        h = HDR_RE.match(line)
        if h:
            ep[h.group(1).lower().replace(" ", "_")] = h.group(2)
            continue
        s = SCENE_RE.match(line)
        if s:
            scene = {"scene": int(s.group(1)), "blocks": []}
            ep["scenes"].append(scene)
            block = None
            continue
        f = FIELD_RE.match(line)
        if f and scene is not None:
            key = f.group(1).lower().replace(" ", "_")
            scene[key] = parse_ts(f.group(2)) if key != "scene_heading" else f.group(2)
            continue
        b = BLOCK_RE.match(line)
        if b and scene is not None:
            label = b.group("label").strip()
            kind = "dialogue"
            speaker = label.split("(")[0].strip()
            parens = [p.strip() for p in re.findall(r"\(([^)]*)\)", label)]
            delivery = [p for p in parens if p.upper().rstrip(".") in DELIVERY]
            cues = [p for p in parens if p not in delivery]
            cue = "; ".join(cues) or None
            if speaker in ("CAMERA", "ACTION", "SOUND FX"):
                kind = speaker.lower().replace(" ", "_")
                speaker = None
            block = {"type": kind, "speaker": speaker, "cue": cue, "delivery": delivery or None,
                     "start": None, "end": None, "text": ""}
            scene["blocks"].append(block)
            continue
        t = TIME_RE.search(line)
        if t and block is not None and block["start"] is None:
            block["start"], block["end"] = secs(t, 1), secs(t, 4)
            continue
        line = MARKER_RE.sub("", line).strip()
        if block is not None and line:
            block["text"] = (block["text"] + " " + line).strip()
    return ep


def fmt(t):
    return "--:--" if t is None else f"{int(t // 60):02d}:{t % 60:05.2f}"


def main(src, dst):
    src, dst = Path(src), Path(dst)
    (dst / "condensed").mkdir(parents=True, exist_ok=True)
    rows = []
    with open(dst / "episodes.jsonl", "w", encoding="utf-8") as out:
        for p in sorted(src.glob("episode-*.txt")):
            ep = parse(p)
            out.write(json.dumps(ep, ensure_ascii=False) + "\n")
            blocks = [b for s in ep["scenes"] for b in s["blocks"]]
            ends = [b["end"] for b in blocks if b["end"] is not None]
            missing = sum(1 for b in blocks if b["start"] is None)
            rows.append({
                "episode": ep["episode"], "duration_s": round(max(ends), 1) if ends else None,
                "scenes": len(ep["scenes"]),
                "dialogue": sum(b["type"] == "dialogue" for b in blocks),
                "action": sum(b["type"] == "action" for b in blocks),
                "camera": sum(b["type"] == "camera" for b in blocks),
                "sound_fx": sum(b["type"] == "sound_fx" for b in blocks),
                "untimed_blocks": missing,
            })
            lines = [f"EPISODE {ep['episode']}: {ep.get('episode_logline', '')}",
                     f"CONTINUITY: {ep.get('continuity_notes', '')}"]
            for s in ep["scenes"]:
                lines.append(f"\n[SCENE {s['scene']}] {s.get('scene_heading', '')} {fmt(s.get('scene_start'))}-{fmt(s.get('scene_end'))}")
                for b in s["blocks"]:
                    if b["type"] == "camera":
                        continue
                    who = b["speaker"] or b["type"].upper()
                    cue = f" ({b['cue']})" if b["cue"] else ""
                    lines.append(f"{fmt(b['start'])} {who}{cue}: {b['text']}")
            (dst / "condensed" / f"ep{ep['episode']:03d}.txt").write_text("\n".join(lines) + "\n")
    with open(dst / "stats.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"parsed {len(rows)} episodes -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
