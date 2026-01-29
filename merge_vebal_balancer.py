#!/usr/bin/env python3
"""
Script para fazer merge dos arquivos veBAL_pre_merge_2.csv e balancer_v2_pre_final_merge.csv
sem perder nenhum dado.
"""

import pandas as pd
from datetime import datetime

# Carregar os arquivos
print("Carregando arquivos...")
balancer_df = pd.read_csv('data/balancer_v2_pre_final_merge.csv')
vebal_df = pd.read_csv('data/veBAL_pre_merge_2.csv')

print(f"balancer_v2_pre_final_merge.csv: {len(balancer_df)} linhas")
print(f"veBAL_pre_merge_2.csv: {len(vebal_df)} linhas")

# Normalizar as datas para o mesmo formato
print("\nNormalizando datas...")
# balancer_v2_pre_final_merge.csv tem 'day', não 'block_date'
balancer_df['block_date_norm'] = pd.to_datetime(balancer_df['day']).dt.date
# veBAL_pre_merge_2.csv tem 'block_date'
vebal_df['block_date_norm'] = pd.to_datetime(vebal_df['block_date']).dt.date

# Criar colunas de merge do veBAL
vebal_df['votes_received'] = None  # Será preenchido do balancer
vebal_df['bal_emited_votes'] = None  # Será preenchido do balancer
vebal_df['core_non_core_vebal'] = None  # Será preenchido do balancer

# Normalizar endereços (lowercase e remover espaços)
print("Normalizando endereços...")
# balancer_v2_pre_final_merge.csv tem 'pool_address', não 'project_contract_address'
balancer_df['pool_address_norm'] = balancer_df['pool_address'].astype(str).str.lower().str.strip()
balancer_df['gauge_address_norm'] = balancer_df['gauge_address'].astype(str).str.lower().str.strip()
balancer_df['gauge_address_norm'] = balancer_df['gauge_address_norm'].replace('nan', '').replace('', None)

# veBAL_pre_merge_2.csv tem 'project_contract_address'
vebal_df['project_contract_address_norm'] = vebal_df['project_contract_address'].astype(str).str.lower().str.strip()
vebal_df['gauge_address_norm'] = vebal_df['gauge_address'].astype(str).str.lower().str.strip()
vebal_df['gauge_address_norm'] = vebal_df['gauge_address_norm'].replace('nan', '').replace('', None)

# Criar chaves de merge
print("Criando chaves de merge...")
# balancer_v2_pre_final_merge.csv: usa pool_address
balancer_df['merge_key_gauge'] = (
    balancer_df['blockchain'].astype(str) + '|' +
    balancer_df['gauge_address_norm'].fillna('').astype(str) + '|' +
    balancer_df['pool_address_norm'].astype(str) + '|' +
    balancer_df['block_date_norm'].astype(str)
)

balancer_df['merge_key_pool'] = (
    balancer_df['blockchain'].astype(str) + '|' +
    balancer_df['pool_address_norm'].astype(str) + '|' +
    balancer_df['block_date_norm'].astype(str)
)

# veBAL_pre_merge_2.csv: usa project_contract_address
vebal_df['merge_key_gauge'] = (
    vebal_df['blockchain'].astype(str) + '|' +
    vebal_df['gauge_address_norm'].fillna('').astype(str) + '|' +
    vebal_df['project_contract_address_norm'].astype(str) + '|' +
    vebal_df['block_date_norm'].astype(str)
)

vebal_df['merge_key_pool'] = (
    vebal_df['blockchain'].astype(str) + '|' +
    vebal_df['project_contract_address_norm'].astype(str) + '|' +
    vebal_df['block_date_norm'].astype(str)
)

# Preparar o dataframe BALANCER para merge (ele tem os dados de votes)
# balancer_v2_pre_final_merge.csv tem: total_votes, daily_emissions, is_core
balancer_merge_cols = ['merge_key_gauge', 'merge_key_pool', 'total_votes', 'daily_emissions', 'is_core', 'pool_address', 'day', 'blockchain', 'gauge_address', 'symbol']
balancer_merge = balancer_df[balancer_merge_cols].copy()
balancer_merge = balancer_merge.rename(columns={
    'total_votes': 'votes_received',
    'daily_emissions': 'bal_emited_votes',
    'is_core': 'core_non_core_balancer',
    'symbol': 'pool_symbol_balancer'
})

# Preparar o dataframe veBAL para merge (ele tem os dados financeiros)
vebal_merge_cols = ['merge_key_gauge', 'merge_key_pool', 'project_contract_address', 'block_date', 'pool_symbol', 'pool_type', 
                    'swap_amount_usd', 'tvl_usd', 'tvl_eth', 'total_protocol_fee_usd', 'protocol_fee_amount_usd',
                    'swap_fee_usd', 'yield_fee_usd', 'swap_fee_%', 'blockchain', 'project', 'version']
vebal_merge = vebal_df[vebal_merge_cols].copy()

# Fazer merge: começar com balancer (base com votes) e adicionar dados financeiros do veBAL
print("\nFazendo merge por gauge_address + pool_address + date...")
# Merge usando balancer como base (tem votes)
merged_df = balancer_merge.merge(
    vebal_merge,
    left_on='merge_key_gauge',
    right_on='merge_key_gauge',
    how='outer',
    suffixes=('', '_vebal')
)

