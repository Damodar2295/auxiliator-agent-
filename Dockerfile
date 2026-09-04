FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY . .
COPY --from=frontend /frontend/dist /app/frontend/dist
RUN pip install --no-cache-dir .
EXPOSE 8080
CMD ["gunicorn", "-c", "gunicorn.conf.py", "agent.main:app"]
