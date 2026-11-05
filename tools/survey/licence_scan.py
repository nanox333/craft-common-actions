"""Which apps' Windows wizards skip the licence page (WelcomeDlg Next -> InstallDirDlg and back)?"""
import base64, json, pathlib, re, subprocess, sys

OUT = pathlib.Path(sys.argv[1])
trees = json.loads((OUT / "trees.json").read_text())
LISTED = {"deckcraft", "filmcraft", "soundcraft"}
for app, files in sorted(trees.items()):
    if "packaging/windows/install-policy.json" not in files:
        continue
    text = ""
    for path, info in files.items():
        if path.startswith("packaging/windows/") and path.endswith(".wxs"):
            blob = OUT / "blobs" / info["sha"]
            if not blob.exists():
                r = subprocess.run(["gh", "api", f"repos/storytold/{app}/git/blobs/{info['sha']}"], capture_output=True, text=True, check=True)
                blob.write_bytes(base64.b64decode(json.loads(r.stdout)["content"]))
            text += blob.read_text(encoding="utf-8", errors="replace")
    wixui = re.search(r'<ui:WixUI Id="(\w+)"', text)
    forward = re.search(r'Dialog="WelcomeDlg" Control="Next" Event="NewDialog" Value="InstallDirDlg"', text)
    back = re.search(r'Dialog="InstallDirDlg" Control="Back" Event="NewDialog" Value="WelcomeDlg"', text)
    skips = bool(forward and back)
    print(f"{app:15} wizard {wixui.group(1) if wixui else 'own UI':18} skips licence page: {str(skips):5}  "
          f"on the old name list: {str(app in LISTED):5}{'  <-- differs' if skips != (app in LISTED) else ''}")
