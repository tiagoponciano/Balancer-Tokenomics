"""
Merge: balancer_v2_financial_master_final_testing.csv + veBAL_pre_merge_2.csv
Ambos têm blockchain, block_date, project_contract_address e colunas financeiras.
veBAL adiciona: project_contract_address_norm, gauge_address.
Financial adiciona: is_core_pool.
Saída: Aleluia.csv
"""

import pandas as pd
import os

def load_data():
    """Carrega os dois CSVs"""
    print("Carregando CSVs...")
    df_financial = pd.read_csv('data/balancer_v2_financial_master_final_testing.csv')
    df_vebal = pd.read_csv('data/veBAL_pre_merge_2.csv')

    print(f"Financial (testing): {len(df_financial)} linhas, {len(df_financial.columns)} colunas")
    print(f"veBAL_pre_merge_2:   {len(df_vebal)} linhas, {len(df_vebal.columns)} colunas")
    return df_financial, df_vebal


def prepare_vebal_for_merge(df_vebal):
    """
    veBAL pode ter várias linhas por (blockchain, project_contract_address, block_date)
    quando há mais de um gauge. Agregamos por essa chave e ficamos com uma linha por
    pool/dia, pegando o primeiro gauge_address e project_contract_address_norm para
    não duplicar dados financeiros no merge.
    """
    key_cols = ['blockchain', 'project_contract_address', 'block_date']
    extra_cols = ['project_contract_address_norm', 'gauge_address']
    keep = [c for c in extra_cols if c in df_vebal.columns]
    if not keep:
        return df_vebal[key_cols].drop_duplicates()

    agg = df_vebal.groupby(key_cols, as_index=False)[keep].first()
    return agg


def perform_merge(df_financial, df_vebal):
    """Merge outer por blockchain + project_contract_address + block_date."""
    print("\nPreparando veBAL (uma linha por pool/dia)...")
    df_vebal_keys = prepare_vebal_for_merge(df_vebal)

    print("Fazendo merge outer...")
    df_merged = pd.merge(
        df_financial,
        df_vebal_keys,
        on=['blockchain', 'project_contract_address', 'block_date'],
        how='outer',
    )
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
        df_financial, df_vebal = load_data()
        df_merged = perform_merge(df_financial, df_vebal)
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
