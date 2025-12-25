import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health as health_api
from app.core.config import settings

# Configure logging
logging.basicConfig(
	level=logging.DEBUG if settings.debug else logging.INFO,
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
	"""Handle application startup and shutdown events."""
	# Startup
	app.state.start_time = time.time()
	logger.info(f"Starting {settings.app_name} v{settings.version}")
	yield
	# Shutdown
	uptime = time.time() - app.state.start_time
	logger.info(f"Shutting down (uptime: {uptime:.2f}s)")


def create_app() -> FastAPI:
	"""Create and configure the FastAPI application instance."""
	app = FastAPI(
		title=settings.app_name,
		version=settings.version,
		lifespan=lifespan,
	)
	
	# Configure CORS
	app.add_middleware(
		CORSMiddleware,
		allow_origins=settings.cors_origins,
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)
	
	# Register routers
	app.include_router(health_api.router, prefix="/api", tags=["health"])
	
	return app


app = create_app()


if __name__ == "__main__":
	import uvicorn

	uvicorn.run(
		"app.main:app",
		host=settings.host,
		port=settings.port,
		reload=settings.debug,
	)
