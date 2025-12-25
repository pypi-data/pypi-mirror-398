import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_ok() -> None:
	"""Health endpoint should return status, timestamp, and uptime."""
	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://test") as ac:
		r = await ac.get("/api/health")
		assert r.status_code == 200
		data = r.json()
		assert data["status"] == "ok"
		assert "timestamp" in data
		assert "uptime_seconds" in data
		assert isinstance(data["uptime_seconds"], (int, float))

