"""List each app workflow job: a shared-workflow call or a local job (with its steps' uses/run heads)."""
import collections, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent / 'pylib'))
import yaml

OUT = pathlib.Path(sys.argv[1])
trees = json.loads((OUT / "trees.json").read_text())
local = collections.defaultdict(list)
shared_calls = collections.Counter()
for app, files in sorted(trees.items()):
    for p, info in files.items():
        if not (p.startswith(".github/workflows/") and p.endswith((".yml", ".yaml"))):
            continue
        f = OUT / "blobs" / info["sha"]
        if not f.exists():
            continue
        doc = yaml.load(f.read_text(encoding="utf-8", errors="replace"), Loader=yaml.BaseLoader) or {}
        for name, job in (doc.get("jobs") or {}).items():
            if "uses" in job:
                shared_calls[job["uses"].split("@")[0].replace("storytold/craft-common-actions/", "")] += 1
                continue
            steps = []
            for s in job.get("steps", []):
                if "uses" in s:
                    steps.append("uses " + s["uses"].split("@")[0])
                elif "run" in s:
                    steps.append("run: " + s.get("name", s["run"].strip().splitlines()[0])[:70])
            local[(p.split("/")[-1], name)].append((app, steps))

print("== shared workflow calls")
for k, n in shared_calls.most_common():
    print(f"{n:3}  {k}")
print("\n== local jobs (workflow:job -> apps)")
for (wf, job), entries in sorted(local.items(), key=lambda kv: -len(kv[1])):
    print(f"\n{len(entries):3} apps  {wf}:{job}  [{', '.join(a for a, _ in entries)}]")
    for s in entries[0][1][:14]:
        print("        ", s)

