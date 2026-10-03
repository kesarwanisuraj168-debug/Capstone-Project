"""
Smart Campus Occupancy Forecasting & Capacity Optimization — FastAPI backend.

Run (from project root):
    py -3.11 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import FRONTEND_DIR
from .database import Base, engine
from .routes import analytics, auth, dashboard, dataset, occupancy, optimization, prediction


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from .seed import seed_all
    seed_all()
    yield


app = FastAPI(
    title="Smart Campus Occupancy Forecasting & Capacity Optimization",
    description="AIML + Data Science project: spatiotemporal occupancy "
                "forecasting and room/resource capacity optimisation.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(occupancy.router)
app.include_router(prediction.router)
app.include_router(optimization.router)
app.include_router(dashboard.router)
app.include_router(dataset.router)
app.include_router(analytics.router)


@app.get("/health")
@app.get("/api/health")
def health():
    from .services import forecasting
    try:
        meta = forecasting.model_metrics()
        model_ok = True
    except RuntimeError:
        meta, model_ok = {}, False
    return {
        "status": "ok",
        "model_loaded": model_ok,
        "model": meta.get("model"),
        "docs": "/docs",
    }


# ---------- static frontend ----------
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{page:path}", include_in_schema=False)
    def spa(page: str):
        candidate = (FRONTEND_DIR / page).resolve()
        if FRONTEND_DIR.resolve() in candidate.parents and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)