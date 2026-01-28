import pandas as pd
import numpy as np

# Ler os arquivos CSV
print("Lendo arquivos...")
fsn_data = pd.read_csv('./data/FSN_data.csv')
vebal_votes = pd.read_csv('./data/vebal_votes_valid.csv')

print(f"FSN_data shape: {fsn_data.shape}")
print(f"vebal_votes shape: {vebal_votes.shape}")

# Filtrar apenas pools V2: onde poolId_v2 não está vazio
# Remover espaços em branco e valores vazios
fsn_data['poolId_v2'] = fsn_data['poolId_v2'].astype(str).str.strip()
fsn_data['poolId'] = fsn_data['poolId'].astype(str).str.strip()

# Filtrar apenas linhas onde poolId_v2 não está vazio e não é 'nan'
v2_pools = fsn_data[
    (fsn_data['poolId_v2'].notna()) & 
    (fsn_data['poolId_v2'] != '') & 
    (fsn_data['poolId_v2'] != 'nan') &
    (fsn_data['poolId'].notna()) & 
    (fsn_data['poolId'] != '') & 
    (fsn_data['poolId'] != 'nan')
].copy()

print(f"\nPools V2 encontradas: {len(v2_pools)}")

# Criar mapeamento de gauge_address (id) para poolId_v2
gauge_to_pool_v2 = dict(zip(v2_pools['id'], v2_pools['poolId_v2']))
gauge_to_pool = dict(zip(v2_pools['id'], v2_pools['poolId']))

print(f"Gauges V2 únicos: {len(gauge_to_pool_v2)}")

# Filtrar vebal_votes para manter apenas gauges V2
# Primeiro, vamos garantir que os gauge_address estão normalizados (lowercase, sem espaços)
vebal_votes['gauge_address'] = vebal_votes['gauge_address'].astype(str).str.strip().str.lower()
v2_pools['id'] = v2_pools['id'].astype(str).str.strip().str.lower()

# Criar conjunto de gauges V2
v2_gauges = set(v2_pools['id'].unique())

# Filtrar votos apenas para gauges V2
v2_votes = vebal_votes[vebal_votes['gauge_address'].isin(v2_gauges)].copy()

print(f"\nVotos V2 encontrados: {len(v2_votes)}")

# Normalizar pool_address para comparação
v2_votes['pool_address'] = v2_votes['pool_address'].astype(str).str.strip().str.lower()

# Criar mapeamento normalizado
gauge_to_pool_v2_normalized = {k.lower().strip(): v.lower().strip() if pd.notna(v) else '' 
                                for k, v in gauge_to_pool_v2.items()}

# Verificar se o pool_address corresponde ao poolId_v2
# Vamos adicionar uma coluna de verificação
def get_expected_pool_v2(gauge_addr):
    return gauge_to_pool_v2_normalized.get(gauge_addr.lower().strip(), '')

v2_votes['expected_pool_v2'] = v2_votes['gauge_address'].apply(get_expected_pool_v2)

# Filtrar apenas onde pool_address corresponde ao poolId_v2 OU onde pool_address está vazio (alguns podem não ter pool_address)
# Mas garantimos que o gauge_address está na lista V2
v2_votes_filtered = v2_votes[
    (v2_votes['pool_address'] == v2_votes['expected_pool_v2']) | 
    (v2_votes['pool_address'].isna()) |
    (v2_votes['pool_address'] == '') |
    (v2_votes['pool_address'] == 'nan')
].copy()

print(f"Votos V2 após validação de pool_address: {len(v2_votes_filtered)}")

# Remover a coluna auxiliar
v2_votes_filtered = v2_votes_filtered.drop(columns=['expected_pool_v2'])

# Selecionar apenas as colunas solicitadas
columns_to_keep = [
    'day', 'round_id', 'start_date', 'end_date', 'blockchain', 
    'gauge_address', 'pool_address', 'symbol', 'total_votes', 
    'pct_votes_in_round', 'daily_emissions', 'daily_emissions_usd', 'daily_fees'
]

v2_votes_final = v2_votes_filtered[columns_to_keep].copy()

# Salvar CSV de votos V2
output_file = './data/votes_balancer_v2.csv'
v2_votes_final.to_csv(output_file, index=False)
print(f"\nCSV criado: {output_file}")
print(f"Total de linhas: {len(v2_votes_final)}")

# Identificar pools e gauges removidos
# Pools removidos: pools que estão em vebal_votes mas não estão na lista V2
all_pools_in_votes = set(vebal_votes['pool_address'].dropna().astype(str).str.strip().str.lower().unique())
v2_pool_addresses = set([v.lower().strip() for v in gauge_to_pool_v2.values() if pd.notna(v) and v != ''])

removed_pools = all_pools_in_votes - v2_pool_addresses
removed_pools_df = pd.DataFrame({'pool_address': list(removed_pools)})
removed_pools_df = removed_pools_df[removed_pools_df['pool_address'] != '']
removed_pools_df = removed_pools_df[removed_pools_df['pool_address'] != 'nan']

# Gauges removidos: gauges que estão em vebal_votes mas não estão na lista V2
all_gauges_in_votes = set(vebal_votes['gauge_address'].dropna().astype(str).str.strip().str.lower().unique())
removed_gauges = all_gauges_in_votes - v2_gauges
removed_gauges_df = pd.DataFrame({'gauge_address': list(removed_gauges)})
removed_gauges_df = removed_gauges_df[removed_gauges_df['gauge_address'] != '']
removed_gauges_df = removed_gauges_df[removed_gauges_df['gauge_address'] != 'nan']

# Salvar CSVs de removidos
removed_pools_file = './data/removed_pool.csv'
removed_gauges_file = './data/removed_gauge.csv'

removed_pools_df.to_csv(removed_pools_file, index=False)
removed_gauges_df.to_csv(removed_gauges_file, index=False)

print(f"\nCSV de pools removidos criado: {removed_pools_file}")
print(f"Total de pools removidos: {len(removed_pools_df)}")
print(f"\nCSV de gauges removidos criado: {removed_gauges_file}")
print(f"Total de gauges removidos: {len(removed_gauges_df)}")

# Estatísticas finais
print("\n=== RESUMO ===")
print(f"Total de pools V2: {len(v2_pools)}")
print(f"Total de votos V2: {len(v2_votes_final)}")
print(f"Pools removidos: {len(removed_pools_df)}")
print(f"Gauges removidos: {len(removed_gauges_df)}")
