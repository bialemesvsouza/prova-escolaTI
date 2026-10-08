FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

WORKDIR /app

COPY src/ ./src/
COPY variante/ ./variante/

RUN mkdir -p /data && chown -R nobody:nogroup /data /app

USER nobody

EXPOSE 8080

CMD ["python", "-m", "src.main"]

