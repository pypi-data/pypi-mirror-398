FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Crucial for finding the zenithauth package in the src folder
ENV PYTHONPATH=/app/src

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Install UV for lightning fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy package metadata first to leverage Docker cache
COPY pyproject.toml README.md ./
RUN uv pip install --system .[dev]

# Copy the rest of the source code
COPY . .

CMD ["pytest"]

