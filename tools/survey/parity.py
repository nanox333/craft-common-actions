"""Run the new check and the apps' original inline check on every app's real Cargo.lock/config."""
import base64, json, os, pathlib, subprocess, sys, tempfile, tomllib

OUT = pathlib.Path(sys.argv[1]); SCRIPT = sys.argv[2]
trees = json.loads((OUT / "trees.json").read_text())


def original(root):
    # The inline script's two Python checks, verbatim apart from the working directory.
    if not (root / "Cargo.lock").exists():
        return 1
    for path in (".cargo/config", ".cargo/config.toml"):
        p = root / path
        if not p.exists():
            continue
        config = tomllib.load(open(p, "rb"))
        replaced = [n for n, s in config.get("source", {}).items() if isinstance(s, dict) and "replace-with" in s]
        if replaced or "patch" in config or "paths" in config:
            return 1
    lock = tomllib.load(open(root / "Cargo.lock", "rb"))
    bad = sorted({p["source"] for p in lock.get("package", []) if p.get("source", "").startswith("git+")
                  and not p["source"].startswith("git+https://github.com/storytold/")})
    return 1 if bad else 0


stub = pathlib.Path(tempfile.mkdtemp()) / "cargo.bat"
stub.write_text("@exit /b 0\r\n")
for app, files in sorted(trees.items()):
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        gits = 0
        for name in ("Cargo.lock", ".cargo/config.toml", ".cargo/config"):
            info = files.get(name)
            if not info:
                continue
            r = subprocess.run(["gh", "api", f"repos/storytold/{app}/git/blobs/{info['sha']}"], capture_output=True, text=True, check=True)
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_bytes(base64.b64decode(json.loads(r.stdout)["content"]))
        if (root / "Cargo.lock").exists():
            gits = sum(1 for p in tomllib.load(open(root / "Cargo.lock", "rb")).get("package", []) if p.get("source", "").startswith("git+"))
        new = subprocess.run([sys.executable, SCRIPT, "--directory", d], env=dict(os.environ, CARGO=str(stub)), capture_output=True, text=True)
        old = original(root)
        same = "same" if (new.returncode == 0) == (old == 0) else "DIFFERENT"
        detail = new.stdout.strip().splitlines()[-1] if new.stdout.strip() else new.stderr.strip()[-120:]
        print(f"{app:15} git deps {gits:3}  original {'pass' if old == 0 else 'FAIL'}  new {'pass' if new.returncode == 0 else 'FAIL'}  {same}  | {detail}")
