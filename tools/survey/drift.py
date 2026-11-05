"""Download candidate shared files, normalise app names, and measure real drift."""
import base64, collections, concurrent.futures as cf, difflib, json, pathlib, re, subprocess, sys

OUT = pathlib.Path(sys.argv[1])
trees = json.loads((OUT / "trees.json").read_text())
CAND = re.compile(r"^(packaging/|xtask/src/(ico|version|layers|stats)\.rs$|xtask/Cargo\.toml$|\.github/|\.cargo/config\.toml$|"
                  r"\.config/nextest\.toml$|rustfmt\.toml$|clippy\.toml$|\.gitattributes$|docs/brand/LICENSE-brand\.txt$|"
                  r"sonar-project\.properties$|SECURITY\.md$|docs/releasing\.md$|flake\.nix$)")
BINARY = (".png", ".tiff", ".DS_Store", ".ico", ".icns")
CACHE = OUT / "blobs"; CACHE.mkdir(exist_ok=True)

def name_pattern(app):
    if app.startswith("craft-"):
        core = app[len("craft-"):]
        return re.compile(rf"craft[\s_.-]?{re.escape(core)}", re.I)
    core = app[: -len("craft")]
    return re.compile(rf"{re.escape(core)}[\s_.-]?craft", re.I)

def blob(app, sha):
    f = CACHE / sha
    if not f.exists():
        r = subprocess.run(["gh", "api", f"repos/storytold/{app}/git/blobs/{sha}"], capture_output=True, text=True, check=True)
        f.write_bytes(base64.b64decode(json.loads(r.stdout)["content"]))
    return f.read_bytes().decode("utf-8", "replace")

jobs = {}
for app, files in trees.items():
    for p, info in files.items():
        if p != "__meta__" and CAND.match(p) and not p.endswith(BINARY) and info["size"] < 400_000:
            jobs[(app, p)] = info["sha"]
with cf.ThreadPoolExecutor(12) as ex:
    texts = dict(zip(jobs, ex.map(lambda k: blob(k[0], jobs[k]), jobs)))

by_path = collections.defaultdict(dict)
for (app, p), text in texts.items():
    by_path[p][app] = name_pattern(app).sub("APP", text)

report = []
for p, copies in by_path.items():
    if len(copies) < 4:
        continue
    groups = collections.defaultdict(list)
    for app, t in copies.items():
        groups[t].append(app)
    ranked = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    canon = ranked[0][0]
    canon_lines = canon.splitlines()
    sims = sorted(difflib.SequenceMatcher(None, canon_lines, t.splitlines()).ratio() for t in copies.values())
    lines = len(canon.splitlines())
    report.append({"path": p, "apps": len(copies), "variants": len(groups), "largest": len(ranked[0][1]),
                   "lines": lines, "min_sim": round(sims[0], 3), "median_sim": round(sims[len(sims) // 2], 3),
                   "groups": [sorted(a) for _, a in ranked]})
report.sort(key=lambda r: (-r["apps"], r["path"]))
(OUT / "drift.json").write_text(json.dumps(report, indent=1))
for r in report:
    print(f'{r["apps"]:3} apps {r["variants"]:3} norm-variants largest {r["largest"]:2} ~{r["lines"]:4} lines '
          f'sim min {r["min_sim"]:.2f} med {r["median_sim"]:.2f}  {r["path"]}')
