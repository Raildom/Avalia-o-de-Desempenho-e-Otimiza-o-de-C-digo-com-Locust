"""
Entrypoint da API REST monolítica (FastAPI).

Inicializa a aplicação, registra os routers e popula o banco no startup.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import slow, detail, status, create


OPTIMIZED = os.environ.get("OPTIMIZED", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa o banco de dados e popula com dados de seed."""
    init_db()
    modo = "OTIMIZADO" if OPTIMIZED else "BASELINE (lento)"
    print(f"[API] Modo: {modo}")
    print("[API] Banco de dados inicializado. API pronta!")
    yield


app = FastAPI(
    title="API Monolítica - Trabalho 7",
    description="API REST para testes de desempenho com Locust",
    version="1.0.0",
    lifespan=lifespan,
)

# Registrar routers
app.include_router(slow.router, tags=["Recurso Lento"])
app.include_router(detail.router, tags=["Recurso Detalhe"])
app.include_router(status.router, tags=["Status"])
app.include_router(create.router, tags=["Criar Recurso"])


@app.get("/")
def root():
    """Rota raiz com informações da API."""
    return {
        "app": "API Monolítica - Trabalho 7",
        "modo": "otimizado" if OPTIMIZED else "baseline",
        "endpoints": [
            "GET  /api/recurso-lento",
            "GET  /api/recurso-detalhe/{id}",
            "GET  /api/status",
            "POST /api/recurso",
        ],
        "docs": "/docs",
    }
