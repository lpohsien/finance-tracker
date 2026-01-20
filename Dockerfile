# Stage 1: Build Frontend
FROM node:20-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Runtime
FROM python:3.13-slim
WORKDIR /app

# Install uv
RUN pip install uv

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml ./
RUN uv pip install --system --no-cache -e .[backend]

# Copy Backend Code
COPY api/ ./api/
COPY src/ ./src/
COPY scripts/ ./scripts/

# Copy Frontend Build
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Env variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Run
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port $PORT"]
