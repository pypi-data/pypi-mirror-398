# basecollab (Rust + PyO3) — maintainer notes

This repo is a Rust library exposing a Python extension module that scans a Git repository for `TODO` followed by `:` or ` :` lines and enriches matches with `git blame` metadata.

The code is primarily in [`src/lib.rs`](src/lib.rs:1).

## What it does

- Walks directories (default: `.`) and scans text files for the regex `TODO\s*:`.
- Skips binary files, large files (default 10MB), excluded extensions and excluded dirs.
- Skips Git-untracked and Git-ignored files (so TODOs outside version control don’t show up).
- For each matching line, attaches blame data: commit id, author, timestamp.

Data model: [`TodoItem`](src/lib.rs:15).

## Key functions (Rust)

- Directory traversal + orchestration: [`scan_directories()`](src/lib.rs:187)
- Per-file scanning: [`scan_file()`](src/lib.rs:138)
- Git blame info: [`git_blame_line()`](src/lib.rs:54)
- Git tracking filter (respects `.gitignore` + skips untracked): [`is_git_tracked()`](src/lib.rs:165)

## Python entrypoint

Exported function: [`scan_py()`](src/lib.rs:216)

Important details:
- `scan_py()` discovers the Git workdir root via `Repository::discover(".")` and uses it as the `repo_path` for blame/tracking.
- `scan_py()` also normalizes `selected_dirs` so scanning is rooted at the repo root even when Python is executed from a different current working directory.

Output format (Python)
- `scan_py()` returns a JSON list of **section nodes**, grouped by repo root folders (top-level directories).
- Each node looks like: `{ "type": "section", "name": "./frontend", "children": [TodoItem, ...] }`.
- Root-level files are grouped under the section name `"./"`.

Module name is `basecollab`: [`basecollab()`](src/lib.rs:276).

## Build & test (host)

Rust tests:
```bash
# Make sure to build_wheel before running python so its up to date with most recent rust code changes.
make build_wheel rust_test python_test
```

Notes:
- Rust runs tests in parallel by default; tests are annotated with `serial_test` to avoid interleaved output: see [`mod tests`](src/lib.rs:285) and dev dependency in [`Cargo.toml`](Cargo.toml:1).

Python build (local):
```bash
python -m venv .venv
source .venv/bin/activate
pip install maturin
maturin develop
python -c "import basecollab; print(basecollab.scan_py(None,None,None,None))"
```

Packaging config: [`pyproject.toml`](pyproject.toml:1).

## Publishing to PyPI / TestPyPI

Maturin needs credentials:
- Preferred (maturin >=1.10): `MATURIN_PYPI_TOKEN=<pypi token>`
- Legacy (still works in some setups): `MATURIN_USERNAME=__token__` + `MATURIN_PASSWORD=<pypi token>`

Gotchas:
- If this is the **first upload** for a new project name, a **project-scoped** token may fail; use an **account-wide** token for the initial publish.
- A `403 Invalid or non-existent authentication information` almost always means the token is invalid/revoked, or you're using a token from the wrong index (PyPI vs TestPyPI).

Recommended: use environment variables (don’t commit tokens).

If you use docker-compose, put tokens in a local `.env` file (not committed) and recreate the container so they’re injected:
```bash
echo 'PYPI_TOKEN=pypi-...' >> .env
echo 'TEST_PYPI_TOKEN=pypi-...' >> .env
docker compose up -d --force-recreate
```

Then:
- TestPyPI (rehearsal): `make publish_wheel_dry`
- PyPI (real): `make publish_wheel`

## Docker (manylinux wheel + runtime)

This repo ships a multi-stage Dockerfile:

- **builder stage** (`ghcr.io/pyo3/maturin`) builds a manylinux wheel.
- **runtime stage** (`python:3.11-slim`) installs the built wheel.

See [`Dockerfile`](Dockerfile:1).

### Build image
```bash
docker build -t basecollab:latest .
```

### Run a scan against your host repo (no need to keep a long-running container)
```bash
docker run --rm -v "$PWD":/data -w /data basecollab:latest \
  python -c "import basecollab; print(basecollab.scan_py(None,None,None,None))"
```

## docker-compose workflow (fast iteration)

Compose uses the repo’s Dockerfile and mounts the repo into the container:
[`docker-compose.yml`](docker-compose.yml:1).

This enables quick rebuilds of the wheel **inside the running container** (without rebuilding the whole image), then reinstalling the wheel.

Make targets are in [`Makefile`](Makefile:1).

### Typical loop

1) Build + start compose service:
```bash
make build
```

2) After editing Rust code (ex: [`src/lib.rs`](src/lib.rs:1)), rebuild + reinstall wheel inside the container:
```bash
make build_wheel
```

If Python scan returns `[]` inside the container but Rust finds TODOs, it’s usually Git refusing the mounted repo as “dubious ownership”. Fix once:
```bash
make git_safe
```

3) Compare outputs:
```bash
make python_test
make rust_test
```

## Notes / gotchas

- `.gitignore` behavior: since we skip untracked/ignored files in [`is_git_tracked()`](src/lib.rs:165), you won’t see TODOs in untracked scratch files.
- manylinux vs “local” wheels:
  - manylinux enforcement can fail if you build on a non-manylinux base (GLIBC symbol issues). Use the builder stage in [`Dockerfile`](Dockerfile:1) to produce manylinux wheels.
  - fast iteration in compose builds a wheel for the *container platform* (no manylinux enforcement).
- maturin may require `patchelf`; runtime stage installs `maturin[patchelf]` in [`Dockerfile`](Dockerfile:38).
