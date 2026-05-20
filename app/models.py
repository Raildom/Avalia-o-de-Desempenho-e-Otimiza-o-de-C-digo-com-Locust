"""
Modelos SQLAlchemy para o banco de dados.
Define as tabelas Produto e Categoria.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Categoria(Base):
    """Tabela de categorias de produtos."""

    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False, unique=True)
    descricao = Column(Text, nullable=True)

    produtos = relationship("Produto", back_populates="categoria")

    def __repr__(self):
        return f"<Categoria(id={self.id}, nome='{self.nome}')>"


class Produto(Base):
    """Tabela de produtos - entidade principal da API."""

    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=True)
    preco = Column(Float, nullable=False)
    tags = Column(String(500), nullable=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)

    categoria = relationship("Categoria", back_populates="produtos")

    def __repr__(self):
        return f"<Produto(id={self.id}, nome='{self.nome}')>"
