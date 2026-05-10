# Use Python 3.11 slim image as base
FROM python:3.12-slim

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=metabase_agent.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libmagic1 \
        libvips42 \
        libcairo2-dev \
        libgirepository1.0-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# install dependencies from uv.lock file
COPY pyproject.toml uv.lock ./

# https://github.com/astral-sh/uv/issues/10462
# uv records index url into uv.lock but doesn't failover among multiple indexes
RUN --mount=type=cache,id=metabase_uv,target=/root/.cache/uv,sharing=locked \
    if [ "$NEED_MIRROR" = "1" ]; then \
        sed -i 's|pypi.org|mirrors.aliyun.com/pypi|g' uv.lock; \
    else \
        sed -i 's|mirrors.aliyun.com/pypi|pypi.org|g' uv.lock; \
    fi; \
    uv sync --python 3.12 --frozen && \
    .venv/bin/python3 -m ensurepip --upgrade

# Copy project
COPY . .

# Create logs directory
RUN mkdir -p logs


# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run database migrations and start Daphne server
CMD ["sh", "-c", "uv run python manage.py migrate && uv run daphne -b 0.0.0.0 -p 8000 metabase_agent.asgi:application"]