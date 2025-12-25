# Releasing `telegram-dsl`

This project uses `setuptools-scm`, so the package version is derived from git tags of the form `vX.Y.Z`.

Goal: a single, local, manual trigger that produces a consistent version across:
- git tag
- GitHub Release
- PyPI distribution metadata

## One command (the only supported flow)

1. Ensure you’re on the commit you want to release and your working tree is clean.
   You must be on the `main` branch (releases from other branches are refused).
2. Run:

`make release VERSION=0.1.0`

That command:
- refuses to create a tag that already exists
- refuses to create a tag older than (or equal to) the latest existing `v*` tag
- creates an **annotated** tag `v0.1.0`
- pushes the tag to `origin`

Pushing the tag triggers `.github/workflows/release.yml`, which:
- runs tests
- builds sdist/wheel
- validates artifacts (`twine check`)
- creates a GitHub Release for the tag and attaches the artifacts
- publishes the same artifacts to PyPI (via Trusted Publishing)

## PyPI setup (Trusted Publishing)

The workflow uses `pypa/gh-action-pypi-publish` without a password, which requires configuring PyPI Trusted Publishing for:
- GitHub repo: `ciurlaro/telegram-dsl`
- Workflow: `.github/workflows/release.yml`

If PyPI currently contains older releases you don’t care about, you must handle that in PyPI’s UI (or by deleting/yanking releases) before trying to “restart” at `0.1.0`.

## Notes

- Tags are the source of truth for the version; do not create tags from GitHub Actions.
