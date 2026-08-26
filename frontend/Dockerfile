# ────────────────────────────────────────────────────────────────────
# E-Commerce Frontend Dockerfile
# Builds Vite + React app and serves via Nginx
# ────────────────────────────────────────────────────────────────────

FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install --quiet

COPY . .

# Vite build — inject API URL at build time if needed
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ── Nginx runtime ────────────────────────────────────────────────────
FROM nginx:alpine AS final

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx SPA config — handles React Router client-side routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:80 || exit 1

CMD ["nginx", "-g", "daemon off;"]
