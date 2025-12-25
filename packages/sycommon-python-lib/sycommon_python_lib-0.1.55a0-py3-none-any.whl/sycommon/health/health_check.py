from fastapi import FastAPI, APIRouter


def setup_health_handler(app: FastAPI):
    health_router = APIRouter()

    @health_router.get("/actuator/health")
    async def health_check():
        """实现 Nacos 健康检查接口"""
        return {
            "status": "UP",
            "groups": ["liveness", "readiness"]
        }

    app.include_router(health_router)

    return app
