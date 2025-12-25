from fastapi import FastAPI, APIRouter
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html


def setup_docs_handler(app: FastAPI):
    docs_router = APIRouter()

    @docs_router.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title}",
            swagger_favicon_url="https://static.sytechnology.com/img/sylogopng.png",
            swagger_js_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.27.1/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.27.1/swagger-ui.css",
            swagger_ui_parameters={"defaultModelsExpandDepth": -1},
        )

    @docs_router.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title}",
            redoc_favicon_url="https://static.sytechnology.com/img/sylogopng.png",
            redoc_js_url="https://cdn.bootcdn.net/ajax/libs/redoc/2.1.5/redoc.standalone.js",
        )

    app.include_router(docs_router)

    return app
