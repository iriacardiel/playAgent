# ===== Base image =====
FROM python:3.12.3-slim AS base
# ===== Environment =====
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
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && uv venv "$VIRTUAL_ENV"

# ===== Dependency layer (cacheable) =====
# Copy only the project metadata so we can cache the resolved deps
COPY pyproject.toml ./

# Install locked dependencies *into* /opt/venv.
# --python targets the venv interpreter; --active uses the already-active env.
RUN uv sync --python "$VIRTUAL_ENV/bin/python" --active

# ===== App layer =====
# Now bring in the rest of your source *after* deps are installed
COPY . .

# Install your package editable, without re-resolving deps
RUN uv pip install --python "$VIRTUAL_ENV/bin/python" --no-deps .

# ---- Runtime (slim, no build tools) ----
FROM base AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Copy venv and app artifacts
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# # Non-root user
# RUN useradd -u 10001 -m appuser && chown -R appuser:appuser /app /opt/venv
# USER appuser

# App defaults baked in (override via compose if needed)
ENV PORT=2024
EXPOSE 2024

# Default command (no PYTHONPATH needed)
CMD /opt/venv/bin/langgraph dev \
    --config ./langgraph.json \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --allow-blocking \
    --no-browser