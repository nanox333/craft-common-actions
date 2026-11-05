"""Turn the four pinned app installer sources into made-up fixture apps for craft-common-actions.

Mechanical: each app's display name, WiX id prefix and lowercase id become a fixture's, URLs point at
example.invalid, the manufacturer is neutral and every GUID is new (no fixture carries a real app's
upgrade identity). Run once; the output is committed, this script is not.
"""
import json, pathlib, re, struct, sys, uuid, zlib

SRC = pathlib.Path(sys.argv[1]); POLICIES = pathlib.Path(sys.argv[2]); OUT = pathlib.Path(sys.argv[3])

# source app -> (fixture directory, display name / id prefix, lowercase id, what it covers)
FIXTURES = {
    "effectcraft": ("custom-ui", "FixtureCustomUi", "fixturecustomui"),
    "filmcraft": ("skips-licence", "FixtureSkipsLicence", "fixtureskipslicence"),
    "vectorcraft": ("localized", "FixtureLocalized", "fixturelocalized"),
    "photocraft": ("file-associations", "FixtureAssociations", "fixtureassociations"),
}
GUID = re.compile(r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}")


def rename(text, app, display, lower, guids):
    core = app[: -len("craft")]
    text = re.sub(r"https://getartcraft\.com/apps/" + app, f"https://example.invalid/{lower}", text)
    text = text.replace(f"https://github.com/storytold/{app}/issues", f"https://example.invalid/{lower}/issues")
    text = text.replace("https://discord.gg/artcraft", "https://example.invalid/help")
    text = text.replace("Learning Machines LLC", "craft-common-actions test fixture")
    text = text.replace(core.capitalize() + "Craft", display)   # EffectCraft
    text = text.replace(core.capitalize() + "craft", display)   # Effectcraft (WiX id prefix, ProgIds)
    text = text.replace(app, lower)                             # effectcraft (files, App Paths, ids)
    text = GUID.sub(lambda m: guids.setdefault(m.group(0).upper(), str(uuid.uuid4()).upper()), text)
    leftover = re.findall(rf"(?i){core}[\s_.-]?craft", text)
    if leftover:
        raise SystemExit(f"{app}: unreplaced {leftover}")
    return text


def tiny_ico():
    # One 16x16 PNG entry: enough for WiX to embed as the product icon.
    raw = b"".join(b"\x00" + b"\x2b\x6c\xb0\xff" * 16 for _ in range(16))
    chunk = lambda kind, data: struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    return struct.pack("<HHH", 0, 1, 1) + struct.pack("<BBBBHHII", 16, 16, 0, 0, 1, 32, len(png), 22) + png


OUT.mkdir(parents=True, exist_ok=True)
(OUT / "fixture.ico").write_bytes(tiny_ico())
for app, (folder, display, lower) in FIXTURES.items():
    guids = {}
    target = OUT / folder / "packaging/windows"
    target.mkdir(parents=True, exist_ok=True)
    for source in sorted((SRC / app).iterdir()):
        if source.name == "test-legacy-fixture.ps1":
            continue
        name = source.name.replace(app, lower)
        text = source.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        (target / name).write_text(rename(text, app, display, lower, guids), encoding="utf-8", newline="\n")
    policy = json.loads(rename((POLICIES / f"{app}.json").read_text(encoding="utf-8-sig"), app, display, lower, guids))
    policy["icon"] = "../fixture.ico"
    if app == "filmcraft":
        policy["skipsLicencePage"] = True
    (target / "install-policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{folder}: {display} ({lower}), {len(guids)} new GUIDs, files: {sorted(p.name for p in target.iterdir())}")
