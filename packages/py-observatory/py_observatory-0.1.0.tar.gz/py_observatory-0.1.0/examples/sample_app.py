"""Sample FastAPI application demonstrating py-observatory usage."""

import asyncio
import random
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from py_observatory import Observatory

# Create and configure Observatory
observatory = Observatory()


# ========== Cronjob Examples ==========

@observatory.monitor_job(schedule="*/5 * * * *")
async def data_sync_job():
    """Simulated data sync job that runs every 5 minutes."""
    await asyncio.sleep(random.uniform(0.1, 0.5))
    if random.random() < 0.1:  # 10% chance of failure
        raise Exception("Data sync failed: connection timeout")
    return {"synced": random.randint(10, 100)}


@observatory.monitor_job("cleanup_old_records", schedule="0 0 * * *")
async def cleanup_job():
    """Simulated cleanup job that runs daily."""
    await asyncio.sleep(random.uniform(0.2, 0.8))
    return {"deleted": random.randint(5, 50)}


@observatory.monitor_job("generate_report", schedule="0 */6 * * *")
async def report_job():
    """Simulated report generation job that runs every 6 hours."""
    await asyncio.sleep(random.uniform(0.5, 1.5))
    if random.random() < 0.05:  # 5% chance of failure
        raise ValueError("Report generation failed: invalid data")
    return {"report_id": f"RPT-{random.randint(1000, 9999)}"}


async def run_background_jobs():
    """Run cronjobs in background for demo purposes."""
    while True:
        try:
            # Run jobs with different frequencies
            await data_sync_job()
        except Exception:
            pass  # Job failures are already tracked

        await asyncio.sleep(5)  # Run every 5 seconds for demo

        # Run cleanup less frequently
        if random.random() < 0.2:
            try:
                await cleanup_job()
            except Exception:
                pass

        # Run report even less frequently
        if random.random() < 0.1:
            try:
                await report_job()
            except Exception:
                pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for background tasks."""
    # Start background job runner
    task = asyncio.create_task(run_background_jobs())
    yield
    # Cleanup
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await observatory.close()


# Create FastAPI app with lifespan
app = FastAPI(title="Sample Observatory App", lifespan=lifespan)

# Instrument the app
observatory.instrument(app)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Hello World", "status": "ok"}


@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID."""
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    return {"id": user_id, "name": f"User {user_id}"}


@app.post("/api/orders")
async def create_order(order: dict = None):
    """Create an order with custom metrics."""
    order = order or {"type": "online", "total": 99.99}

    # Track custom counter
    await observatory.increment("orders_created", {"type": order.get("type", "unknown")})

    # Track order value histogram
    await observatory.histogram("order_value", order.get("total", 0))

    return {"status": "created", "order": order}


@app.get("/api/external")
async def external_call():
    """Make an external API call (tracked by Observatory)."""
    async with observatory.create_http_client() as client:
        try:
            response = await client.get("https://httpbin.org/get")
            return {"status": "success", "external_status": response.status_code}
        except Exception as e:
            return {"status": "error", "message": str(e)}


@app.get("/api/slow")
async def slow_endpoint():
    """Simulated slow endpoint for testing latency histograms."""
    import asyncio
    await asyncio.sleep(0.5)
    return {"status": "ok", "delay": "500ms"}


@app.get("/api/error")
async def error_endpoint():
    """Endpoint that always raises an error."""
    raise ValueError("This is a test error")


@app.on_event("shutdown")
async def shutdown():
    """Clean up Observatory on shutdown."""
    await observatory.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
