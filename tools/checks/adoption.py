"""Per app: what switching to the shared signing actions and git-sources.yml would change."""
import json, pathlib, re, sys

OUT = pathlib.Path(sys.argv[1])
trees = json.loads((OUT / "trees.json").read_text())


def text(files, path):
    info = files.get(path)
    if not info:
        return None
    f = OUT / "blobs" / info["sha"]
    return f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""


for app, files in sorted(trees.items()):
    if ".github/workflows/release.yml" not in files:
        continue
    mac = text(files, "packaging/macos/package.sh") or ""
    ps1 = text(files, "packaging/windows/package.ps1") or ""
    mac_vars = sorted(set(re.findall(r"\b(MACOS_SIGN_IDENTITY|MACOS_KEYCHAIN)\b", mac)))
    sign_calls = [line.strip() for line in ps1.splitlines() if re.search(r"sign\.ps1", line) and not line.strip().startswith("#")]
    git_sources = [p.split("/")[-1] for p in files if p.startswith(".github/workflows/")
                   and "Git dependencies come from storytold" in (text(files, p) or "")]
    print(f"{app:15} mac package.sh reads {','.join(mac_vars) or 'NEITHER':34} "
          f"sign.ps1 calls in package.ps1: {len(sign_calls)}  git-sources job in: {','.join(git_sources) or '-'}")
    for call in sign_calls[:2]:
        print(f"{'':17}{call[:140]}")
