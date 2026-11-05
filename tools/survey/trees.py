"""Fetch each app repo's tree (path -> blob sha) and report files shared across apps."""
import json, subprocess, sys, collections, pathlib

APPS = """artcraft cadcraft craft-anything craft-launcher deckcraft designcraft effectcraft figcraft filmcraft
gridcraft lightcraft materialcraft pdfcraft photocraft soundcraft texturecraft vectorcraft wordcraft""".split()
OUT = pathlib.Path(sys.argv[1])

def gh(*args):
    return json.loads(subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=True).stdout)

trees = {}
for app in APPS:
    meta = gh(f"repos/storytold/{app}")
    branch = meta["default_branch"]
    t = gh(f"repos/storytold/{app}/git/trees/{branch}?recursive=1")
    trees[app] = {e["path"]: {"sha": e["sha"], "size": e.get("size", 0)} for e in t["tree"] if e["type"] == "blob"}
    trees[app]["__meta__"] = {"sha": branch, "size": len(t["tree"]), "truncated": t.get("truncated"), "pushed": meta["pushed_at"], "archived": meta["archived"]}
    print(app, branch, len(trees[app]), "truncated" if t.get("truncated") else "", file=sys.stderr)
(OUT / "trees.json").write_text(json.dumps(trees))

paths = collections.defaultdict(dict)
for app, files in trees.items():
    for p, info in files.items():
        if p == "__meta__":
            continue
        paths[p][app] = info["sha"]

skip_prefix = ("assets/", "src/", "crates/", "tests/fixtures", "i18n/", "locales/", "docs/screenshots")
rows = []
for p, by_app in paths.items():
    if len(by_app) < 4 or p.startswith(skip_prefix):
        continue
    variants = collections.Counter(by_app.values())
    rows.append((len(by_app), len(variants), p, variants.most_common(1)[0][1]))
rows.sort(key=lambda r: (-r[0], r[2]))
with open(OUT / "shared.txt", "w") as f:
    for n, v, p, top in rows:
        f.write(f"{n:3} apps {v:3} variants (largest group {top:2})  {p}\n")
