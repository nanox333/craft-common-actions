"""Which version/date/sha variables does each app's packaging read, and does release.yml set them?"""
import base64, json, pathlib, re, subprocess, sys

OUT = pathlib.Path(sys.argv[1]); RELEASE = pathlib.Path(sys.argv[2]).read_text()
trees = json.loads((OUT / "trees.json").read_text())
set_in_release = set(re.findall(r"^\s+([A-Z0-9_]+_(?:VERSION|BUILD_DATE|BUILD_SHA)):", RELEASE, re.M))
NAME = re.compile(r"\$\{?([A-Z][A-Z0-9_]*_(?:VERSION|BUILD_DATE|BUILD_SHA))\b|env!?\(\s*\"([A-Z][A-Z0-9_]*_(?:VERSION|BUILD_DATE|BUILD_SHA))\"|option_env!\(\"([A-Z][A-Z0-9_]*_(?:VERSION|BUILD_DATE|BUILD_SHA))\"")


def blob(app, sha):
    f = OUT / "blobs" / sha
    if not f.exists():
        r = subprocess.run(["gh", "api", f"repos/storytold/{app}/git/blobs/{sha}"], capture_output=True, text=True, check=True)
        f.write_bytes(base64.b64decode(json.loads(r.stdout)["content"]))
    return f.read_text(encoding="utf-8", errors="replace")


for app, files in sorted(trees.items()):
    if ".github/workflows/release.yml" not in files:
        continue
    read = {}
    for path, info in files.items():
        if path == "__meta__" or info["size"] > 300_000:
            continue
        if not (path.startswith("packaging/") or path.endswith("build.rs") or path.startswith("xtask/src/")):
            continue
        if not path.endswith((".sh", ".ps1", ".rs", ".py")):
            continue
        for m in NAME.finditer(blob(app, info["sha"])):
            name = next(g for g in m.groups() if g)
            if name not in ("CARGO_PKG_VERSION", "RUSTC_VERSION"):
                read.setdefault(name, set()).add(path)
    prefixes = sorted({n.rsplit("_", 2 if n.endswith(("BUILD_DATE", "BUILD_SHA")) else 1)[0] for n in read})
    env_sh = next((files[p] for p in ("packaging/env.sh", "packaging/common.sh") if p in files), None)
    declared = re.search(r'VERSION="\$\{([A-Z0-9_]+)_VERSION:-', blob(app, env_sh["sha"])) if env_sh else None
    missing = sorted(n for n in read if n not in set_in_release and n.split("_")[0] not in ("CARGO", "CRAFT"))
    print(f"{app:15} prefixes read: {', '.join(prefixes) or '-':40} env.sh declares: {declared.group(1) if declared else '-':18} "
          f"read but not set by release.yml: {', '.join(missing) or 'none'}")
