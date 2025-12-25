# FastAPI Starter Template

A minimal, production-ready FastAPI template to kickstart your next project. This template includes everything you need to build a modern API with FastAPI.

## Features

- ✅ **FastAPI 0.109+** with async support
- ✅ **Pydantic v2** settings with environment variable support
- ✅ **Modern Python** (3.11+) with type hints
- ✅ **CORS** middleware pre-configured
- ✅ **Health check** endpoint with uptime tracking
- ✅ **Logging** configured out of the box
- ✅ **Testing** setup with pytest and httpx
- ✅ **Docker** ready for containerization
- ✅ **Clean architecture** - simple but extensible

## Quick Start

### 1. Clone or Copy This Template

```bash
# Copy this template directory to your project location
cp -r template/infrastructure/base my-fastapi-project
cd my-fastapi-project
```

### 2. Set Up Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your preferred settings
```

### 4. Run the Application

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload

# Or use the Makefile
make run
```

Visit http://localhost:8000/docs to see the interactive API documentation.

### 5. Run Tests

```bash
# Make sure you're in the virtual environment
PYTHONPATH=. pytest -v tests/

# Or use the Makefile (handles PYTHONPATH automatically)
make test
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── api/                 # API endpoints
│   │   ├── __init__.py
│   │   └── health.py        # Health check endpoint
│   └── core/                # Core configuration
│       ├── __init__.py
│       └── config.py        # Settings management
├── tests/
│   └── test_health.py       # Basic health endpoint test
├── .env.example             # Example environment variables
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── Makefile                # Common commands
└── README.md               # This file
```

## Adding New Features

### Add a New Endpoint

1. Create a new router file in `app/api/`:

```python
# app/api/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
async def get_users():
    return {"users": []}
```

2. Register it in `app/main.py`:

```python
from app.api import users

app.include_router(users.router, prefix="/api", tags=["users"])
```

### Add Database Support

1. Add your database library to `requirements.txt` (e.g., `sqlalchemy`, `databases`)
2. Create a `app/db/` folder for database models and connections
3. Initialize the database connection in the `lifespan` function in `main.py`

### Add Authentication

1. Install `python-jose[cryptography]` and `passlib[bcrypt]`
2. Create `app/core/security.py` for auth utilities
3. Add authentication dependencies and protect your endpoints

## Docker Deployment

### Build and Run

```bash
docker build -t my-fastapi-app .
docker run -p 8000:8000 my-fastapi-app

# Or use the Makefile
make docker-build
make docker-run
```

### With Docker Compose

Create a `docker-compose.yml`:

```yaml
version: "3.8"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
    env_file:
      - .env
```

Run: `docker-compose up`

## Configuration

All configuration is managed through environment variables in `.env`:

- `APP_NAME`: Application name (default: "FastAPI Starter")
- `VERSION`: API version (default: "0.1.1")
- `DEBUG`: Debug mode - enables auto-reload and verbose logging (default: false)
- `HOST`: Server host (default: "0.0.0.0")
- `PORT`: Server port (default: 8000)
- `CORS_ORIGINS`: Comma-separated list of allowed CORS origins

## Best Practices

- Keep the project structure flat and simple
- Use dependency injection for database sessions, auth, etc.
- Write tests for all endpoints
- Use type hints everywhere
- Keep business logic separate from API routes
- Use Pydantic models for request/response validation

## Next Steps

- Add database models and migrations (Alembic)
- Implement authentication and authorization
- Add rate limiting middleware
- Set up CI/CD pipeline
- Configure monitoring and logging (Sentry, etc.)
- Add API versioning strategy

## License

MIT License - feel free to use this template for any project!
