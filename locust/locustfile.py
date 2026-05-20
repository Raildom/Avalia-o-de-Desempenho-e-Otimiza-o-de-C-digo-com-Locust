"""
Locustfile — Plano de teste de carga para a API Monolítica.

Mix de Carga (Workload Mix):
  - GET  /api/recurso-lento         → 40% dos acessos (gargalo)
  - GET  /api/recurso-detalhe/{id}  → 30% dos acessos (consulta indexada)
  - GET  /api/status                → 20% dos acessos (healthcheck)
  - POST /api/recurso               → 10% dos acessos (cadastro)
"""

import random
from locust import HttpUser, task, between


class ApiUser(HttpUser):
    """
    Simula um usuário real da API com distribuição de acessos realista.
    Espera entre 1 e 2 segundos entre cada requisição.
    """

    wait_time = between(1, 2)

    # ── 40% — Endpoint com gargalo ──────────────────────────

    @task(4)
    def recurso_lento(self):
        """Acessa o endpoint de relatório (gargalo de desempenho)."""
        self.client.get("/api/recurso-lento", name="/api/recurso-lento")

    # ── 30% — Consulta por ID ───────────────────────────────

    @task(3)
    def recurso_detalhe(self):
        """Consulta um produto aleatório por ID (1 a 1000)."""
        produto_id = random.randint(1, 1000)
        self.client.get(
            f"/api/recurso-detalhe/{produto_id}",
            name="/api/recurso-detalhe/{id}",
        )

    # ── 20% — Healthcheck ──────────────────────────────────

    @task(2)
    def status(self):
        """Verifica o status da aplicação."""
        self.client.get("/api/status", name="/api/status")

    # ── 10% — Cadastro ─────────────────────────────────────

    @task(1)
    def criar_recurso(self):
        """Cria um novo produto com dados aleatórios."""
        payload = {
            "nome": f"Produto Teste {random.randint(1, 99999)}",
            "descricao": "Produto criado durante teste de carga Locust",
            "preco": round(random.uniform(10.0, 500.0), 2),
            "tags": "teste, locust, carga",
            "categoria_id": random.randint(1, 10),
        }
        self.client.post("/api/recurso", json=payload, name="/api/recurso")
