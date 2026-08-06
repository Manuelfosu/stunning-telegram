FROM node:20-alpine AS ui
ENV NODE_ENV=development
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm install --include=dev --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt
COPY backend/ ./
COPY --from=ui /ui/dist ./dist
RUN mkdir -p /app/uploads /var/data/uploads
EXPOSE 8000
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
