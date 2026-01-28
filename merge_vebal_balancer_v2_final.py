"""
Merge veBAL_pre_merge_2.csv com balancer_v2_pre_final_merge.csv para gerar o dataset final.
- Base: balancer_v2 (uma linha por day × gauge), para preservar votes_received.sum() = total_votes.sum() do b2.
- Join: left de b2 para veBAL por (gauge_address, date). Métricas de pool (TVL, fees, etc.) vêm do veBAL.
- core_non_core: inteiro 0/1 (is_core). 1 = core, 0 = non_core.
- Saída: balancer_v2_merged.csv com as colunas exigidas pela aplicação Streamlit.
"""

import pandas as pd
import numpy as np
import os

DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "balancer_v2_merged.csv")

FINAL_COLUMNS = [
    "blockchain",
    "project",
    "version",
    "block_date",
    "project_contract_address",
    "pool_symbol",
    "pool_type",
    "swap_amount_usd",
    "tvl_usd",
    "tvl_eth",
    "total_protocol_fee_usd",
    "protocol_fee_amount_usd",
    "swap_fee_usd",
    "yield_fee_usd",
    "swap_fee_%",
    "core_non_core",
    "direct_incentives",
    "bal_emited_votes",
    "votes_received",
]


def normalize_gauge(addr):
    if pd.isna(addr):
        return None
    s = str(addr).strip().lower()
    if s in ("", "nan"):
        return None
    return s


