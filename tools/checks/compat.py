"""Per app: keychain path assumptions, and app-title vs the product name/URL its sign.ps1 embeds."""
import base64, json, pathlib, re, subprocess, sys

OUT = pathlib.Path(sys.argv[1])
trees = json.loads((OUT / "trees.json").read_text())


def text(app, files, path):
    info = files.get(path)
    if not info:
        return ""
    f = OUT / "blobs" / info["sha"]
    if not f.exists():
        r = subprocess.run(["gh", "api", f"repos/storytold/{app}/git/blobs/{info['sha']}"], capture_output=True, text=True, check=True)
        f.write_bytes(base64.b64decode(json.loads(r.stdout)["content"]))
    return f.read_text(encoding="utf-8", errors="replace")


for app, files in sorted(trees.items()):
    if ".github/workflows/release.yml" not in files:
        continue
    release = text(app, files, ".github/workflows/release.yml")
    title = re.search(r"app-title:\s*\"?([^\"\n]+?)\"?\s*$", release, re.M)
    sign = text(app, files, "packaging/windows/sign.ps1")
    d = re.search(r"'/d',\s*'([^']*)'", sign)
    du = re.search(r"'/du',\s*'([^']*)'", sign)
    mac = text(app, files, "packaging/macos/package.sh") + text(app, files, "packaging/macos/verify.sh")
    fixed_keychain = sorted(set(re.findall(r"[\w$/{}.-]*signing\.keychain(?:-db)?", mac)))
    title_s = title.group(1).strip() if title else "?"
    d_s = d.group(1) if d else "?"
    url_ok = du and du.group(1) == f"https://github.com/storytold/{app}"
    print(f"{app:15} app-title {title_s:18} sign.ps1 /d {d_s:18} {'same' if title_s == d_s else 'DIFFERENT':9} "
          f"/du {'repo URL' if url_ok else (du.group(1) if du else '?')}  fixed keychain path: {', '.join(fixed_keychain) or 'none'}")
