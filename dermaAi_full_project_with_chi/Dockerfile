FROM node:22-alpine AS frontend-build

WORKDIR /frontend
ARG VITE_DERMOSCOPY_MODEL_API_URL=https://javariarizwan-ham10000-api.hf.space
ENV VITE_DERMOSCOPY_MODEL_API_URL=$VITE_DERMOSCOPY_MODEL_API_URL
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/db.sqlite3 \
    MEDIA_ROOT=/data/media

WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend-build /frontend/dist/ /app/frontend_dist/
RUN python manage.py makemigrations --check --dry-run \
    && python manage.py collectstatic --noinput \
    && mkdir -p /data/media \
    && addgroup --system app \
    && adduser --system --ingroup app app \
    && chown -R app:app /app /data

USER app
EXPOSE 8000
CMD ["sh", "/app/entrypoint.sh"]