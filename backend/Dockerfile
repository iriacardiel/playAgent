# ===== Base image =====
FROM python:3.12.3-slim

# ===== Environment =====
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Keep the venv path explicit & first on PATH
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:/root/.local/bin:${PATH}"

# ===== System deps (minimal) =====
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash curl ca-certificates build-essential git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ===== Install uv =====
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# ===== Create the virtualenv (once) =====
RUN uv venv "$VIRTUAL_ENV"

# ===== Dependency layer (cacheable) =====
# Copy only the project metadata so we can cache the resolved deps
COPY pyproject.toml uv.lock ./

# Install locked dependencies *into* /opt/venv.
# --python targets the venv interpreter; --active uses the already-active env.
RUN uv sync --python "$VIRTUAL_ENV/bin/python" --active

# ===== App layer =====
# Now bring in the rest of your source *after* deps are installed
COPY . .

# Install your package editable, without re-resolving deps
RUN uv pip install --python "$VIRTUAL_ENV/bin/python" --no-deps -e .