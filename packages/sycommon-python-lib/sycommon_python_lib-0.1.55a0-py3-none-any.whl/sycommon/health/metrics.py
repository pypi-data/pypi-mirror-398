from fastapi import FastAPI, APIRouter


def setup_metrics_handler(app: FastAPI):
    metrics_router = APIRouter()

    @metrics_router.get("/metrics")
    async def metrics():
        return {"status": "alive"}

    app.include_router(metrics_router)

    return app
