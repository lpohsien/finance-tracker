FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY README.md .

# Install dependencies
RUN uv pip install --system .

# Create data directory
RUN mkdir -p data

# Set environment variables
ENV PYTHONPATH=/app

# Run the bot
CMD ["python", "src/main.py"]
