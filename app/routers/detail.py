"""
Router: GET /api/recurso-detalhe/{id}
Consulta simples e indexada de um produto por ID, com detalhes da categoria.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Produto
from app.schemas import ProdutoDetalhe

router = APIRouter()


@router.get("/api/recurso-detalhe/{produto_id}", response_model=ProdutoDetalhe)
def recurso_detalhe(produto_id: int, db: Session = Depends(get_db)):
    """Retorna os detalhes de um produto específico (busca por PK indexada)."""
    produto = (
        db.query(Produto)
        .options(joinedload(Produto.categoria))
        .filter(Produto.id == produto_id)
        .first()
    )

    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    return produto
