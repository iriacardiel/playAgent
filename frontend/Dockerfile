
FROM node:22-alpine AS base
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.12.3 --activate

FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
# Create public directory before running postinstall script
RUN mkdir -p public
RUN pnpm install --frozen-lockfile

FROM deps AS builder
WORKDIR /app
COPY . .
ARG LANGGRAPH_API_URL=http://backend:2924
ENV LANGGRAPH_API_URL=${LANGGRAPH_API_URL}
RUN pnpm build

FROM node:22-alpine AS runner
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.12.3 --activate
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/package.json ./package.json
COPY --from=deps /app/pnpm-lock.yaml ./pnpm-lock.yaml
COPY . .
ARG LANGGRAPH_API_URL=http://backend:2924
ENV LANGGRAPH_API_URL=${LANGGRAPH_API_URL}
CMD ["pnpm", "dev"]
