# craft-common-actions: where things stand and what's next

Last updated 2026-11-05. Upstream: `storytold/craft-common-actions`. Your fork:
`nanox333/craft-common-actions-fork`. A copy of this file, plus the helper scripts, is on the
fork's `notes/handoff` branch.

## Already merged upstream

| PR | What it does |
| --- | --- |
| #140 | `actions/import-macos-certificate`: shared macOS certificate import |
| #144 | `actions/setup-windows-signing`: shared Windows `sign.ps1` |
| #146 | Release workflow pushes the Flatpak OCI tags itself; only a stable `release`-branch build moves `stable-<arch>` (no app change needed) |
| #147 | `git-sources.yml` + `actions/check-git-sources`: the shared "git dependencies come from storytold" check |

## Open upstream PRs (yours)

| PR | State | Notes |
| --- | --- | --- |
| #136 Windows installer policy checks | CI green, CodeRabbit passed, clean | Dylan objected to app names in shared code. Reworked: made-up fixture apps, no app checkouts, `skipsLicencePage` defaults to `false` and comes only from the policy. **After my reply was posted, four more commits landed (1f55b4b) that cut the fixtures from four to two (`custom-ui`, `wixui`).** The posted reply still says "four made-up apps", so update it or add a short follow-up comment. |
| #148 No per-app lists in `release.yml` | CI green, clean | Made by another Claude session. Removes 298 lines of `<APP>_VERSION/_BUILD_DATE/_BUILD_SHA`, adds `actions/export-app-build-env` (reads the prefix from the app's `packaging/env.sh`). Also fixes materialcraft and texturecraft, which got no build version/date/sha. |
| #137 sonarcloud test fix | open | You chose to leave it open. Branch `fix/sonarcloud-test-pat-fallback` is kept for it. |

## Ready but NOT opened: the shared signing PR

Branch `feat/release-shared-signing` on the fork (commit d8b875a). Open it with:

```bash
gh pr create --repo storytold/craft-common-actions --base main --head nanox333:feat/release-shared-signing --title "Release: sign with the shared macOS import and Windows signing script" --body-file <write a body from the commit message>
```

What it does:
- The macOS release job uses `import-macos-certificate` instead of the app's `packaging/macos/import-cert.sh`. **This takes effect for all 17 apps on their next release.**
- The Windows release job and `windows-arm64.yml` run `setup-windows-signing` before `package.ps1`, so `CRAFT_SIGN_SCRIPT` is always set. Nothing changes for an app until its `package.ps1` uses it.
- `windows-arm64.yml` gets an optional `app-title` input (falls back to `app-dir`), so no caller changes.
- New test `tests/test_release_shared_signing.py`: passes, and fails against main.

Checked:
- every app's `app-title` equals the product name its own `sign.ps1` embeds;
- every app's URL is the repository URL;
- no app hard-codes a keychain path;
- all 17 app copies of `import-cert.sh` run the same `security` steps as the shared one;
- a trial merge with #148 has no conflicts.

### Real-runner smoke test (throwaway)

The branch `test/shared-signing-smoke` on the fork has
`.github/workflows/signing-smoke.yml`, which runs the shared actions the way the new
`release.yml` does, with made-up test certificates. It uses no secrets and publishes nothing.
Latest run: https://github.com/nanox333/craft-common-actions-fork/actions/runs/42059612990

- macOS import, sign and clean up: **passed**.
- Windows, with and without a test certificate: **passed**: signed, timestamped and verified, and the `App [x64].exe` name handled literally.
- macOS without a certificate: was still queued for a runner when this was written.

**Delete that branch when you're done:**

```bash
git push https://github.com/nanox333/craft-common-actions-fork.git --delete test/shared-signing-smoke
```

The one thing it can't prove is Apple's real certificate and notarization. Those steps are the same ones the app scripts run today.

## Next: one PR per app (Dylan agreed: "one PR per app for all of the actions")

Do these **after the shared signing PR merges**. The Windows change depends on it. Ideally do them
after #136 merges too, so each app gets a single PR.

