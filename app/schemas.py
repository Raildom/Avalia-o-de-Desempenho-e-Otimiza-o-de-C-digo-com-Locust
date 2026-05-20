"""
Schemas Pydantic para validação de request/response da API.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── Categoria ────────────────────────────────────────────────

class CategoriaOut(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Produto ──────────────────────────────────────────────────

class ProdutoCreate(BaseModel):
    """Schema para criação de um novo produto via POST."""
    nome: str = Field(..., min_length=1, max_length=200)
    descricao: Optional[str] = None
    preco: float = Field(..., gt=0)
    tags: Optional[str] = None
    categoria_id: int = Field(..., gt=0)


class ProdutoOut(BaseModel):
    """Schema de resposta para um produto."""
    id: int
    nome: str
    descricao: Optional[str] = None
    preco: float
    tags: Optional[str] = None
    categoria_id: int

    model_config = {"from_attributes": True}


class ProdutoDetalhe(ProdutoOut):
    """Schema de resposta para produto com detalhes da categoria."""
    categoria: CategoriaOut


# ── Relatório (endpoint lento) ───────────────────────────────

class ProdutoRelatorio(BaseModel):
    """Item do relatório gerado pelo endpoint lento."""
    id: int
    nome: str
    preco: float
    categoria_nome: str
    resumo: str


class RelatorioOut(BaseModel):
    """Resposta do endpoint /api/recurso-lento."""
    total_produtos: int
    itens: list[ProdutoRelatorio]


# ── Status ───────────────────────────────────────────────────

class StatusOut(BaseModel):
    status: str
    timestamp: str
    total_produtos: int
    total_categorias: int
