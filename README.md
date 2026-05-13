# Metabase Agent

Metabase Agent is a Django + Ninja API service that powers AI-assisted Metabase workflows.

It currently includes:

- v1 helper APIs for image analysis and SQL generation/fixing.
- v2 conversational agent APIs (streaming and non-streaming).
- v2 dashboard analysis APIs (streaming and non-streaming).
- license and model compatibility endpoints used by Metabase integrations.

## Architecture Overview

Main folders:

- metabase_agent: Django project settings and root URLs.
- views: HTTP endpoints split by API version.
- agents: LLM and streaming agent logic.
- tools: tool functions used by agent workflows.
- utils: shared API clients, logging, model provider, and message history.
- constants: schemas, prompts, and API constants.
- docs: endpoint-specific docs and examples.
- data: sample requests and debug payloads.

## Requirements

- Python 3.12 recommended (matches container runtime).
- uv package manager.
- Docker and Docker Compose (optional, for containerized runs).
- PostgreSQL optional (SQLite is default when DB_DRIVER is not pg).

## Quick Start (Local)

1. Install dependencies with uv.

```bash
uv sync
```

2. Create a .env file in the project root.

```env
SECRET_KEY=replace-with-a-secure-value
DEBUG=True

# LLM provider (set at least one)
OPENAI_API_KEY=
DEEPSEEK_API_KEY=

# Optional model/provider overrides
OPEN_AI_BASE_URL=
OPEN_AI_MODEL_NAME=gpt-4o
GROQ_API_KEY=

# Metabase integration
METABASE_API_KEY=
METABASE_BASE_URL=http://localhost:3000

# Database
DB_DRIVER=sqlite
DATABASE_NAME=
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

3. Run migrations.

```bash
uv run python manage.py migrate
```

4. Start the server.

```bash
uv run python manage.py runserver 0.0.0.0:8000
```

5. Open docs and admin.

- API v1 docs: http://localhost:8000/api/v1/docs
- API v2 docs: http://localhost:8000/api/v2/docs
- Django admin: http://localhost:8000/admin

## Docker

Development compose:

```bash
docker-compose up --build
```

- Web app: http://localhost:8000
- Postgres: localhost:5432

Production-like compose:

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

- Nginx entrypoint: http://localhost:8080
- TLS port mapping: https://localhost:8443

## API Surface

Root routes:

- /api/v1/
- /api/v2/
- /api/ (license endpoints)
- /anthropic/ (model/message compatibility endpoints)

### v1 Endpoints

- POST /api/v1/analyze/chart
- POST /api/v1/analyze/dashboard
- POST /api/v1/sql/generate
- POST /api/v1/sql/fix
- POST /api/v1/select-metric/
- POST /api/v1/find-outliers/

### v2 Agent Endpoints

- POST /api/v2/agent/non_stream
- POST /api/v2/agent/stream

Request examples and streaming notes:

- docs/agent.md
- data/sample_agent_request.json

### v2 Dashboard Endpoints

- POST /api/v2/dashboard_analysis/non_stream
- POST /api/v2/dashboard_analysis/stream

Request examples and streaming notes:

- docs/dashboard-agent.md
- data/sample_dashboard_request.json

### License and Compatibility Endpoints

- GET /api/{token}/v2/status
- POST /api/{token}/v2/metering
- GET /anthropic/v1/models
- POST /anthropic/v1/messages

## Environment Variables

Core variables:

- SECRET_KEY: Django secret key.
- DEBUG: true or false.
- OPENAI_API_KEY: primary OpenAI key.
- DEEPSEEK_API_KEY: optional alternative provider key.
- OPEN_AI_BASE_URL: optional custom OpenAI-compatible endpoint.
- OPEN_AI_MODEL_NAME: defaults to gpt-4o.
- METABASE_API_KEY: Metabase API key used by tool calls.
- METABASE_BASE_URL: Metabase base URL.

Database variables (used when DB_DRIVER=pg):

- DATABASE_NAME
- DATABASE_USER
- DATABASE_PASSWORD
- DATABASE_HOST
- DATABASE_PORT

## Common Commands

Run tests:

```bash
uv run python manage.py test
```

Create and apply migrations:

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
```

Collect static files:

```bash
uv run python manage.py collectstatic --noinput
```

Tail container logs:

```bash
docker-compose logs -f web
```

## Troubleshooting

No env.example file exists in this repo, so create .env manually.

If model initialization fails:

- Set OPENAI_API_KEY or DEEPSEEK_API_KEY.
- Ensure OPEN_AI_BASE_URL is valid when provided.

If Metabase tools fail:

- Verify METABASE_BASE_URL and METABASE_API_KEY.
- Confirm your Metabase instance is reachable from this service.

If database startup fails:

- Use DB_DRIVER=sqlite for local quick start.
- For PostgreSQL, ensure all DATABASE_* vars are set correctly.

Logs are written to the logs directory with daily rotation.