Apps (17): cadcraft, craft-anything, craft-launcher, deckcraft, designcraft, effectcraft, figcraft,
filmcraft, gridcraft, lightcraft, materialcraft, pdfcraft, photocraft, soundcraft, texturecraft,
vectorcraft, wordcraft.

Each app PR:
1. **Windows signing.** In `packaging/windows/package.ps1`, replace the three
   `& (Join-Path $PSScriptRoot 'sign.ps1') ...` uses (one is in a comment) with
   `& $env:CRAFT_SIGN_SCRIPT ...`. Then delete `packaging/windows/sign.ps1`.
   - Decide what local builds do when `CRAFT_SIGN_SCRIPT` is unset: skip signing with a warning, the same as having no secrets today.
2. **macOS import.** Delete `packaging/macos/import-cert.sh`. The shared release workflow no longer runs it once the signing PR merges.
3. **git-sources.**
   - Eight apps carry the pasted job: cadcraft (`nix.yml`, `release.yml`), designcraft (`release.yml`), filmcraft (`nix.yml`), lightcraft (`nix.yml`, `release.yml`), pdfcraft (`ci.yml`), photocraft (`ci.yml`), soundcraft (`nix.yml`), vectorcraft (`release.yml`). Replace the job with `uses: storytold/craft-common-actions/.github/workflows/git-sources.yml@main`, keeping the same job id `git-sources` so `needs: git-sources` keeps working.
   - In pdfcraft's `ci.yml` the same job also runs "Windows font notice regressions". Keep that step somewhere when the job goes.
   - The other nine apps can add the job in `ci.yml`. All 18 apps pass the check today.
4. **Windows install policy** (once #136 merges). Swap the `windows-install-policy` job in `packaging-lint.yml` for `uses: .../windows-install-policy.yml@main`.
   - Apps whose wizard skips the licence page add `"skipsLicencePage": true` to `packaging/windows/install-policy.json`: deckcraft, filmcraft, soundcraft, figcraft, photocraft and vectorcraft.
   - Check lightcraft first: it has its own UI but matched the scan.
   - Re-check #136's README for its final migration rules, since its last commits changed things.

## Other ideas from the survey (not started)

Ranked by value for effort:
- **Identical files that could be shared:** `packaging/linux/postinst.sh` (16 apps; craft-launcher skips the MIME refresh), `packaging/.shellcheckrc` (16), `packaging/windows/install-policy.wxi` (13).
- **macOS DMG layout** (14 apps): `packaging/macos/dmg/generate.py` + `background.svg` + `dmg-layout.DS_Store` as a `macos-dmg` action.
- **AppImage CLI entry point:** three conventions (`--cli`, a `cli` subcommand, a symlink named `<app>-cli`). Agree one first, ideally alongside PR #105.
- **xtask Rust helpers** (`version.rs`, `ico.rs`, `stats.rs`, `layers.rs`) belong in a shared crate. Fixes that never spread: the stricter version check (only photocraft, vectorcraft, soundcraft) and a symlink-loop guard in `stats.rs` (3 different versions; 5 apps have none).
- **Per-app `package.sh` scripts** (Linux/macOS/Windows/FreeBSD): 70–87% alike; a big project.
- **Ruled out:** web cache headers (file names are content-hashed or versioned) and the FreeBSD font gate (already in `freebsd.yml`).

## Gotchas when working on this from Windows PowerShell 5.1

- Commit messages with double quotes split into separate arguments: use `git commit -F <file>`.
- `gh --jq` with double quotes inside needs `\"`, or put the query in a file (`gh api graphql -F query=@file`).
- `gh pr list --head` only matches the branch name, not `owner:branch`.
- Don't share one clone between two sessions: another session overwrote files in a shared scratch clone once. Use one clone per task.
- Helper scripts are in `tools/` on the `notes/handoff` branch (survey, drift, per-app checks). They expect a `trees.json` from `tools/survey/trees.py` in the folder you pass them.
