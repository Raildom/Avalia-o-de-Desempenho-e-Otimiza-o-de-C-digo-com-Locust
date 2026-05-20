"""
Configuração do banco de dados SQLite e seed de dados iniciais.
Popula o banco com ~1000 produtos distribuídos em 10 categorias.
"""

import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models import Base, Categoria, Produto

DATABASE_URL = "sqlite:///./data.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency que fornece uma sessão do banco por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -- Dados para seed ------------------------------------------

CATEGORIAS = [
    ("Eletrônicos", "Dispositivos eletrônicos e gadgets"),
    ("Roupas", "Vestuário masculino e feminino"),
    ("Alimentos", "Produtos alimentícios e bebidas"),
    ("Livros", "Livros físicos e digitais"),
    ("Esportes", "Artigos esportivos e fitness"),
    ("Casa e Jardim", "Móveis, decoração e jardinagem"),
    ("Brinquedos", "Brinquedos e jogos infantis"),
    ("Automotivo", "Peças e acessórios automotivos"),
    ("Saúde", "Produtos de saúde e bem-estar"),
    ("Ferramentas", "Ferramentas manuais e elétricas"),
]

ADJETIVOS = [
    "Premium", "Básico", "Profissional", "Compacto", "Ultra",
    "Max", "Plus", "Eco", "Smart", "Classic", "Turbo", "Master",
    "Pro", "Lite", "Digital", "Super", "Mega", "Power", "Elite", "Prime",
]

SUBSTANTIVOS = {
    "Eletrônicos": ["Fone", "Carregador", "Cabo USB", "Teclado", "Mouse", "Monitor", "Webcam", "HD Externo", "Pendrive", "Caixa de Som"],
    "Roupas": ["Camiseta", "Calça", "Jaqueta", "Moletom", "Bermuda", "Vestido", "Saia", "Blazer", "Meia", "Boné"],
    "Alimentos": ["Café", "Chocolate", "Biscoito", "Suco", "Granola", "Mel", "Azeite", "Massa", "Molho", "Cereal"],
    "Livros": ["Romance", "Thriller", "Biografia", "Manual", "Guia", "Dicionário", "Atlas", "Antologia", "Enciclopédia", "Almanaque"],
    "Esportes": ["Bola", "Raquete", "Luva", "Tênis", "Caneleira", "Haltere", "Corda", "Colchonete", "Mochila", "Garrafa"],
    "Casa e Jardim": ["Vaso", "Luminária", "Cortina", "Tapete", "Almofada", "Prateleira", "Regador", "Pá", "Tesoura de Poda", "Adubo"],
    "Brinquedos": ["Boneco", "Quebra-cabeça", "Jogo de Tabuleiro", "Carrinho", "Lego", "Pelúcia", "Pipa", "Massinha", "Dominó", "Pião"],
    "Automotivo": ["Pneu", "Óleo", "Filtro", "Lâmpada", "Tapete Carro", "Capa Banco", "Antena", "Buzina", "Retrovisor", "Volante"],
    "Saúde": ["Vitamina", "Protetor Solar", "Termômetro", "Balança", "Medidor de Pressão", "Faixa Elástica", "Massageador", "Inalador", "Gel", "Pomada"],
    "Ferramentas": ["Martelo", "Chave", "Alicate", "Furadeira", "Serra", "Parafuso", "Broca", "Trena", "Nível", "Lixa"],
}

TAGS_POOL = [
    "promoção", "novo", "destaque", "importado", "nacional",
    "oferta", "limitado", "exclusivo", "best-seller", "sustentável",
    "orgânico", "artesanal", "premium", "econômico", "tendência",
]


def seed_database(db: Session) -> None:
    """Popula o banco de dados com categorias e ~1000 produtos."""
    # Verifica se já há dados
    if db.query(Categoria).count() > 0:
        return

    # Criar categorias
    categorias_obj = []
    for nome, descricao in CATEGORIAS:
        cat = Categoria(nome=nome, descricao=descricao)
        db.add(cat)
        categorias_obj.append(cat)
    db.flush()

    # Criar ~1000 produtos (100 por categoria)
    random.seed(42)
    for cat in categorias_obj:
        nomes_base = SUBSTANTIVOS[cat.nome]
        for i in range(100):
            adj = random.choice(ADJETIVOS)
            base = random.choice(nomes_base)
            nome_produto = f"{base} {adj} {i + 1}"
            preco = round(random.uniform(5.0, 999.99), 2)
            tags = ", ".join(random.sample(TAGS_POOL, k=random.randint(1, 4)))
            descricao = (
                f"{nome_produto} da categoria {cat.nome}. "
                f"Produto de alta qualidade com garantia estendida. "
                f"Ideal para uso diário e profissional. "
                f"Especificações técnicas detalhadas disponíveis sob consulta."
            )

            produto = Produto(
                nome=nome_produto,
                descricao=descricao,
                preco=preco,
                tags=tags,
                categoria_id=cat.id,
            )
            db.add(produto)

    db.commit()
    print(f"[SEED] Banco populado: {db.query(Categoria).count()} categorias, {db.query(Produto).count()} produtos.")


def init_db() -> None:
    """Cria as tabelas e popula o banco de dados."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
