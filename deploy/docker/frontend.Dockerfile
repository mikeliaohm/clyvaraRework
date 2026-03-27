FROM node:20-alpine

WORKDIR /app/frontend

COPY frontend/package*.json /app/frontend/
RUN npm ci

COPY frontend /app/frontend

EXPOSE 8001

CMD ["sh", "-c", "npm run dev -- --host 0.0.0.0 --port ${FRONTEND_PORT:-8001}"]
