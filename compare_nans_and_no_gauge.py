"""
Script para comparar nans_por_contrato.csv e veBAL_pre_merge_no_gauge.csv
e identificar pools diferentes entre eles
"""

import pandas as pd
import os

DATA_DIR = "data"
OUTPUT_DIR = "data"

def normalize_address(addr):
    """Normaliza endereços para comparação (lowercase, sem espaços)"""
    if pd.isna(addr) or addr == '':
        return None
    return str(addr).strip().lower()

def main():
    print("=" * 80)
    print("COMPARANDO nans_por_contrato.csv E veBAL_pre_merge_no_gauge.csv")
    print("=" * 80)
    
    # 1. Carregar arquivos
    print("\n📂 Carregando arquivos...")
    nans_file = os.path.join(DATA_DIR, "nans_por_contrato.csv")
    no_gauge_file = os.path.join(DATA_DIR, "veBAL_pre_merge_no_gauge.csv")
    
    df_nans = pd.read_csv(nans_file)
    df_no_gauge = pd.read_csv(no_gauge_file)
    
    print(f"  ✓ nans_por_contrato.csv: {len(df_nans)} registros")
    print(f"  ✓ veBAL_pre_merge_no_gauge.csv: {len(df_no_gauge)} registros")
    
    # 2. Normalizar project_contract_address em ambos
    print("\n🔧 Normalizando endereços...")
    df_nans['project_contract_address_norm'] = df_nans['project_contract_address'].apply(normalize_address)
    df_no_gauge['project_contract_address_norm'] = df_no_gauge['project_contract_address'].apply(normalize_address)
    
    # 3. Criar conjuntos de endereços únicos
    nans_addresses = set(df_nans['project_contract_address_norm'].dropna())
    no_gauge_addresses = set(df_no_gauge['project_contract_address_norm'].dropna())
    
    print(f"  ✓ Endereços únicos em nans_por_contrato.csv: {len(nans_addresses)}")
    print(f"  ✓ Endereços únicos em veBAL_pre_merge_no_gauge.csv: {len(no_gauge_addresses)}")
    
    # 4. Encontrar diferenças
    print("\n🔍 Analisando diferenças...")
    
    # Pools que estão em nans mas não em no_gauge
    only_in_nans = nans_addresses - no_gauge_addresses
    
    # Pools que estão em no_gauge mas não em nans
    only_in_no_gauge = no_gauge_addresses - nans_addresses
    
    # Pools que estão em ambos
    in_both = nans_addresses & no_gauge_addresses
    
    print(f"  ✓ Pools em ambos arquivos: {len(in_both)}")
    print(f"  ⚠️ Pools apenas em nans_por_contrato.csv: {len(only_in_nans)}")
    print(f"  ⚠️ Pools apenas em veBAL_pre_merge_no_gauge.csv: {len(only_in_no_gauge)}")
    
    # 5. Criar DataFrames com as diferenças
    print("\n💾 Criando arquivos com diferenças...")
    
    # 5.1. Pools apenas em nans_por_contrato.csv
    if len(only_in_nans) > 0:
        df_only_nans = df_nans[df_nans['project_contract_address_norm'].isin(only_in_nans)].copy()
        df_only_nans = df_only_nans[['project_contract_address', 'gauge_address']].drop_duplicates()
        
        only_nans_file = os.path.join(OUTPUT_DIR, "only_in_nans_por_contrato.csv")
        df_only_nans.to_csv(only_nans_file, index=False)
        print(f"  📄 Arquivo criado: {only_nans_file}")
        print(f"     Total de pools: {len(df_only_nans)}")
    
    # 5.2. Pools apenas em veBAL_pre_merge_no_gauge.csv
    if len(only_in_no_gauge) > 0:
        df_only_no_gauge = df_no_gauge[df_no_gauge['project_contract_address_norm'].isin(only_in_no_gauge)].copy()
        df_only_no_gauge = df_only_no_gauge.drop(columns=['project_contract_address_norm'], errors='ignore')
        
        only_no_gauge_file = os.path.join(OUTPUT_DIR, "only_in_veBAL_pre_merge_no_gauge.csv")
        df_only_no_gauge.to_csv(only_no_gauge_file, index=False)
        print(f"  📄 Arquivo criado: {only_no_gauge_file}")
        print(f"     Total de pools: {len(df_only_no_gauge)}")
    
    # 5.3. Pools em ambos (para referência)
    if len(in_both) > 0:
        df_both_nans = df_nans[df_nans['project_contract_address_norm'].isin(in_both)].copy()
        df_both_no_gauge = df_no_gauge[df_no_gauge['project_contract_address_norm'].isin(in_both)].copy()
        
        # Merge para comparar
        df_both_merged = df_both_nans[['project_contract_address', 'gauge_address']].merge(
            df_both_no_gauge[['project_contract_address', 'blockchain', 'pool_symbol', 'total_tvl_usd']],
            on='project_contract_address',
            how='inner',
            suffixes=('_nans', '_no_gauge')
        )
        
        both_file = os.path.join(OUTPUT_DIR, "in_both_files.csv")
        df_both_merged.to_csv(both_file, index=False)
        print(f"  📄 Arquivo criado: {both_file}")
        print(f"     Total de pools: {len(df_both_merged)}")
    
    # 6. Resumo final
    print("\n" + "=" * 80)
    print("📊 RESUMO DA COMPARAÇÃO")
    print("=" * 80)
    print(f"Total de pools em nans_por_contrato.csv: {len(nans_addresses)}")
    print(f"Total de pools em veBAL_pre_merge_no_gauge.csv: {len(no_gauge_addresses)}")
    print(f"Pools em ambos: {len(in_both)}")
    print(f"Pools apenas em nans_por_contrato.csv: {len(only_in_nans)}")
    print(f"Pools apenas em veBAL_pre_merge_no_gauge.csv: {len(only_in_no_gauge)}")
    print("=" * 80)
    
    # 7. Estatísticas adicionais
    if len(only_in_nans) > 0:
        print("\n📈 Estatísticas das pools apenas em nans_por_contrato.csv:")
        df_only_nans_stats = df_nans[df_nans['project_contract_address_norm'].isin(only_in_nans)]
        print(f"  Total de registros: {len(df_only_nans_stats)}")
        print(f"  Média de gauge_address (NAs): {df_only_nans_stats['gauge_address'].mean():.2f}")
        print(f"  Máximo de gauge_address (NAs): {df_only_nans_stats['gauge_address'].max()}")
    
    if len(only_in_no_gauge) > 0:
        print("\n📈 Estatísticas das pools apenas em veBAL_pre_merge_no_gauge.csv:")
        df_only_no_gauge_stats = df_no_gauge[df_no_gauge['project_contract_address_norm'].isin(only_in_no_gauge)]
        print(f"  Total de registros: {len(df_only_no_gauge_stats)}")
        print(f"  Total TVL: ${df_only_no_gauge_stats['total_tvl_usd'].sum():,.2f}")
        print(f"  Por blockchain:")
        for chain in df_only_no_gauge_stats['blockchain'].unique():
            chain_count = len(df_only_no_gauge_stats[df_only_no_gauge_stats['blockchain'] == chain])
            print(f"    {chain}: {chain_count} pools")

if __name__ == "__main__":
    main()
