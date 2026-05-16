# VALLUM — Production Dockerfile
# Multi-stage build for minimal attack surface

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements-cloud.txt .
RUN pip install --no-cache-dir --user -r requirements-cloud.txt

# Stage 2: Runtime
FROM python:3.11-slim

RUN groupadd -r vallum && useradd -r -g vallum vallum

WORKDIR /app

COPY --from=builder /root/.local /home/vallum/.local
COPY --chown=vallum:vallum vallum/ ./vallum/
COPY --chown=vallum:vallum deploy/ ./deploy/

ENV PATH=/home/vallum/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENV=production

RUN chmod 755 /app && chown -R vallum:vallum /app

USER vallum

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

CMD ["sh", "-c", "uvicorn vallum.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
