# fapis — FastAPI Infrastructure Starter

**Version 0.1.1**

`fapis` is a CLI tool and template library to quickly scaffold production-ready FastAPI projects. It provides a clean, modern, and beginner-friendly base template that follows current best practices.

## ✨ What's New in 0.1.1

This release significantly simplifies the base template structure:

- ✅ **Simplified Architecture** - Removed unnecessary abstraction layers
- ✅ **Modern Dependencies** - Updated to Pydantic v2, FastAPI 0.109+, and Python 3.12
- ✅ **Flatter Structure** - Reduced from 4 to 2 folders in `app/`
- ✅ **Better Documentation** - Comprehensive README with practical examples
- ✅ **Enhanced Features** - CORS support, uptime tracking, modern datetime handling
- ✅ **Beginner Friendly** - Easier to understand and extend

### Key Changes

| Aspect        | v0.1.0                                      | v0.1.1                 |
| ------------- | ------------------------------------------- | ---------------------- |
| Pydantic      | v1 (deprecated)                             | v2 (modern)            |
| Python        | 3.11                                        | 3.12                   |
| App Folders   | 4 (api, core, dependencies, infrastructure) | 2 (api, core)          |
| Configuration | `BaseSettings`                              | `pydantic-settings`    |
| Lifecycle     | Separate module                             | Inline context manager |
| README        | Basic                                       | Comprehensive guide    |

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install fapis

# Or install from source for development
git clone https://github.com/Dirac1235/fapis.git
cd fapis
pip install -e .
```

### Generate a New Project

```bash
# Create a new FastAPI project
fapis base ./my-awesome-api

# Navigate to the project
cd my-awesome-api

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000/docs for interactive API documentation!

## 📦 What's Included

The base template includes:

- ✅ **FastAPI 0.109+** with modern async support
- ✅ **Pydantic v2** settings with environment variables
- ✅ **CORS middleware** pre-configured
- ✅ **Health check** endpoint with uptime tracking
- ✅ **Logging** configured and ready to use
- ✅ **Testing** setup with pytest and httpx
- ✅ **Docker** configuration for containerization
- ✅ **Makefile** with helpful development commands
- ✅ **Type hints** throughout the codebase

## 🗂️ Project Structure (Simplified!)

The generated project has a clean, minimal structure:

```
my-awesome-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point with lifecycle
│   ├── api/                 # API endpoints (add your routes here)
│   │   ├── __init__.py
│   │   └── health.py        # Example health check endpoint
│   └── core/                # Core configuration
│       ├── __init__.py
│       └── config.py        # Settings management with pydantic-settings
├── tests/
│   └── test_health.py       # Example tests with pytest
├── .env.example             # Environment variables template
├── .gitignore              # Python gitignore
├── Dockerfile              # Production-ready container
├── Makefile                # Development commands
├── README.md               # Project-specific documentation
└── requirements.txt        # Python dependencies
```

**No more unnecessary folders!** Everything you need, nothing you don't.

## 🛠️ Development Workflow

### Available Make Commands

```bash
make help          # Show all available commands
make install       # Install dependencies
make run           # Run development server with auto-reload
make test          # Run tests with pytest
make clean         # Remove Python cache files
make docker-build  # Build Docker image
make docker-run    # Run Docker container
```

### Adding Features

**Add a new endpoint:**

```python
# app/api/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
async def get_users():
    return {"users": ["Alice", "Bob"]}
```

Then register it in `app/main.py`:

```python
from app.api import users

app.include_router(users.router, prefix="/api", tags=["users"])
```

**Add database support:**

1. Add SQLAlchemy or your preferred ORM to `requirements.txt`
2. Create `app/db/` for models and connections
3. Initialize in the `lifespan` function in `main.py`

See the template README for more examples!

## 📚 Template Features

### Environment Configuration

All settings are managed through `.env` file:

```bash
APP_NAME="My Awesome API"
VERSION="0.1.1"
DEBUG=true
HOST="0.0.0.0"
PORT=8000
CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
```

### Health Endpoint

Every generated project includes a health check endpoint:

```bash
curl http://localhost:8000/api/health
```

Response:

```json
{
  "status": "ok",
  "timestamp": "2025-12-22T07:39:29.805384+00:00",
  "uptime_seconds": 42.15
}
```

### CORS Support

CORS is pre-configured and can be customized via environment variables:

```python
# Configured via settings
CORS_ORIGINS="http://localhost:3000,https://myapp.com"
```

## 🐳 Docker Deployment

The template includes a production-ready Dockerfile:

```bash
# Build the image
docker build -t my-awesome-api .

# Run the container
docker run -p 8000:8000 my-awesome-api
```

Or use Docker Compose (create your own `docker-compose.yml`):

```yaml
version: "3.8"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
```

## 🤝 How the CLI Works

The CLI is simple and straightforward:

```bash
fapis <template> <destination>
```

Currently available templates:

- `base` - Modern, minimal FastAPI starter (recommended)

Example:

```bash
fapis base ./services/my-service
```

The CLI will:

1. Copy the template files to your destination
2. Initialize a git repository (if git is available)
3. Provide next steps for you to follow

## 📖 Links

- **GitHub Repository**: [Dirac1235/fapis](https://github.com/Dirac1235/fapis)
- **PyPI Package**: [pypi.org/project/fapis](https://pypi.org/project/fapis/)
- **Template Source**: `fapis/templates/infrastructure/base/`
- **Issues & Feedback**: [GitHub Issues](https://github.com/Dirac1235/fapis/issues)

## 🎯 Why Use fapis?

- **Beginner-Friendly**: Simple structure that's easy to understand
- **Production-Ready**: Includes logging, health checks, CORS, Docker
- **Modern**: Uses latest FastAPI, Pydantic v2, and Python best practices
- **Extensible**: Clear patterns for adding features
- **Well-Documented**: Both the CLI and generated projects have great docs
- **Type-Safe**: Full type hints throughout

## 🔄 Migration from 0.1.0

If you have projects generated with v0.1.0, here are the key differences:

1. **Removed folders**: `app/dependencies/`, `app/infrastructure/`
2. **Removed files**: `app/core/logging.py`
3. **Updated imports**: Pydantic settings now from `pydantic-settings`
4. **New features**: CORS middleware, uptime tracking, modern datetime

For new projects, use v0.1.1. Existing projects can continue using v0.1.0 or be manually updated.

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Dirac1235/fapis.git
cd fapis

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .

# Make your changes...

# Test the CLI
fapis base ./test-project
cd test-project
pip install -r requirements.txt
pytest -v
```

## 🌟 Show Your Support

If you find this project helpful, please give it a ⭐ on GitHub!

---

**Built with ❤️ for the FastAPI community**
