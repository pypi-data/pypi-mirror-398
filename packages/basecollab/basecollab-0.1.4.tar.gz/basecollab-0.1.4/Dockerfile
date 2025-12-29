# NOTE: maturin images are tagged with a leading "v" (e.g. v1.4.0) or "latest".
FROM ghcr.io/pyo3/maturin:latest AS builder

WORKDIR /app
COPY pyproject.toml Cargo.toml README.md ./
COPY src ./src

# Build deps for crates like openssl-sys / libgit2-sys
# (maturin base image is manylinux; use yum)
RUN yum install -y openssl-devel pkgconfig && yum clean all

# Build manylinux-compliant wheel for CPython 3.11 to match the runtime image.
# (The maturin image contains multiple CPython versions under /opt/python/)
RUN maturin build --release --strip --compatibility manylinux2014 \
    --interpreter /opt/python/cp311-cp311/bin/python

FROM python:3.11-slim AS runtime
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1

# Install system deps for git2/openssl
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends ca-certificates libssl-dev pkg-config git \ 
    && rm -rf /var/lib/apt/lists/*

# Avoid git issues (otherwise this might stop the python rust code from working)
RUN git config --global --add safe.directory /app || true

COPY --from=builder /app/target/wheels/*.whl /tmp/
RUN pip install /tmp/*.whl && rm /tmp/*.whl

# Runtime deps for building in-container too (useful with docker-compose + volumes).
# This doesn't rebuild the whole image each time; it enables `maturin build` inside the running container.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl pkg-config libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust + maturin in runtime so you can rebuild the wheel via volume mounts.
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN pip install --no-cache-dir "maturin[patchelf]"

# Default command keeps container alive
CMD ["tail", "-f", "/dev/null"]
#CMD ["python", "-c", "import basecollab, json; print(json.loads(basecollab.scan_py(None,None,None,None)))"]
