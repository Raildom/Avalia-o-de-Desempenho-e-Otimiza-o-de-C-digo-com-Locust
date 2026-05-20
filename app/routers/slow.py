"""
Router: GET /api/recurso-lento

Este endpoint contém o GARGALO PROPOSITAL do sistema.

─── VERSÃO BASELINE (OPTIMIZED=false) ───
Problemas intencionais:
  1. N+1 Queries: para cada produto, faz uma query separada para buscar a categoria
  2. Concatenação de strings ineficiente com += em loop
  3. Regex compilado a cada chamada (re.compile dentro do handler)
  4. Sem cache — recalcula tudo a cada requisição

─── VERSÃO OTIMIZADA (OPTIMIZED=true) ───
Correções aplicadas:
  1. Uma única query com JOIN (eliminando N+1)
  2. Strings com list + join
  3. Regex pré-compilado no nível do módulo
  4. Cache em memória com TTL de 30 segundos
"""

import os
import re
import time
from functools import lru_cache

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Produto, Categoria
from app.schemas import RelatorioOut, ProdutoRelatorio

router = APIRouter()

# Variável de ambiente para alternar entre versão lenta e otimizada
OPTIMIZED = os.environ.get("OPTIMIZED", "false").lower() == "true"

# ── Regex pré-compilado para a versão otimizada ─────────────
_PATTERN_TAGS = re.compile(r",\s*")


# ────────────────────────────────────────────────────────────
#  VERSÃO BASELINE — LENTA (com gargalo proposital)
# ────────────────────────────────────────────────────────────

def _gerar_relatorio_lento(db: Session) -> dict:
    """
    Gera o relatório de forma INEFICIENTE:
    - Busca todos os produtos (1 query)
    - Para CADA produto, faz uma query separada na tabela de categorias (N queries)
    - Concatena strings com += (O(n²) em Python)
    - Compila regex a cada iteração
    """
    # 1 query para buscar todos os produtos (sem JOIN)
    produtos = db.query(Produto).all()

    itens = []
    for produto in produtos:
        # N+1: query individual para buscar a categoria de CADA produto
        categoria = db.query(Categoria).filter(
            Categoria.id == produto.categoria_id
        ).first()

        # Concatenação ineficiente de strings com +=
        resumo = ""
        resumo += f"Produto: {produto.nome}. "
        resumo += f"Categoria: {categoria.nome}. "
        resumo += f"Preço: R$ {produto.preco:.2f}. "

        # Regex compilado a CADA iteração (desnecessário)
        pattern = re.compile(r",\s*")
        if produto.tags:
            tags_list = pattern.split(produto.tags)
            resumo += f"Tags: {', '.join(tags_list)}. "

        # Processamento extra desnecessário: reverter e re-reverter a descrição
        if produto.descricao:
            desc_reversed = produto.descricao[::-1]
            desc_original = desc_reversed[::-1]
            resumo += f"Descrição: {desc_original[:80]}..."

        itens.append(ProdutoRelatorio(
            id=produto.id,
            nome=produto.nome,
            preco=produto.preco,
            categoria_nome=categoria.nome,
            resumo=resumo,
        ))

    return {"total_produtos": len(itens), "itens": itens}


# ────────────────────────────────────────────────────────────
#  VERSÃO OTIMIZADA — RÁPIDA
# ────────────────────────────────────────────────────────────

# Cache simples com TTL
_cache: dict = {"data": None, "timestamp": 0}
_CACHE_TTL = 30  # segundos


def _gerar_relatorio_otimizado(db: Session) -> dict:
    """
    Gera o relatório de forma EFICIENTE:
    - Uma única query com JOIN (eager loading)
    - Strings construídas com list + join
    - Regex pré-compilado no nível do módulo
    - Cache em memória com TTL de 30 segundos
    """
    now = time.time()

    # Verificar cache
    if _cache["data"] is not None and (now - _cache["timestamp"]) < _CACHE_TTL:
        return _cache["data"]

    # UMA ÚNICA query com JOIN — elimina o problema N+1
    produtos = (
        db.query(Produto)
        .options(joinedload(Produto.categoria))
        .all()
    )

    itens = []
    for produto in produtos:
        # Construção eficiente de strings com lista + join
        parts = [
            f"Produto: {produto.nome}",
            f"Categoria: {produto.categoria.nome}",
            f"Preço: R$ {produto.preco:.2f}",
        ]

        if produto.tags:
            # Usa regex pré-compilado no nível do módulo
            tags_list = _PATTERN_TAGS.split(produto.tags)
            parts.append(f"Tags: {', '.join(tags_list)}")

        if produto.descricao:
            parts.append(f"Descrição: {produto.descricao[:80]}...")

        resumo = ". ".join(parts) + "."

        itens.append(ProdutoRelatorio(
            id=produto.id,
            nome=produto.nome,
            preco=produto.preco,
            categoria_nome=produto.categoria.nome,
            resumo=resumo,
        ))

    result = {"total_produtos": len(itens), "itens": itens}

    # Atualizar cache
    _cache["data"] = result
    _cache["timestamp"] = now

    return result


# ────────────────────────────────────────────────────────────
#  ENDPOINT
# ────────────────────────────────────────────────────────────

@router.get("/api/recurso-lento", response_model=RelatorioOut)
def recurso_lento(db: Session = Depends(get_db)):
    """
    Gera um relatório com todos os produtos e suas categorias.
    A versão (lenta ou otimizada) depende da variável OPTIMIZED.
    """
    if OPTIMIZED:
        return _gerar_relatorio_otimizado(db)
    else:
        return _gerar_relatorio_lento(db)