def main():
    print("=" * 60)
    print("Merge final: balancer_v2 (base) + veBAL -> balancer_v2_merged.csv")
    print("=" * 60)

    vebal_path = os.path.join(DATA_DIR, "veBAL_pre_merge_2.csv")
    b2_path = os.path.join(DATA_DIR, "balancer_v2_pre_final_merge.csv")

    print("\n📖 Carregando arquivos...")
    vebal = pd.read_csv(vebal_path)
    b2 = pd.read_csv(b2_path)
    print(f"   veBAL: {len(vebal):,} linhas")
    print(f"   balancer_v2: {len(b2):,} linhas")
    b2_votes_sum = b2["total_votes"].sum()
    print(f"   total_votes (b2): {b2_votes_sum:,.2f}")

    # Preparar veBAL: (gauge, date) -> métricas de pool
    print("\n🔧 Preparando veBAL...")
    vebal["block_date_dt"] = pd.to_datetime(vebal["block_date"], errors="coerce")
    vebal["_date"] = vebal["block_date_dt"].dt.date
    vebal["_gauge_norm"] = vebal["gauge_address"].apply(normalize_gauge)
    vebal_metrics = vebal.dropna(subset=["_gauge_norm"]).copy()
    # Uma linha por (gauge, date) para evitar duplicar linhas do b2 no merge
    vebal_metrics = vebal_metrics.drop_duplicates(subset=["_gauge_norm", "_date"], keep="first")
    cols_vebal = [
        "_gauge_norm", "_date",
        "pool_symbol", "pool_type",
        "swap_amount_usd", "tvl_usd", "tvl_eth",
        "total_protocol_fee_usd", "protocol_fee_amount_usd",
        "swap_fee_usd", "yield_fee_usd", "swap_fee_%",
    ]
    vebal_metrics = vebal_metrics[cols_vebal].copy()
    vebal_metrics = vebal_metrics.rename(columns={
        "pool_symbol": "pool_symbol_vebal",
        "pool_type": "pool_type_vebal",
    })

    # Preparar balancer_v2 como base
    print("🔧 Preparando balancer_v2 (base)...")
    b2["_date"] = pd.to_datetime(b2["day"], errors="coerce").dt.date
    b2["_gauge_norm"] = b2["gauge_address"].apply(normalize_gauge)
    b2 = b2.dropna(subset=["_gauge_norm"]).copy()

    # Merge: b2 LEFT veBAL por (gauge, date). Base = b2.
    print("\n🔗 Merge: balancer_v2 (base) + veBAL por (gauge_address, date)...")
    merged = b2.merge(
        vebal_metrics,
        on=["_gauge_norm", "_date"],
        how="left",
        suffixes=("", "_vebal"),
    )

    # direct_incentives = round_emissions_usd / duration (per day)
    merged["start_dt"] = pd.to_datetime(merged["start_date"], errors="coerce")
    merged["end_dt"] = pd.to_datetime(merged["end_date"], errors="coerce")
    merged["duration_days"] = (
        (merged["end_dt"] - merged["start_dt"]).dt.days
    ).clip(lower=1)
    merged["daily_emissions_usd"] = pd.to_numeric(merged["daily_emissions_usd"], errors="coerce").fillna(0)
    round_agg = merged.groupby(["_gauge_norm", "round_id"], as_index=False).agg(
        round_emissions_usd=("daily_emissions_usd", "sum"),
        duration_days=("duration_days", "first"),
    )
    round_agg["direct_incentives"] = np.where(
        round_agg["duration_days"] > 0,
        round_agg["round_emissions_usd"] / round_agg["duration_days"],
        0.0,
    )
    merged = merged.merge(
        round_agg[["_gauge_norm", "round_id", "direct_incentives"]],
        on=["_gauge_norm", "round_id"],
        how="left",
    )
    merged["direct_incentives"] = merged["direct_incentives"].fillna(0)

    # Montar tabela final
    out = pd.DataFrame()
    out["blockchain"] = merged["blockchain"]
    out["project"] = "balancer"
    out["version"] = 2
    out["block_date"] = merged["day"]
    out["project_contract_address"] = merged["pool_address"]
    # pool_symbol: preferir veBAL se houver match, senão symbol do b2
    out["pool_symbol"] = merged["pool_symbol_vebal"].fillna(merged["symbol"])
    out["pool_type"] = merged["pool_type_vebal"]
    out["swap_amount_usd"] = merged["swap_amount_usd"]
    out["tvl_usd"] = merged["tvl_usd"]
    out["tvl_eth"] = merged["tvl_eth"]
    out["total_protocol_fee_usd"] = merged["total_protocol_fee_usd"]
    out["protocol_fee_amount_usd"] = merged["protocol_fee_amount_usd"]
    out["swap_fee_usd"] = merged["swap_fee_usd"]
    out["yield_fee_usd"] = merged["yield_fee_usd"]
    out["swap_fee_%"] = merged["swap_fee_%"]
    # core_non_core: 0/1 (is_core). 1 = core, 0 = non_core.
    out["core_non_core"] = merged["is_core"].fillna(0).astype(int)
    out["direct_incentives"] = pd.to_numeric(merged["direct_incentives"], errors="coerce").fillna(0)
    out["bal_emited_votes"] = merged["daily_emissions"]
    out["votes_received"] = merged["total_votes"]

    # Tipos numéricos: não preencher métricas veBAL com 0 (mantém NaN onde não há match)
    for c in ["swap_amount_usd", "tvl_usd", "tvl_eth", "total_protocol_fee_usd",
              "protocol_fee_amount_usd", "swap_fee_usd", "yield_fee_usd", "swap_fee_%"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    for c in ["bal_emited_votes", "votes_received"]:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0)

    out = out[FINAL_COLUMNS]

    # Verificação: soma de votos deve bater com b2
    out_votes_sum = out["votes_received"].sum()
    assert abs(out_votes_sum - b2_votes_sum) < 1.0, (
        f"votes_received.sum() = {out_votes_sum:.2f} != total_votes (b2) = {b2_votes_sum:.2f}"
    )

    n_total = len(out)
    n_with_vebal = out["tvl_usd"].notna().sum()
    n_core = (out["core_non_core"] == 1).sum()
    n_non_core = (out["core_non_core"] == 0).sum()

    print(f"\n📊 Resultado:")
    print(f"   Total de linhas: {n_total:,}")
    print(f"   Linhas com match veBAL (métricas): {n_with_vebal:,}")
    print(f"   core_non_core: 1 (core) = {n_core:,}, 0 (non_core) = {n_non_core:,}")
    print(f"   votes_received.sum() = {out_votes_sum:,.2f} (= total_votes b2)")

    print(f"\n💾 Salvando: {OUTPUT_FILE}")
    out.to_csv(OUTPUT_FILE, index=False)
    print("✅ Concluído.")

    return out


if __name__ == "__main__":
    main()