# Para registros que não fizeram match, tentar apenas por pool_address + date
print("Preenchendo registros sem match usando apenas pool_address + date...")
mask_no_match = merged_df['pool_symbol'].isna()  # Usar pool_symbol como indicador de match
if mask_no_match.sum() > 0:
    print(f"  {mask_no_match.sum()} registros sem match por gauge, tentando por pool apenas...")
    
    # Criar um dataframe temporário com merge por pool apenas
    vebal_merge_pool = vebal_merge.drop_duplicates(subset=['merge_key_pool'], keep='first')
    
    # Fazer merge apenas com as linhas sem match
    no_match_df = merged_df.loc[mask_no_match, ['merge_key_pool']].copy()
    temp_merge = no_match_df.merge(
        vebal_merge_pool,
        on='merge_key_pool',
        how='left',
        suffixes=('', '_pool')
    )
    
    # Criar um dicionário de mapeamento por merge_key_pool
    pool_update_dict = {}
    for idx, row in temp_merge.iterrows():
        pool_key = row['merge_key_pool']
        if pool_key not in pool_update_dict:
            pool_update_dict[pool_key] = {}
            for col in ['project_contract_address', 'block_date', 'pool_symbol', 'pool_type',
                        'swap_amount_usd', 'tvl_usd', 'tvl_eth', 'total_protocol_fee_usd',
                        'protocol_fee_amount_usd', 'swap_fee_usd', 'yield_fee_usd', 'swap_fee_%',
                        'blockchain', 'project', 'version']:
                if col in temp_merge.columns and pd.notna(row[col]):
                    pool_update_dict[pool_key][col] = row[col]
    
    # Aplicar atualizações
    for idx in merged_df[mask_no_match].index:
        pool_key = merged_df.loc[idx, 'merge_key_pool']
        if pool_key in pool_update_dict:
            for col, value in pool_update_dict[pool_key].items():
                if pd.isna(merged_df.loc[idx, col]):
                    merged_df.loc[idx, col] = value

# Converter core_non_core para string (core/non-core)
print("Convertendo core_non_core...")
merged_df['core_non_core'] = merged_df['core_non_core_balancer'].apply(
    lambda x: 'core' if pd.notna(x) and x == 1 else ('non-core' if pd.notna(x) and x == 0 else None)
)

# Selecionar e ordenar as colunas finais
print("\nPreparando colunas finais...")
final_columns = [
    'blockchain',
    'project',
    'version',
    'block_date',
    'project_contract_address',
    'pool_symbol',
    'pool_type',
    'swap_amount_usd',
    'tvl_usd',
    'tvl_eth',
    'total_protocol_fee_usd',
    'protocol_fee_amount_usd',
    'swap_fee_usd',
    'yield_fee_usd',
    'swap_fee_%',
    'core_non_core',
    'bal_emited_votes',
    'votes_received'
]

# Verificar se todas as colunas existem
missing_cols = [col for col in final_columns if col not in merged_df.columns]
if missing_cols:
    print(f"AVISO: Colunas faltando: {missing_cols}")

# Criar dataframe final
# Preencher project_contract_address com pool_address se não tiver
merged_df['project_contract_address'] = merged_df['project_contract_address'].fillna(merged_df['pool_address'])
# Preencher block_date com day se não tiver
merged_df['block_date'] = merged_df['block_date'].fillna(merged_df['day'].astype(str))
# Preencher pool_symbol se não tiver
merged_df['pool_symbol'] = merged_df['pool_symbol'].fillna(merged_df['pool_symbol_balancer'])
# Preencher project e version se não tiver
merged_df['project'] = merged_df['project'].fillna('balancer')
merged_df['version'] = merged_df['version'].fillna(2)

# Converter block_date para formato correto
# Primeiro converter day para datetime se necessário
merged_df['day_dt'] = pd.to_datetime(merged_df['day'], errors='coerce')
# Usar block_date se existir, senão usar day formatado
merged_df['block_date'] = merged_df['block_date'].fillna(
    merged_df['day_dt'].dt.strftime('%Y-%m-%d %H:%M:%S%z')
)
# Garantir formato com timezone
merged_df['block_date'] = merged_df['block_date'].apply(
    lambda x: str(x) + '+00:00' if pd.notna(x) and '+00:00' not in str(x) and len(str(x)) < 20 else str(x) if pd.notna(x) else x
)

final_df = merged_df[final_columns].copy()

# Estatísticas
print("\n=== Estatísticas do Merge ===")
print(f"Total de linhas no arquivo final: {len(final_df)}")
print(f"Linhas com votes_received: {final_df['votes_received'].notna().sum()}")
print(f"Linhas com bal_emited_votes: {final_df['bal_emited_votes'].notna().sum()}")
print(f"Linhas com core_non_core: {final_df['core_non_core'].notna().sum()}")

# Verificar se não perdemos dados do balancer
print(f"\nLinhas originais do balancer: {len(balancer_df)}")
print(f"Linhas no merge final: {len(final_df)}")
if len(final_df) != len(balancer_df):
    print(f"AVISO: Diferença de {len(final_df) - len(balancer_df)} linhas!")

# Salvar o arquivo
print("\nSalvando arquivo balancer_v2_merged2.csv...")
final_df.to_csv('data/balancer_v2_merged2.csv', index=False)
print("Arquivo salvo com sucesso!")

# Verificar registros do veBAL que não foram mergeados
print("\nVerificando registros do veBAL que não foram mergeados...")
vebal_merged_keys = set(merged_df[merged_df['votes_received'].notna()]['merge_key_gauge'].tolist() + 
                        merged_df[merged_df['votes_received'].notna()]['merge_key_pool'].tolist())
vebal_all_keys = set(vebal_df['merge_key_gauge'].tolist() + vebal_df['merge_key_pool'].tolist())
unmerged_vebal = len(vebal_all_keys - vebal_merged_keys)
print(f"Chaves do veBAL não mergeadas: {unmerged_vebal}")

if unmerged_vebal > 0:
    print("\nAVISO: Alguns registros do veBAL não foram mergeados.")
    print("Isso pode ser normal se houver datas ou endereços diferentes.")

print("\n=== Merge concluído ===")
