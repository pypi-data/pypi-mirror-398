import os
from fastapi import FastAPI, status
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import orjson


def add_healthcheck(app: FastAPI) -> None:
    class HealthCheck(BaseModel):
        status: str = "OK"

    @app.get(
        "/healthz",
        summary="Perform a Health Check",
        response_description="Return HTTP Status Code 200 (OK)",
        status_code=status.HTTP_200_OK,
        response_model=HealthCheck,
    )
    def get_health() -> HealthCheck:
        """
        Perform a Health Check
        Endpoint to perform a healthcheck on. This endpoint can primarily be used Docker
        to ensure a robust container orchestration and management is in place. Other
        services which rely on proper functioning of the API service will not deploy if this
        endpoint returns any other HTTP status code except 200 (OK).
        Returns:
            HealthCheck: Returns a JSON response with the health status
        """
        return HealthCheck(status="OK")


class ORJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content) -> bytes:
        return orjson.dumps(content, option=orjson.OPT_SERIALIZE_NUMPY)


def set_app_doc_static_file(app, favicon_url="/static/icon.png"):
    root = os.path.dirname(os.path.realpath(__file__))
    app.mount("/static", StaticFiles(directory=f"{root}/static"), name="static")

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
            swagger_favicon_url=f"{favicon_url}",
        )

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url="/static/redoc.standalone.js",
            redoc_favicon_url=f"{favicon_url}",
        )


def create_app(title, version='1.0', add_health_route=False, openapi_tags=None, set_static_file=True,
               favicon_url='/static/icon.png') -> FastAPI:
    if openapi_tags is None:
        openapi_tags = [
            {"name": "private",
             "description": "私有接口"},
            {"name": "public",
             "description": "公有接口"},
        ]
    app = FastAPI(openapi_tags=openapi_tags,
                  title=title,
                  version=version,
                  description="",
                  docs_url=None,
                  redoc_url=None,
                  default_response_class=ORJSONResponse,
                  )
    if set_static_file:
        set_app_doc_static_file(app, favicon_url=favicon_url)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if add_health_route:
        add_healthcheck(app)

    return app


def add_router(app: FastAPI, router: APIRouter):
    app.include_router(router)
