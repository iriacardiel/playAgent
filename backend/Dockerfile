# ===== Base image =====
FROM python:3.12.3-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:/root/.local/bin:${PATH}"

WORKDIR /app

FROM base AS builder
# ===== System deps (minimal) =====
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash curl ca-certificates build-essential git \
 && rm -rf /var/lib/apt/lists/*

# ===== Install uv =====
#RUN curl -LsSf https://astral.sh/uv/install.sh | sh && uv venv "$VIRTUAL_ENV"
RUN python -m pip install --user uv && python -m uv venv "$VIRTUAL_ENV"

# ===== Dependency layer (cacheable) =====
# Copy only the project metadata so we can cache the resolved deps
COPY pyproject.toml ./

# Install locked dependencies *into* /opt/venv.
RUN uv sync --python "$VIRTUAL_ENV/bin/python" --active

# ---- Runtime (slim, no build tools) ----
FROM base AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Copy only the venv from builder (no duplicate app copy)
COPY --from=builder /opt/venv /opt/venv

# Copy source code directly to runtime (only once)
COPY . .

# Set PYTHONPATH so Python can find your modules without installing as package
ENV PYTHONPATH="/app/src" \
    PORT=2024

# Default command
CMD /opt/venv/bin/langgraph dev \
    --config ./langgraph.json \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --allow-blocking \
    --no-browser