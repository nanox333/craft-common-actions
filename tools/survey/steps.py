"""Print the run: body of every workflow step whose name matches, grouped by normalised text."""
import collections, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent / "pylib"))
import yaml

OUT = pathlib.Path(sys.argv[1]); NAME = re.compile(sys.argv[2], re.I)
trees = json.loads((OUT / "trees.json").read_text())
groups = collections.defaultdict(list)
for app, files in sorted(trees.items()):
    pat = re.compile(rf"{re.escape(app[:-5])}[\s_.-]?craft" if not app.startswith("craft-") else rf"craft[\s_.-]?{re.escape(app[6:])}", re.I)
    for p, info in files.items():
        if not p.startswith(".github/workflows/"):
            continue
        f = OUT / "blobs" / info["sha"]
        if not f.exists():
            continue
        doc = yaml.load(f.read_text(encoding="utf-8", errors="replace"), Loader=yaml.BaseLoader) or {}
        for jn, job in (doc.get("jobs") or {}).items():
            for s in job.get("steps", []) or []:
                if NAME.search(s.get("name", "")) and "run" in s:
                    groups[pat.sub("APP", s["run"])].append(f"{app}:{p.split('/')[-1]}:{jn}")
for text, where in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print(f"==== {len(where)}: {', '.join(where)}\n{text}")
