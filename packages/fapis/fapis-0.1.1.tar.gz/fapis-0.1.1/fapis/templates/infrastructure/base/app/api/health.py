import time
from datetime import datetime, UTC

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request):
	"""Health check endpoint with service metadata and uptime."""
	start_time = getattr(request.app.state, "start_time", time.time())
	uptime = time.time() - start_time
	
	return {
		"status": "ok",
		"timestamp": datetime.now(UTC).isoformat(),
		"uptime_seconds": round(uptime, 2),
	}

