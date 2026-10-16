# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.13

# --- builder: resolve and install the pinned dependencies into a virtualenv ---
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
COPY requirements.txt .
# Hashes in requirements.txt make pip refuse any file that is not the one locked.
RUN /opt/venv/bin/pip install --require-hashes -r requirements.txt

# --- runtime: the venv and the code only, no build tools, no root ---
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home \
        --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
# Owned by root and read-only for the app user: a compromised process cannot edit its code.
COPY alembic.ini gunicorn.conf.py ./
COPY alembic ./alembic
COPY app ./app
COPY --chmod=755 docker/entrypoint.sh /usr/local/bin/docker-entrypoint
COPY docker/healthcheck.py /usr/local/bin/healthcheck.py
# PYTHONDONTWRITEBYTECODE is set, so compile once here to keep start-up fast.
RUN python -m compileall -q app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD ["python", "/usr/local/bin/healthcheck.py"]

ENTRYPOINT ["docker-entrypoint"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]
