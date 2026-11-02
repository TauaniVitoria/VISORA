"""
FastAPI Main Application Entrypoint.
Plataforma SaaS de Gestão de Estacionamentos com ALPR.
"""

from contextlib import asynccontextmanager
import logging
import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import Base, engine

logger = logging.getLogger("visora.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Criação das tabelas na inicialização quando disponível
    if settings.ENVIRONMENT != "testing" and not settings.DATABASE_URL.startswith("sqlite"):
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            # Em desenvolvimento local sem Postgres ativo, não impede o startup
            pass
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Setup CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Registra as rotas da versão 1 da API
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware de telemetria para medir tempo de resposta HTTP."""
    start_time = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
    return response


@app.exception_handler(IntegrityError)
async def sqlalchemy_integrity_error_handler(request: Request, exc: IntegrityError):
    """Tratamento centralizado para violações de integridade relacional."""
    logger.warning("Violação de integridade no banco de dados em %s: %s", request.url.path, str(exc.orig or exc))
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Conflito de integridade de dados. Verifique se o registro já existe ou possui vínculos."},
    )


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify service availability."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }
