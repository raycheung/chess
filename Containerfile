FROM node:24-alpine AS frontend
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY backend/chess_app ./chess_app
COPY --from=frontend /src/dist ./static
ENV PATH=/app/.venv/bin:$PATH CHESS_DATA=/data CHESS_STATIC=/app/static
USER 1000
EXPOSE 8000
CMD ["uvicorn", "chess_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
