"""What each app's packaging/macos/import-cert.sh exports or does beyond importing the certificate."""
import json, pathlib, re, sys

OUT = pathlib.Path(sys.argv[1])
trees = json.loads((OUT / "trees.json").read_text())
for app, files in sorted(trees.items()):
    info = files.get("packaging/macos/import-cert.sh")
    if not info:
        continue
    text = (OUT / "blobs" / info["sha"]).read_text(encoding="utf-8", errors="replace")
    exported = sorted(set(re.findall(r"^\s*(?:echo|printf)[^\n]*?\b([A-Z][A-Z0-9_]+)=[^\n]*>>\s*\"?\$\{?GITHUB_(?:ENV|OUTPUT)", text, re.M)))
    security = sorted(set(re.findall(r"\bsecurity\s+([a-z-]+)", text)))
    print(f"{app:15} exports {','.join(exported) or '-':40} security subcommands: {' '.join(security)}")
