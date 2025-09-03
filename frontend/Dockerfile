# ===== Base image: Node + pnpm via Corepack =====
FROM node:22-alpine AS base
WORKDIR /app
ENV CI=1 NEXT_TELEMETRY_DISABLED=1
RUN corepack enable && corepack prepare pnpm@9.12.3 --activate

# ===== Deps =====
FROM base AS deps
WORKDIR /app
COPY pnpm-lock.yaml package.json ./
RUN pnpm install --frozen-lockfile

# ===== Builder =====
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_OUTPUT=standalone
RUN pnpm build

# # ===== Runner =====
# FROM node:22-alpine AS runner
# WORKDIR /app
# ENV NODE_ENV=production PORT=3003 NEXT_TELEMETRY_DISABLED=1
# COPY --from=builder /app/.next/standalone ./
# COPY --from=builder /app/.next/static ./.next/static
# COPY --from=builder /app/public ./public

EXPOSE 3003
# HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
#   CMD wget -qO- http://127.0.0.1:3003/ >/dev/null || exit 1
# CMD ["node", "server.js"]