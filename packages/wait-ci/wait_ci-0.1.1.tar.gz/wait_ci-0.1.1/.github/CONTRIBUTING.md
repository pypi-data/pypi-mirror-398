# Contributing to `wait-ci`

`wait-ci` is packaged with [`uv`](https://github.com/astral-sh/uv) + `hatch-vcs`. Everything from local development to PyPI releases flows through those tools. This document covers:

- Spinning up a dev environment and running the CLI
- Common make commands for development and testing
- How versioning works (git tags) and how to cut/publish a release

---

## 1. Getting started

```bash
# 1) Clone and enter the repo
git clone git@github.com:mikegoelzer/wait-ci.git
cd wait-ci

# 2) Set up dev environment (creates .venv, installs dependencies)
make install-dev

# 3) Run tests
make test

# 4) Run the CLI locally
uv run --no-sync wait-ci --help
```

### Note on using editable local installs

If you have an editable local install of `curvpyutils`, you need to edit the Makefile to fix the relative path to the local package (look near the top for the line that starts with `LOCAL_CURVPYUTILS_PATH`).

---

## 2. Common Make Commands

### Development Environment

- **`make install-dev`** - Set up full development environment with editable installs
  Creates .venv, installs package + dev dependencies, and links to local curvpyutils if available

- **`make install-min`** - Minimal install (package only, no dev tools)
  Just installs the wait-ci package in editable mode

- **`make install`** - Alias for `install-min`

- **`make test`** - Run pytest test suite
  Uses `--no-sync` to preserve editable local package links

- **`make clean`** - Remove build artifacts, cache files, and virtual environment
  Cleans up __pycache__, dist/, .pytest_cache, .ruff_cache, etc.

### Versioning

- **`make bump-patch`** - Bump patch version (e.g., 1.0.0 → 1.0.1)
  Creates a local git tag only (does not push)

- **`make bump-minor`** - Bump minor version (e.g., 1.0.0 → 1.1.0)
  Creates a local git tag only (does not push)

- **`make bump-major`** - Bump major version (e.g., 1.0.0 → 2.0.0)
  Creates a local git tag only (does not push)

### Publishing to PyPI

- **`make publish-patch`** - Run tests, bump patch, push tag, create GitHub release
  One command to handle patch releases end-to-end

- **`make publish-minor`** - Run tests, bump minor, push tag, create GitHub release
  One command to handle minor releases end-to-end

- **`make publish-major`** - Run tests, bump major, push tag, create GitHub release
  One command to handle major releases end-to-end

---

## 3. Versioning & release process

`wait-ci` uses `hatch-vcs` to derive its version number directly from git tags that match the pattern `wait-ci-v<MAJOR>.<MINOR>.<PATCH>`. No files need manual editing—bumping the version = creating the right tag.

### Easy way: Use make commands

```bash
# make sure you're on an up-to-date main
git switch main
git pull origin main

# publish a patch release (runs tests, bumps version, pushes tag, creates release)
make publish-patch

# or for minor/major releases:
# make publish-minor
# make publish-major
```

The `publish-*` targets will:
1. Run the test suite
2. Bump the version and create a git tag
3. Push the tag to GitHub
4. Create a GitHub Release (which triggers PyPI publishing via CI)

### Manual way: Step by step

If you prefer more control:

```bash
# 1) Bump version locally
make bump-patch  # or bump-minor, bump-major

# 2) Push the tag
git push origin wait-ci-v$(uv run --no-sync python scripts/bump_version.py --show-latest)

# 3) Create GitHub Release
gh release create wait-ci-v${NEW_VERSION} \
  --title "wait-ci-v${NEW_VERSION}" \
  --notes "Describe highlights here."
```

Publishing the GitHub Release triggers `.github/workflows/release.yml`, which:
- Checks out the repo
- Uses `uv build` to produce sdists/wheels from the tagged commit
- Uploads the artifacts to PyPI using trusted publishing (OIDC), so no secrets are needed

Monitor the GitHub Actions run. When it finishes green, verify on PyPI:
```bash
pip install --upgrade wait-ci
```

If something goes wrong, delete the GitHub Release (which also deletes the tag), fix the issue, re-tag, and repeat the steps above.

---

## 4. Summary checklist

1. Clone + `make install-dev`
2. Develop / test with `uv run --no-sync wait-ci`, `make test`, etc.
3. To release: `make publish-patch` (or `publish-minor`/`publish-major`)

Thanks for helping improve `wait-ci`!
