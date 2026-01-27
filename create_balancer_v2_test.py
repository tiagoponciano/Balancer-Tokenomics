"""
Script para unir vebal_votes_valid.csv com FSN_data.csv
e identificar pools faltantes
"""

import pandas as pd
import numpy as np
import os

DATA_DIR = "data"
OUTPUT_DIR = "data"

def normalize_address(addr):
    """Normaliza endereços para comparação (lowercase, sem espaços)"""
    if pd.isna(addr) or addr == '':
        return None
    return str(addr).lower().strip()

def main():
    print("=" * 80)
    print("CRIAÇÃO DO ARQUIVO: balancer_v2_test.csv")
    print("=" * 80)
    
    # 1. Carregar dados de votos
    print("\n📂 Carregando arquivos...")
    votes_file = os.path.join(DATA_DIR, "vebal_votes_valid.csv")
    df_votes = pd.read_csv(votes_file)
    print(f"  ✓ vebal_votes_valid.csv: {len(df_votes)} registros")
    
    # 2. Carregar mapping de gauges
    mapping_file = os.path.join(DATA_DIR, "FSN_data.csv")
    df_mapping = pd.read_csv(mapping_file)
    print(f"  ✓ FSN_data.csv: {len(df_mapping)} registros")
    
    # 3. Normalizar gauge addresses
    print("\n🔧 Normalizando endereços...")
    df_votes['gauge_address_norm'] = df_votes['gauge_address'].apply(normalize_address)
    df_mapping['gauge_address_norm'] = df_mapping['id'].apply(normalize_address)
    
    # 4. Merge com mapping
    print("\n🔗 Fazendo merge com mapping...")
    df_merged = df_votes.merge(
        df_mapping,
        left_on='gauge_address_norm',
        right_on='gauge_address_norm',
        how='left',
        suffixes=('', '_mapping')
    )
    
    print(f"  ✓ Merge concluído: {len(df_merged)} registros")
    print(f"  ✓ Registros com pool mapeado: {df_merged['poolId'].notna().sum()}")
    print(f"  ✓ Registros sem pool mapeado: {df_merged['poolId'].isna().sum()}")
    
    # 5. Identificar pools faltantes
    print("\n🔍 Identificando pools faltantes...")
    
    # Gauges que não têm pool mapeado (nem poolId nem poolId_v2)
    missing_pools = df_merged[
        (df_merged['poolId'].isna()) & 
        (df_merged['poolId_v2'].isna())
    ].copy()
    
    if len(missing_pools) > 0:
        missing_gauges = missing_pools.groupby('gauge_address').agg({
            'round_id': 'nunique',
            'blockchain': 'first',
            'symbol': 'first',
            'pool_address': 'first'  # pool_address do vebal_votes_valid
        }).reset_index()
        missing_gauges.columns = ['gauge_address', 'rounds_count', 'blockchain', 'symbol', 'pool_address_from_votes']
        
        print(f"  ⚠️ {len(missing_gauges)} gauges sem pool mapeado no FSN_data.csv")
        print(f"     Total de registros afetados: {len(missing_pools)}")
        
        # Verificar se esses gauges têm pool_address no vebal_votes_valid
        gauges_with_pool_address = missing_gauges[missing_gauges['pool_address_from_votes'].notna()]
        print(f"     Gauges com pool_address no vebal_votes_valid: {len(gauges_with_pool_address)}")
        
        # Salvar lista de pools faltantes
        missing_file = os.path.join(OUTPUT_DIR, "missing_pools_from_mapping.csv")
        missing_gauges.to_csv(missing_file, index=False)
        print(f"  ✓ Lista de pools faltantes salva em: {missing_file}")
    
    # 6. Preparar dados finais
    print("\n📊 Preparando dados finais...")
    
    # Selecionar colunas relevantes
    final_cols = [
        'day', 'round_id', 'start_date', 'end_date', 'blockchain',
        'gauge_address', 'pool_address',
        'symbol', 'gauge_votes_in_round', 'pct_votes_in_round',
        'daily_emissions', 'daily_emissions_usd', 'daily_fees',
        'poolId', 'poolId_v2', 'chain', 'status'
    ]
    
    # Manter apenas colunas que existem
    available_cols = [c for c in final_cols if c in df_merged.columns]
    df_final = df_merged[available_cols].copy()
    
    # Preencher pool_address usando poolId_v2 ou poolId (primeiros 42 caracteres)
    if 'pool_address' in df_final.columns:
        # Primeiro tenta poolId_v2 (já é 42 caracteres)
        if 'poolId_v2' in df_final.columns:
            df_final['pool_address'] = df_final['pool_address'].fillna(df_final['poolId_v2'])
        
        # Depois tenta poolId (primeiros 42 caracteres)
        if 'poolId' in df_final.columns:
            mask = df_final['pool_address'].isna()
            df_final.loc[mask, 'pool_address'] = df_final.loc[mask, 'poolId'].astype(str).str[:42].str.lower()
    
    # 7. Estatísticas
    print("\n📈 Estatísticas:")
    print(f"  ✓ Total de registros: {len(df_final)}")
    print(f"  ✓ Gauges únicos: {df_final['gauge_address'].nunique()}")
    print(f"  ✓ Pools únicos (pool_address): {df_final['pool_address'].notna().sum()}")
    print(f"  ✓ Pools únicos (poolId): {df_final['poolId'].notna().sum()}")
    print(f"  ✓ Pools únicos (poolId_v2): {df_final['poolId_v2'].notna().sum()}")
    
    # 8. Salvar arquivo final
    output_file = os.path.join(OUTPUT_DIR, "balancer_v2_test.csv")
    df_final.to_csv(output_file, index=False)
    
    print("\n" + "=" * 80)
    print(f"✅ ARQUIVO CRIADO: {output_file}")
    print(f"   Total de registros: {len(df_final):,}")
    print("=" * 80)

if __name__ == "__main__":
    main()
