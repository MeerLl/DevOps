FROM python:3.11-slim as builder
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app/.venv .venv
COPY . .
HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1
CMD [".venv/bin/python", "main.py"]