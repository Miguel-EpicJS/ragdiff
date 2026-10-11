FROM python:3.12-alpine3.21

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apk add --no-cache libstdc++ \
    && pip install --no-cache-dir uv==0.6.14 \
    && addgroup -S ragdiff \
    && adduser -S -G ragdiff ragdiff

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
COPY frontend ./frontend
COPY examples ./examples

USER ragdiff
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["uv", "run", "--no-sync", "uvicorn", "ragdiff.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
