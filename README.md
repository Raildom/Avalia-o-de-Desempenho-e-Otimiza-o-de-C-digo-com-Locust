# Avaliação de Desempenho e Otimização de Código com Locust

Projeto acadêmico para avaliar o desempenho de uma API REST monolítica, identificar gargalos de código e medir o impacto de refatorações usando o **Locust** como ferramenta de teste de carga.

## 📁 Estrutura do Projeto

```
├── app/                      # API REST (FastAPI)
│   ├── main.py               # Entrypoint
│   ├── database.py           # Configuração SQLite + seed
│   ├── models.py             # Modelos SQLAlchemy
│   ├── schemas.py            # Schemas Pydantic
│   └── routers/
│       ├── slow.py           # GET /api/recurso-lento (gargalo)
│       ├── detail.py         # GET /api/recurso-detalhe/{id}
│       ├── status.py         # GET /api/status
│       └── create.py         # POST /api/recurso
├── locust/
│   └── locustfile.py         # Plano de teste de carga
├── scripts/
│   ├── run_project.sh        # Executa TUDO (Baseline + Otimizado + Relatório)
│   └── generate_report.py    # Gera tabelas e gráficos comparativos
├── results/                  # Resultados dos testes (gerado automaticamente)
│   ├── baseline/             # CSVs da Fase 1
│   ├── optimized/            # CSVs da Fase 2
│   └── summary/              # Tabelas CSV + gráficos PNG
├── requirements.txt
└── README.md
```

## 🚀 Como Reproduzir

### Pré-requisitos

- Python 3.10+
- pip

### 1. Clonar e instalar dependências

```bash
git clone <https://github.com/Raildom/Avalia-o-de-Desempenho-e-Otimiza-o-de-C-digo-com-Locust.git>
cd Avalia-o-de-Desempenho-e-Otimiza-o-de-C-digo-com-Locust
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Executar tudo de uma vez

```bash
chmod +x scripts/run_project.sh
./scripts/run_project.sh
```

O script executa automaticamente:
1. **Fase 1 (Baseline)** — API com gargalo, 5 repetições × 5 min × 50 usuários
2. **Fase 2 (Otimizado)** — API refatorada, 5 repetições × 5 min × 50 usuários
3. **Relatório** — Tabelas comparativas + 4 gráficos PNG

Os resultados ficam em `results/summary/`.

### (Opcional) Testar a API manualmente

```bash
# Modo Baseline (com gargalo)
uvicorn app.main:app --reload

# Modo Otimizado (sem gargalo)
OPTIMIZED=true uvicorn app.main:app --reload
```

Documentação interativa: http://localhost:8000/docs

## 🔍 Endpoints

| Endpoint | Método | Peso | Descrição |
|---|---|---|---|
| `/api/recurso-lento` | GET | 40% | Relatório completo (contém o gargalo) |
| `/api/recurso-detalhe/{id}` | GET | 30% | Consulta produto por ID (indexada) |
| `/api/status` | GET | 20% | Healthcheck leve |
| `/api/recurso` | POST | 10% | Cadastro de novo produto |

## 🐛 O Gargalo

O endpoint `/api/recurso-lento` na versão **Baseline** possui três problemas intencionais:

1. **N+1 Queries**: Para cada um dos 1000 produtos, uma query separada busca a categoria (1001 queries por request)
2. **Concatenação ineficiente**: Strings concatenadas com `+=` em loop (complexidade O(n²))
3. **Regex recompilado**: `re.compile()` chamado dentro de cada iteração do loop

### Otimizações aplicadas

1. **JOIN único**: Uma query com `joinedload()` substitui as 1001 queries
2. **List + join**: Strings construídas com lista e `"".join()`
3. **Regex pré-compilado**: Compilado uma vez no nível do módulo
4. **Cache em memória**: Resultado mantido em cache por 30 segundos

## 📊 Métricas Coletadas

- Tempo médio de resposta (ms)
- Tempo máximo de resposta (ms)
- Requisições por segundo (req/s)
- Total de requisições
- Erros (4xx/5xx) e taxa de sucesso (%)

## ⚙️ Configuração dos Testes

| Parâmetro | Valor |
|---|---|
| Usuários simultâneos | 50 |
| Spawn rate | 10 users/s |
| Duração por teste | 5 minutos |
| Warm-up descartado | 1º minuto |
| Repetições por fase | 5 |
| Workers da API | 1 |
