"""For each given path: the variant groups and each variant's diff from the largest group (app names normalised)."""
import collections, difflib, json, pathlib, re, sys

OUT = pathlib.Path(sys.argv[1]); MAXLINES = int(sys.argv[2]); PATHS = sys.argv[3:]
trees = json.loads((OUT / "trees.json").read_text())

def name_pattern(app):
    if app.startswith("craft-"):
        return re.compile(rf"craft[\s_.-]?{re.escape(app[6:])}", re.I)
    return re.compile(rf"{re.escape(app[:-5])}[\s_.-]?craft", re.I)

for p in PATHS:
    groups = collections.defaultdict(list)
    for app, files in trees.items():
        info = files.get(p)
        if info and (OUT / "blobs" / info["sha"]).exists():
            text = (OUT / "blobs" / info["sha"]).read_text(encoding="utf-8", errors="replace")
            groups[name_pattern(app).sub("APP", text)].append(app)
    ranked = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    print(f"\n######## {p}: {len(ranked)} variants")
    canon, canon_apps = ranked[0]
    print(f"== canonical ({len(canon_apps)}): {', '.join(sorted(canon_apps))}")
    for text, apps in ranked[1:]:
        diff = list(difflib.unified_diff(canon.splitlines(), text.splitlines(), lineterm="", n=0))[2:]
        print(f"-- variant ({len(apps)}): {', '.join(sorted(apps))}  [{len(diff)} diff lines]")
        for line in diff[:MAXLINES]:
            print("   " + line[:150])
