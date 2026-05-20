"""
Router: GET /api/status
Healthcheck leve que retorna o estado da aplicação.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Produto, Categoria
from app.schemas import StatusOut

router = APIRouter()


@router.get("/api/status", response_model=StatusOut)
def status(db: Session = Depends(get_db)):
    """Rota leve de verificação de integridade (healthcheck)."""
    return StatusOut(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_produtos=db.query(Produto).count(),
        total_categorias=db.query(Categoria).count(),
    )
