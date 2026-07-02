FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY utils/ ./utils/

ENV DATABASE_URL=""
ENV CORS_ORIGINS="*"
ENV PORT=8000

EXPOSE 8000

CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
