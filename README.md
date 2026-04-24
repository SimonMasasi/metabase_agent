# Metabase Helpers

A Django application that provides helper tools for working with Metabase. This project includes various utilities for SQL generation, chart analysis, metrics, and agent-based interactions.

## Project Structure

```
metabase_helpers/
├── metabase_agent_helper/      # Agent-based helper functionality
├── metabase_analyzer_helper/   # Analysis tools
├── metabase_metrics_helper/    # Metrics utilities
├── metabase_sql_helper/        # SQL generation tools
├── tools/                      # Core utility tools
├── utils/                      # Helper utilities
├── views/                      # API views (v1 and v2)
├── constants/                  # Application constants
├── data/                       # Data files
└── notebooks/                  # Jupyter notebooks
```

## Prerequisites

- Python 3.11+
- PostgreSQL (optional, SQLite is used by default)
- Docker (for containerized deployment)

## Running the Project

### Method 1: Docker (Recommended)

#### Development with Docker

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd metabase_helpers
   ```

2. **Copy environment file**

   ```bash
   cp env.example .env
   ```

3. **Edit environment variables** (optional)

   ```bash
   nano .env
   ```

   Example `.env` configuration:

   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DB_DRIVER=sqlite  # or 'pg' for PostgreSQL
   ```

4. **Build and run with Docker Compose**

   ```bash
   docker-compose up --build
   ```

5. **Access the application**
   - Application: http://localhost:8000
   - Admin panel: http://localhost:8000/admin/

#### Production with Docker

1. **Set up production environment**

   ```bash
   cp env.example .env
   ```

2. **Configure production settings**

   ```bash
   nano .env
   ```

   Example production `.env`:

   ```env
   SECRET_KEY=your-very-secure-secret-key
   DEBUG=False
   DB_DRIVER=pg
   DATABASE_NAME=metabase_helpers
   DATABASE_USER=your_db_user
   DATABASE_PASSWORD=your_secure_password
   DATABASE_HOST=db
   DATABASE_PORT=5432
   ```

3. **Run production setup**

   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

4. **Access the application**
   - Application: http://localhost (port 80)
   - The setup includes nginx as a reverse proxy

### Method 2: Local Development (Traditional)

#### Prerequisites Setup

1. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   ```bash
      sudo apt install libvips libvips-dev 
   ```
   or in mac 
   ```bash
      brew install vips
   ```


2. **Set up environment variables**
   ```bash
   cp env.example .env
   nano .env  # Edit with your settings
   ```

#### Database Setup

**Option A: SQLite (Default)**

```bash
python manage.py migrate
```

**Option B: PostgreSQL**

1. Install PostgreSQL and create a database:

   ```sql
   CREATE DATABASE metabase_helpers;
   CREATE USER your_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE metabase_helpers TO your_user;
   ```

2. Update your `.env` file:

   ```env
   DB_DRIVER=pg
   DATABASE_NAME=metabase_helpers
   DATABASE_USER=your_user
   DATABASE_PASSWORD=your_password
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

#### Running the Development Server

**Option A: Using Django's development server**

```bash
python manage.py runserver
```

**Option B: Using Daphne (ASGI server)**

```bash
daphne -b 0.0.0.0 -p 8000 metabase_helpers.asgi:application
```

**Option C: Using Uvicorn**

```bash
uvicorn metabase_helpers.asgi:application --host 0.0.0.0 --port 8000 --reload
```

#### Creating a Superuser

```bash
python manage.py createsuperuser
```

## API Endpoints

The application provides several API endpoints:

- **API v1**: `/api/v1/`

  - Analyzer: `/api/v1/analyzer/`
  - Metrics: `/api/v1/metrics/`
  - SQL: `/api/v1/sql/`

- **API v2**: `/api/v2/`
  - Agent: `/api/v2/agent/`

## Development Tools

### Running Tests

```bash
python manage.py test
```

### Collecting Static Files

```bash
python manage.py collectstatic
```

### Database Operations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (SQLite)
rm db.sqlite3
python manage.py migrate
```

### Working with Notebooks

The project includes Jupyter notebooks in the `notebooks/` directory. To run them:

1. Install Jupyter:

   ```bash
   pip install jupyter
   ```

2. Start Jupyter:
   ```bash
   jupyter notebook notebooks/
   ```

## Docker Commands Reference

### Useful Docker Commands

```bash
# Build the image
docker build -t metabase-helpers .

# Run a single container
docker run -p 8000:8000 metabase-helpers

# View running containers
docker ps

# View logs
docker-compose logs web

# Execute commands in running container
docker-compose exec web python manage.py shell

# Stop all services
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# Rebuild containers
docker-compose up --build --force-recreate
```

### Database Management with Docker

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access Django shell
docker-compose exec web python manage.py shell

# Access database shell (PostgreSQL)
docker-compose exec db psql -U postgres metabase_helpers
```

## Environment Variables

| Variable            | Description                        | Default   | Required            |
| ------------------- | ---------------------------------- | --------- | ------------------- |
| `SECRET_KEY`        | Django secret key                  | None      | Yes                 |
| `DEBUG`             | Enable debug mode                  | True      | No                  |
| `OPENAI_API_KEY`    | OpenAI API key for AI features     | None      | Yes                 |
| `METABASE_API_KEY`  | Metabase API key for integration   | None      | Yes                 |
| `METABASE_BASE_URL` | Metabase instance base URL         | None      | Yes                 |
| `DB_DRIVER`         | Database driver ('sqlite' or 'pg') | sqlite    | No                  |
| `DATABASE_NAME`     | Database name                      | None      | If using PostgreSQL |
| `DATABASE_USER`     | Database user                      | None      | If using PostgreSQL |
| `DATABASE_PASSWORD` | Database password                  | None      | If using PostgreSQL |
| `DATABASE_HOST`     | Database host                      | localhost | If using PostgreSQL |
| `DATABASE_PORT`     | Database port                      | 5432      | If using PostgreSQL |

## Troubleshooting

### Common Issues

1. **Port already in use**

   ```bash
   # Find and kill process using port 8000
   lsof -ti:8000 | xargs kill -9
   ```

2. **Database connection issues**

   - Check if PostgreSQL is running
   - Verify database credentials in `.env`
   - Ensure database exists

3. **Docker build issues**

   ```bash
   # Clean Docker cache
   docker system prune -a

   # Rebuild without cache
   docker-compose build --no-cache
   ```

4. **Static files not loading**

   ```bash
   # Collect static files
   python manage.py collectstatic --noinput
   ```

5. **Permission issues with Docker**
   ```bash
   # Fix ownership issues
   sudo chown -R $USER:$USER .
   ```

### Logs

- **Local development**: Check terminal output
- **Docker**: `docker-compose logs web`
- **Application logs**: Check `logs/` directory

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request
