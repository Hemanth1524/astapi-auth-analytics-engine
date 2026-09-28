import time
from fastapi import FastAPI, Request
from app.core.database import Base, engine, SessionLocal
from app.routers import auth, analytics
from app.models import RequestMetric

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth & Analytics API Engine", version="1.0.0")

@app.middleware("http")
async def track_latency_and_metrics(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    if not request.url.path.startswith(("/docs", "/openapi.json", "/redoc")):
        db = SessionLocal()
        try:
            metric = RequestMetric(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                process_time_ms=round(duration_ms, 2)
            )
            db.add(metric)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    return response

app.include_router(auth.router)
app.include_router(analytics.router)

@app.get("/")
def health_check():
    return {"status": "online", "version": "1.0.0"}
