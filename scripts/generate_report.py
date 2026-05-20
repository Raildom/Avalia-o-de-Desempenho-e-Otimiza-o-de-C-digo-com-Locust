#!/usr/bin/env python3
"""
generate_report.py - Gera relatório comparativo Baseline vs Otimizado.

Lê os CSVs das 5 repetições de cada fase, calcula médias das métricas,
gera tabelas comparativas e gráficos com matplotlib.
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_DIR = os.path.join(PROJECT_DIR, "results", "baseline")
OPTIMIZED_DIR = os.path.join(PROJECT_DIR, "results", "optimized")
SUMMARY_DIR = os.path.join(PROJECT_DIR, "results", "summary")
WARMUP_SECONDS = int(os.environ.get("WARMUP_SECONDS", "60"))


def carregar_history(fase_dir: str) -> pd.DataFrame:
    """Carrega e agrega os CSVs de stats_history de todas as repetições."""
    all_runs = []
    for run_name in sorted(os.listdir(fase_dir)):
        run_dir = os.path.join(fase_dir, run_name)
        if not os.path.isdir(run_dir):
            continue
        stats_file = os.path.join(run_dir, "results_stats_history.csv")
        if not os.path.exists(stats_file):
            print(f"  [AVISO] Não encontrado: {stats_file}")
            continue
        df = pd.read_csv(stats_file)
        df["run"] = run_name
        all_runs.append(df)

    if not all_runs:
        print(f"  [ERRO] Nenhum CSV encontrado em {fase_dir}")
        sys.exit(1)

    return pd.concat(all_runs, ignore_index=True)


def _metricas_por_run(history_df: pd.DataFrame) -> pd.DataFrame:
    """Calcula metricas por run, descartando o warm-up inicial."""
    history_df = history_df.copy()
    history_df["Timestamp"] = pd.to_numeric(history_df["Timestamp"], errors="coerce")
    history_df["Requests/s"] = pd.to_numeric(history_df["Requests/s"], errors="coerce")
    history_df["Total Request Count"] = pd.to_numeric(
        history_df["Total Request Count"], errors="coerce"
    )
    history_df["Total Failure Count"] = pd.to_numeric(
        history_df["Total Failure Count"], errors="coerce"
    )
    history_df["Total Average Response Time"] = pd.to_numeric(
        history_df["Total Average Response Time"], errors="coerce"
    )
    history_df["Total Max Response Time"] = pd.to_numeric(
        history_df["Total Max Response Time"], errors="coerce"
    )
    history_df["100%"] = pd.to_numeric(history_df["100%"], errors="coerce")

    rows = []
    for run_name, run_df in history_df.groupby("run"):
        run_df = run_df.sort_values("Timestamp")
        min_ts = run_df["Timestamp"].min()
        max_ts = run_df["Timestamp"].max()
        warmup_end = min_ts + WARMUP_SECONDS
        if (max_ts - min_ts) < WARMUP_SECONDS:
            warmup_end = min_ts

        for endpoint, ep_df in run_df.groupby("Name"):
            ep_df = ep_df.sort_values("Timestamp")

            window_df = ep_df[ep_df["Timestamp"] >= warmup_end]
            window_count = float(window_df["Total Request Count"].sum())
            window_fail = float(window_df["Total Failure Count"].sum())

            if window_count > 0:
                weighted_sum = (window_df["Total Average Response Time"] * window_df["Total Request Count"]).sum()
                window_avg = float(weighted_sum / window_count)
            else:
                window_avg = 0.0
            window_rps = (
                window_df["Requests/s"].mean()
                if not window_df.empty
                else 0.0
            )
            window_max = (
                window_df["100%"].max()
                if not window_df.empty
                else 0.0
            )

            rows.append({
                "run": run_name,
                "Endpoint": endpoint,
                "Tempo Médio (ms)": window_avg,
                "Tempo Máximo (ms)": window_max,
                "Req/s": window_rps,
                "Total Requisições": window_count,
                "Erros": window_fail,
            })

    return pd.DataFrame(rows)


def calcular_metricas(history_df: pd.DataFrame) -> pd.DataFrame:
    """Calcula a media das metricas entre as repeticoes, por endpoint."""
    per_run = _metricas_por_run(history_df)

    metricas = per_run.groupby("Endpoint").agg({
        "Tempo Médio (ms)": "mean",
        "Tempo Máximo (ms)": "mean",
        "Req/s": "mean",
        "Total Requisições": "sum",
        "Erros": "sum",
    }).reset_index()

    metricas["Taxa Sucesso (%)"] = (
        (1 - metricas["Erros"] / metricas["Total Requisições"].replace(0, 1)) * 100
    ).round(2)

    return metricas


def gerar_tabela_comparativa(baseline: pd.DataFrame, optimized: pd.DataFrame) -> pd.DataFrame:
    """Gera tabela comparativa entre Baseline e Otimizado."""
    merged = baseline.merge(
        optimized,
        on="Endpoint",
        suffixes=(" (Baseline)", " (Otimizado)"),
    )
    return merged


def gerar_graficos(baseline: pd.DataFrame, optimized: pd.DataFrame):
    """Gera gráficos comparativos com matplotlib."""
    os.makedirs(SUMMARY_DIR, exist_ok=True)

    # Filtrar endpoints que existem em ambos
    endpoints = baseline[baseline["Endpoint"] != "Aggregated"]["Endpoint"].tolist()
    endpoints_otim = optimized[optimized["Endpoint"] != "Aggregated"]["Endpoint"].tolist()
    endpoints = [e for e in endpoints if e in endpoints_otim]

    if not endpoints:
        print("  [AVISO] Sem endpoints em comum para gerar gráficos.")
        return

    base_data = baseline[baseline["Endpoint"].isin(endpoints)].set_index("Endpoint")
    opt_data = optimized[optimized["Endpoint"].isin(endpoints)].set_index("Endpoint")

    x = np.arange(len(endpoints))
    width = 0.35
    labels = [e.replace("/api/", "") for e in endpoints]

    # -- Gráfico 1: Tempo Médio de Resposta ------------------
    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width/2, base_data.loc[endpoints, "Tempo Médio (ms)"],
                   width, label="Baseline", color="#e74c3c", alpha=0.85)
    bars2 = ax.bar(x + width/2, opt_data.loc[endpoints, "Tempo Médio (ms)"],
                   width, label="Otimizado", color="#2ecc71", alpha=0.85)
    ax.set_xlabel("Endpoint", fontsize=12)
    ax.set_ylabel("Tempo Médio (ms)", fontsize=12)
    ax.set_title("Tempo Médio de Resposta - Baseline vs Otimizado", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.legend()
    ax.bar_label(bars1, fmt="%.1f", padding=3, fontsize=8)
    ax.bar_label(bars2, fmt="%.1f", padding=3, fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(SUMMARY_DIR, "tempo_medio.png"), dpi=150)
    plt.close()
    print("  tempo_medio.png")

    # -- Gráfico 2: Tempo Máximo de Resposta -----------------
    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width/2, base_data.loc[endpoints, "Tempo Máximo (ms)"],
                   width, label="Baseline", color="#e74c3c", alpha=0.85)
    bars2 = ax.bar(x + width/2, opt_data.loc[endpoints, "Tempo Máximo (ms)"],
                   width, label="Otimizado", color="#2ecc71", alpha=0.85)
    ax.set_xlabel("Endpoint", fontsize=12)
    ax.set_ylabel("Tempo Máximo (ms)", fontsize=12)
    ax.set_title("Tempo Máximo de Resposta - Baseline vs Otimizado", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.legend()
    ax.bar_label(bars1, fmt="%.1f", padding=3, fontsize=8)
    ax.bar_label(bars2, fmt="%.1f", padding=3, fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(SUMMARY_DIR, "tempo_maximo.png"), dpi=150)
    plt.close()
    print("  tempo_maximo.png")

    # -- Gráfico 3: Requisições por Segundo ------------------
    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width/2, base_data.loc[endpoints, "Req/s"],
                   width, label="Baseline", color="#e74c3c", alpha=0.85)
    bars2 = ax.bar(x + width/2, opt_data.loc[endpoints, "Req/s"],
                   width, label="Otimizado", color="#2ecc71", alpha=0.85)
    ax.set_xlabel("Endpoint", fontsize=12)
    ax.set_ylabel("Requisições/s", fontsize=12)
    ax.set_title("Throughput (Req/s) - Baseline vs Otimizado", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.legend()
    ax.bar_label(bars1, fmt="%.2f", padding=3, fontsize=8)
    ax.bar_label(bars2, fmt="%.2f", padding=3, fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(SUMMARY_DIR, "throughput.png"), dpi=150)
    plt.close()
    print("  throughput.png")

    # -- Gráfico 4: Comparativo Agregado ---------------------
    agg_base = baseline[baseline["Endpoint"] == "Aggregated"]
    agg_opt = optimized[optimized["Endpoint"] == "Aggregated"]

    if not agg_base.empty and not agg_opt.empty:
        metricas = ["Tempo Médio (ms)", "Tempo Máximo (ms)", "Req/s"]
        fig, axes = plt.subplots(1, 3, figsize=(16, 5))

        for i, metrica in enumerate(metricas):
            val_base = agg_base[metrica].values[0]
            val_opt = agg_opt[metrica].values[0]
            bars = axes[i].bar(
                ["Baseline", "Otimizado"],
                [val_base, val_opt],
                color=["#e74c3c", "#2ecc71"],
                alpha=0.85,
            )
            axes[i].set_title(metrica, fontsize=12, fontweight="bold")
            axes[i].bar_label(bars, fmt="%.2f", padding=3)

        plt.suptitle("Métricas Agregadas - Baseline vs Otimizado",
                     fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(os.path.join(SUMMARY_DIR, "agregado.png"), dpi=150)
        plt.close()
        print("  agregado.png")


def main():
    print("===================================================")
    print("  GERAÇÃO DE RELATÓRIO COMPARATIVO")
    print("===================================================")

    os.makedirs(SUMMARY_DIR, exist_ok=True)

    # Carregar dados
    print("\n[1/4] Carregando dados do Baseline...")
    df_baseline = carregar_history(BASELINE_DIR)

    print("[2/4] Carregando dados do Otimizado...")
    df_optimized = carregar_history(OPTIMIZED_DIR)

    # Calcular métricas
    print("[3/4] Calculando métricas")
    metricas_base = calcular_metricas(df_baseline)
    metricas_opt = calcular_metricas(df_optimized)

    # Salvar tabelas
    metricas_base.to_csv(os.path.join(SUMMARY_DIR, "baseline_resumo.csv"), index=False)
    metricas_opt.to_csv(os.path.join(SUMMARY_DIR, "otimizado_resumo.csv"), index=False)

    comparativo = gerar_tabela_comparativa(metricas_base, metricas_opt)
    comparativo.to_csv(os.path.join(SUMMARY_DIR, "comparativo.csv"), index=False)

    print("\n  Tabelas salvas:")
    print("    baseline_resumo.csv")
    print("    otimizado_resumo.csv")
    print("    comparativo.csv")

    # Gerar gráficos
    print("\n[4/4] Gerando gráficos...")
    gerar_graficos(metricas_base, metricas_opt)

    # Exibir resumo no terminal
    print("\n===================================================")
    print("  RESUMO COMPARATIVO")
    print("===================================================")
    print("\n-- Baseline --")
    print(metricas_base.to_string(index=False))
    print("\n-- Otimizado --")
    print(metricas_opt.to_string(index=False))
    print("\n  Relatório completo em: results/summary/")


if __name__ == "__main__":
    main()
