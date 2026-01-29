"""
Merge: balancer_v2_financial_master_final_testing.csv + veBAL_pre_merge_2.csv + votos/emissões.
- Financial + veBAL_pre_merge_2: blockchain, block_date, project_contract_address; veBAL adiciona
  project_contract_address_norm, gauge_address; financial adiciona is_core_pool.
- Votos e emissões vêm de vebal_votes_valid.csv (agregados por pool/dia para não duplicar).
Saída: Aleluia.csv (com colunas de votos e emissões).
"""

import pandas as pd
import os

VOTES_PATH = 'data/vebal_votes_valid.csv'

def load_data():
    """Carrega os três CSVs (financial, veBAL keys, votos)."""
    print("Carregando CSVs...")
    df_financial = pd.read_csv('data/balancer_v2_financial_master_final_testing.csv')
    df_vebal = pd.read_csv('data/veBAL_pre_merge_2.csv')
    df_votes = pd.read_csv(VOTES_PATH)

    print(f"Financial (testing): {len(df_financial)} linhas, {len(df_financial.columns)} colunas")
    print(f"veBAL_pre_merge_2:   {len(df_vebal)} linhas, {len(df_vebal.columns)} colunas")
    print(f"Votos (vebal_votes_valid): {len(df_votes)} linhas, {len(df_votes.columns)} colunas")
    return df_financial, df_vebal, df_votes


def normalize_date(ser):
    """Normaliza para data (string YYYY-MM-DD) para fazer match entre block_date e day."""
    dt = pd.to_datetime(ser, utc=True, errors='coerce')
    return dt.dt.strftime('%Y-%m-%d')


def prepare_vebal_for_merge(df_vebal):
    """
    veBAL: uma linha por (blockchain, project_contract_address, block_date),
    com project_contract_address_norm e gauge_address (primeiro por grupo).
    """
    key_cols = ['blockchain', 'project_contract_address', 'block_date']
    extra_cols = ['project_contract_address_norm', 'gauge_address']
    keep = [c for c in extra_cols if c in df_vebal.columns]
    if not keep:
        return df_vebal[key_cols].drop_duplicates()
    return df_vebal.groupby(key_cols, as_index=False)[keep].first()


def prepare_votes_for_merge(df_votes):
    """
    Agrega votos por (blockchain, pool_address, day): soma total_votes, daily_emissions,
    daily_emissions_usd, daily_fees; first round_id, start_date, end_date, symbol;
    soma pct_votes_in_round (pode ser >1 quando há vários gauges no mesmo pool).
    """
    key_cols = ['blockchain', 'pool_address', 'day']
    sum_cols = ['total_votes', 'daily_emissions', 'daily_emissions_usd', 'daily_fees', 'pct_votes_in_round']
    sum_cols = [c for c in sum_cols if c in df_votes.columns]
    first_cols = [c for c in ['round_id', 'start_date', 'end_date', 'symbol'] if c in df_votes.columns]

    agg_dict = {c: 'sum' for c in sum_cols}
    for c in first_cols:
        agg_dict[c] = 'first'

    return df_votes.groupby(key_cols, as_index=False).agg(agg_dict)


def perform_merge(df_financial, df_vebal, df_votes):
    """1) Merge financial + veBAL keys. 2) Normaliza datas e merge com votos (left)."""
    print("\nPreparando veBAL (uma linha por pool/dia)...")
    df_vebal_keys = prepare_vebal_for_merge(df_vebal)

    print("Fazendo merge outer (financial + veBAL keys)...")
    df_merged = pd.merge(
        df_financial,
        df_vebal_keys,
        on=['blockchain', 'project_contract_address', 'block_date'],
        how='outer',
    )
    print(f"Base merge: {len(df_merged)} linhas")

    # Normalizar datas para alinhar block_date (financial) com day (votes)
    df_merged['_date_norm'] = normalize_date(df_merged['block_date'])
    df_votes_agg = prepare_votes_for_merge(df_votes)
    df_votes_agg['_date_norm'] = normalize_date(df_votes_agg['day'])

    # Colunas de votos/emissões a trazer (inclui day, round_id, total_votes, daily_emissions, etc.)
    vote_cols = [c for c in df_votes_agg.columns if c not in ('blockchain', 'pool_address', '_date_norm')]
    df_votes_join = df_votes_agg[['blockchain', 'pool_address', '_date_norm'] + vote_cols].copy()
    df_votes_join = df_votes_join.rename(columns={'pool_address': 'project_contract_address'})

    print("Fazendo merge left com votos/emissões (por blockchain, pool, data)...")
    df_merged = pd.merge(
        df_merged,
        df_votes_join,
        on=['blockchain', 'project_contract_address', '_date_norm'],
        how='left',
        suffixes=('', '_votes'),
    )
    df_merged = df_merged.drop(columns=['_date_norm'], errors='ignore')
    print(f"Merge concluído: {len(df_merged)} linhas, {len(df_merged.columns)} colunas")
    return df_merged


def save_result(df_merged):
    """Salva Aleluia.csv"""
    print("\nSalvando resultado...")
    os.makedirs('data', exist_ok=True)
    output_path = 'data/Aleluia.csv'
    df_merged = df_merged.sort_values(['blockchain', 'project_contract_address', 'block_date'])
    df_merged.to_csv(output_path, index=False)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Salvo: {output_path} ({len(df_merged):,} linhas, {len(df_merged.columns)} colunas, {size_mb:.2f} MB)")
    return output_path


def main():
    print("=" * 60)
    print("MERGE: financial_testing + veBAL_pre_merge_2 -> Aleluia.csv")
    print("=" * 60)
    try:
        df_financial, df_vebal, df_votes = load_data()
        df_merged = perform_merge(df_financial, df_vebal, df_votes)
        output_path = save_result(df_merged)
        print("\nConcluído. Arquivo gerado:", output_path)
        return 0
    except Exception as e:
        print("\nErro:", str(e))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
