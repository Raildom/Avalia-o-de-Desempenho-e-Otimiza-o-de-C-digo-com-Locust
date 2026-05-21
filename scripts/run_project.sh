#!/usr/bin/env bash
# ------------------------------------------------------------
#  run_all.sh - Executa TUDO automaticamente:
#    1. Fase 1 (Baseline) - 5 repetições
#    2. Fase 2 (Otimizado) - 5 repetições
#    3. Gera relatório comparativo com gráficos
# ------------------------------------------------------------

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
BASELINE_DIR="$PROJECT_DIR/results/baseline"
OPTIMIZED_DIR="$PROJECT_DIR/results/optimized"
LOCUSTFILE="$PROJECT_DIR/locust/locustfile.py"
REPORT_SCRIPT="$PROJECT_DIR/scripts/generate_report.py"
SUMMARY_FILE="$PROJECT_DIR/results/resumo.csv"

REPETICOES=5
USUARIOS=50
SPAWN_RATE=10
DURACAO="1m"
HOST="http://localhost:8000"
PORT=8000

# -- Ativar venv ---------------------------------------------
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "[ERRO] Virtualenv não encontrado em $VENV_DIR"
    echo "       Crie com: python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

# -- Função: esperar API ficar pronta ------------------------
wait_for_api() {
    echo "       Aguardando API inicializar..."
    for i in $(seq 1 30); do
        if curl -s "$HOST/api/status" > /dev/null 2>&1; then
            echo "       API pronta!"
            return 0
        fi
        sleep 1
    done
    echo "         API não respondeu em 30s"
    exit 1
}

# -- Função: matar processo na porta -------------------------
kill_api() {
    local pid
    pid=$(lsof -ti :$PORT 2>/dev/null || true)
    if [ -n "$pid" ]; then
        kill "$pid" 2>/dev/null || true
        sleep 2
    fi
}

# -- Função: limpar resultados extras ----------------------
cleanup_results() {
    local results_dir="$PROJECT_DIR/results"
    if [ -d "$results_dir" ]; then
        rm -rf "$results_dir/summary"
        find "$results_dir" -type f ! -name "*.csv" -delete
        find "$results_dir" -type d -empty -delete
    fi
}

# -- Função: rodar uma fase ----------------------------------
run_phase() {
    local FASE="$1"       # "baseline" ou "optimized"
    local ENV_VAL="$2"    # "false" ou "true"
    local LABEL="$3"      # Nome para exibição
    local RESULTS="$4"    # Diretório de resultados

    echo ""
    echo "======================================================"
    echo "  $LABEL"
    echo "======================================================"

    mkdir -p "$RESULTS"
    rm -f "$PROJECT_DIR/data.db"
    kill_api

    echo "[1/2] Iniciando API ($FASE)..."
    cd "$PROJECT_DIR"
    OPTIMIZED="$ENV_VAL" uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 &
    API_PID=$!
    wait_for_api

    echo "[2/2] Executando $REPETICOES repetições..."
    echo ""

    for RUN in $(seq 1 $REPETICOES); do
        RUN_DIR="$RESULTS/run_$RUN"
        mkdir -p "$RUN_DIR"
        echo "  --- Repetição $RUN/$REPETICOES ---"

        locust \
            -f "$LOCUSTFILE" \
            --host "$HOST" \
            --users "$USUARIOS" \
            --spawn-rate "$SPAWN_RATE" \
            --run-time "$DURACAO" \
            --headless \
            --csv "$RUN_DIR/results" \
            --csv-full-history \
            --only-summary

        echo "      Salvo em $RUN_DIR/"

        if [ "$RUN" -lt "$REPETICOES" ]; then
            sleep 5
        fi
    done

    echo ""
    echo "  Encerrando API..."
    kill $API_PID 2>/dev/null || true
    wait $API_PID 2>/dev/null || true
    echo "  $LABEL concluída!"
}

# -- MAIN ----------------------------------------------------

echo "+------------------------------------------------------+"
echo "|  TRABALHO 7 - Avaliação de Desempenho com Locust     |"
echo "|  Execução completa: Baseline + Otimizado + Relatório |"
echo "+------------------------------------------------------+"
echo ""
echo "  Configuração:"
echo "    Usuários:    $USUARIOS"
echo "    Spawn rate:  $SPAWN_RATE/s"
echo "    Duração:     $DURACAO por repetição"
echo "    Repetições:  $REPETICOES por fase"
echo "    Total est.:  ~$((REPETICOES * 5 * 2 + 5)) minutos"

# Fase 1
run_phase "baseline" "false" \
    "FASE 1 - BASELINE (Código com Gargalo)" \
    "$BASELINE_DIR"

# Fase 2
run_phase "optimized" "true" \
    "FASE 2 - OTIMIZADO (Código Refatorado)" \
    "$OPTIMIZED_DIR"

# Relatório
echo ""
echo "======================================================"
echo "  GERANDO RELATÓRIO COMPARATIVO"
echo "======================================================"
python "$REPORT_SCRIPT"
cleanup_results

echo ""
echo "+------------------------------------------------------+"
echo "|  TUDO CONCLUÍDO!                                     |"
echo "|                                                      |"
echo "|  Resultados em: results/                             |"
echo "|    - CSVs do Locust em baseline/ e optimized/        |"
echo "|    - resumo.csv (tabela de resumo)                   |"
echo "|                                                      |"
echo "|  Graficos em: reports/graphs/                        |"
echo "+------------------------------------------------------+"
