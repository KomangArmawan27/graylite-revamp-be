import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import RequestLoggingMiddleware
from app.modules import admin, auth, browser, command, form, grid, health, menu, meta, picker

logger = logging.getLogger("erp-api")

app = FastAPI(
    title="ERP API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

@app.on_event("startup")
async def startup_event():
    logger.info(f"startup db_name={settings.DB_NAME} enable_writes={settings.ENABLE_WRITES} enable_delete={settings.ENABLE_DELETE}")

# CORS middleware
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(RequestLoggingMiddleware)
register_error_handlers(app)

# Register routers
app.include_router(health.router)
app.include_router(auth.router, prefix="/v1")
app.include_router(menu.router, prefix="/v1")
app.include_router(meta.router, prefix="/v1")
app.include_router(browser.router, prefix="/v1")
app.include_router(form.router, prefix="/v1")
app.include_router(grid.router, prefix="/v1")
app.include_router(picker.router, prefix="/v1")
app.include_router(command.router, prefix="/v1")
app.include_router(admin.router, prefix="/v1")
