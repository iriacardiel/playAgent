# ===== Base image: Node + pnpm via Corepack =====
FROM node:22-alpine AS base
WORKDIR /app
ENV CI=1 NEXT_TELEMETRY_DISABLED=1
RUN corepack enable && corepack prepare pnpm@9.12.3 --activate

# ===== Deps (install packages) =====
FROM base AS deps
WORKDIR /app
COPY pnpm-lock.yaml package.json ./
RUN pnpm install --frozen-lockfile

# # ===== Dev runtime =====
# FROM base AS dev
# WORKDIR /app
# COPY --from=deps /app/node_modules ./node_modules
# COPY . .
# CMD ["pnpm", "dev", "-p", "3003", "-H", "0.0.0.0"]

# # ===== Builder (prod build) =====
# FROM deps AS builder
# WORKDIR /app
# COPY . .
# ENV NEXT_OUTPUT=standalone
# RUN pnpm build

# # ===== Prod runtime (slim image) =====
# FROM node:22-alpine AS runner
# WORKDIR /app
# ENV NODE_ENV=production
# COPY --from=builder /app/.next/standalone ./
# COPY --from=builder /app/public ./public
# COPY --from=builder /app/.next/static ./.next/static
# EXPOSE 3000
# CMD ["node", "server.js"]