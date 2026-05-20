"""
Router: POST /api/recurso
Cadastro simples de novos produtos no sistema.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Produto, Categoria
from app.schemas import ProdutoCreate, ProdutoOut

router = APIRouter()


@router.post("/api/recurso", response_model=ProdutoOut, status_code=201)
def criar_recurso(dados: ProdutoCreate, db: Session = Depends(get_db)):
    """Cria um novo produto no banco de dados."""
    # Verifica se a categoria existe
    categoria = db.query(Categoria).filter(Categoria.id == dados.categoria_id).first()
    if not categoria:
        raise HTTPException(status_code=400, detail="Categoria não encontrada")

    produto = Produto(
        nome=dados.nome,
        descricao=dados.descricao,
        preco=dados.preco,
        tags=dados.tags,
        categoria_id=dados.categoria_id,
    )
    db.add(produto)
    db.commit()
    db.refresh(produto)

    return produto
