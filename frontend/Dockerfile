# ── Stage 1: build React app ──────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# ── Stage 2: serve with nginx (uses envsubst for BACKEND_URL at runtime) ──────
FROM nginx:1.27-alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx template (BACKEND_URL substituted at container start)
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

# nginx:alpine automatically runs envsubst on /etc/nginx/templates/*.template
