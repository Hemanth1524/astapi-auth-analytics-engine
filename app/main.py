import time
from fastapi import FastAPI, Request, Response
from starlette.concurrency import run_in_threadpool
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.database import Base, engine, SessionLocal
from app.core.rate_limit import limiter
from app.routers import auth, analytics
from app.models import RequestMetric

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth & Analytics API Engine", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def record_metric(endpoint: str, method: str, status_code: int, duration_ms: float, client_ip: str | None):
    db = SessionLocal()
    try:
        metric = RequestMetric(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            process_time_ms=round(duration_ms, 2),
            client_ip=client_ip
        )
        db.add(metric)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

@app.middleware("http")
async def track_latency_and_metrics(request: Request, call_next):
    start_time = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        # Re-raise so FastAPI error handlers run, but retain 500 status_code for metrics
        raise
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else None)
        
        if not request.url.path.startswith(("/docs", "/openapi.json", "/redoc")):
            await run_in_threadpool(
                record_metric,
                request.url.path,
                request.method,
                status_code,
                duration_ms,
                client_ip
            )

app.include_router(auth.router)
app.include_router(analytics.router)

@app.get("/")
def health_check():
    return {"status": "online", "version": "1.0.0"}
