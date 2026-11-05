# Helper scripts

Working tools from the 2026-11-05 survey of the Craft apps. Not production code.

- `survey/trees.py OUT_DIR`: fetches every app's file tree (needs `gh`), writes `trees.json` and `shared.txt`. Run it first; the others read `OUT_DIR/trees.json` and cache file contents in `OUT_DIR/blobs`.
- `survey/drift.py OUT_DIR`: per shared file, how many real variants there are once app names are swapped out.
- `survey/diffs.py OUT_DIR MAXLINES PATH...`: each variant's diff from the most common one.
- `survey/jobs.py`, `survey/steps.py OUT_DIR 'step name regex'`: app workflow jobs that run on their own, and the text of matching steps.
- `survey/licence_scan.py`: which apps' Windows wizards skip the licence page.
- `survey/envnames.py`, `survey/parity.py`: build-variable names; git-sources parity check.
- `checks/adoption.py`, `checks/compat.py`, `checks/importcert_exports.py`: per-app checks for switching to the shared signing actions.
- `checks/prsummary.py`: prints a PR's reviews, threads and comments from a GraphQL dump.
- `fixtures/make_fixtures.py`: how the #136 fixture apps were first generated from pinned app sources.
- `smoke-test/signing-smoke.yml`: the throwaway real-runner test of the shared signing actions.

`survey/jobs.py` and `steps.py` need PyYAML; on Python 3.14 use `pip install --only-binary :all: --target <dir> pyyaml==6.0.3`.
