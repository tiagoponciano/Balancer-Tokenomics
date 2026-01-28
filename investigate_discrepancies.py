import pandas as pd
import numpy as np

# Ler os arquivos CSV
print("Lendo arquivos...")
fsn_data = pd.read_csv('./data/FSN_data.csv')
vebal_votes = pd.read_csv('./data/vebal_votes_valid.csv')
removed_gauges = pd.read_csv('./data/removed_gauge.csv')
removed_pools = pd.read_csv('./data/removed_pool.csv')

print(f"\n=== INVESTIGAÇÃO DAS DISCREPÂNCIAS ===\n")

# Normalizar dados
fsn_data['poolId_v2'] = fsn_data['poolId_v2'].astype(str).str.strip()
fsn_data['id_normalized'] = fsn_data['id'].astype(str).str.strip().str.lower()
vebal_votes['gauge_address_normalized'] = vebal_votes['gauge_address'].astype(str).str.strip().str.lower()
vebal_votes['pool_address_normalized'] = vebal_votes['pool_address'].astype(str).str.strip().str.lower()

# 1. Por que 104 poolId_v2 vazios mas só 97 removidos?
print("=== QUESTÃO 1: Por que 104 poolId_v2 vazios mas só 97 removidos? ===\n")

# Gauges com poolId_v2 vazio no FSN
non_v2_in_fsn = fsn_data[
    (fsn_data['poolId_v2'].isna()) | 
    (fsn_data['poolId_v2'] == '') | 
    (fsn_data['poolId_v2'] == 'nan')
].copy()

non_v2_gauges_set = set(non_v2_in_fsn['id_normalized'].unique())
all_gauges_in_votes_set = set(vebal_votes['gauge_address_normalized'].unique())
removed_gauges_set = set(removed_gauges['gauge_address'].astype(str).str.strip().str.lower().unique())

print(f"Total de gauges com poolId_v2 vazio no FSN_data.csv: {len(non_v2_gauges_set)}")
print(f"Total de gauges únicos nos votos: {len(all_gauges_in_votes_set)}")
print(f"Total de gauges removidos: {len(removed_gauges_set)}")

# Gauges com poolId_v2 vazio que NÃO estão nos votos
non_v2_not_in_votes = non_v2_gauges_set - all_gauges_in_votes_set
print(f"\nGauges com poolId_v2 vazio que NÃO estão nos votos: {len(non_v2_not_in_votes)}")
print(f"Esses gauges não precisam ser removidos porque não aparecem nos votos.")

if len(non_v2_not_in_votes) > 0:
    print(f"\nExemplos de gauges com poolId_v2 vazio que não estão nos votos:")
    non_v2_not_in_votes_df = fsn_data[fsn_data['id_normalized'].isin(non_v2_not_in_votes)][['id', 'poolId', 'poolId_v2', 'status', 'chain']].head(10)
    print(non_v2_not_in_votes_df.to_string())

# Verificar se todos os gauges removidos têm poolId_v2 vazio no FSN
removed_not_in_fsn = removed_gauges_set - non_v2_gauges_set
print(f"\nGauges removidos que NÃO estão no FSN_data.csv: {len(removed_not_in_fsn)}")
print(f"Esses são gauges que aparecem nos votos mas não estão no FSN_data.csv")

# 2. Por que mais gauges removidos (97) do que pools removidas (63)?
print("\n\n=== QUESTÃO 2: Por que mais gauges removidos (97) do que pools removidas (63)? ===\n")

removed_pools_set = set(removed_pools['pool_address'].astype(str).str.strip().str.lower().unique())
print(f"Total de pools removidas: {len(removed_pools_set)}")
print(f"Total de gauges removidos: {len(removed_gauges_set)}")

# Para cada gauge removido, verificar qual pool_address ele tem nos votos
removed_gauges_with_pools = []

for gauge in removed_gauges['gauge_address'].values:
    gauge_norm = str(gauge).strip().lower()
    
    # Buscar pool_address desse gauge nos votos
    votes_for_gauge = vebal_votes[vebal_votes['gauge_address_normalized'] == gauge_norm]
    
    # Pegar pool_addresses únicos desse gauge
    pool_addresses = votes_for_gauge['pool_address_normalized'].dropna().unique()
    pool_addresses = [p for p in pool_addresses if p != '' and p != 'nan']
    
    removed_gauges_with_pools.append({
        'gauge_address': gauge,
        'pool_addresses_in_votes': pool_addresses,
        'num_pools': len(pool_addresses),
        'is_pool_removed': any(p in removed_pools_set for p in pool_addresses) if pool_addresses else False
    })

removed_gauges_pools_df = pd.DataFrame(removed_gauges_with_pools)

# Análise
print(f"\nGauges removidos que têm pool_address nos votos: {len(removed_gauges_pools_df[removed_gauges_pools_df['num_pools'] > 0])}")
print(f"Gauges removidos SEM pool_address nos votos: {len(removed_gauges_pools_df[removed_gauges_pools_df['num_pools'] == 0])}")

# Gauges removidos cuja pool também foi removida
gauges_with_removed_pools = removed_gauges_pools_df[removed_gauges_pools_df['is_pool_removed'] == True]
print(f"Gauges removidos cuja pool_address também foi removida: {len(gauges_with_removed_pools)}")

# Gauges removidos cuja pool NÃO foi removida (pool_address vazio ou não está na lista de removidas)
gauges_without_removed_pools = removed_gauges_pools_df[removed_gauges_pools_df['is_pool_removed'] == False]
print(f"Gauges removidos cuja pool_address NÃO foi removida: {len(gauges_without_removed_pools)}")

# Verificar pools únicas dos gauges removidos
all_pools_from_removed_gauges = set()
for pools_list in removed_gauges_pools_df['pool_addresses_in_votes']:
    all_pools_from_removed_gauges.update(pools_list)

print(f"\nPools únicas associadas aos gauges removidos: {len(all_pools_from_removed_gauges)}")
print(f"Pools removidas: {len(removed_pools_set)}")

# Pools que estão associadas a gauges removidos mas não foram removidas
pools_in_gauges_not_removed = all_pools_from_removed_gauges - removed_pools_set
print(f"Pools associadas a gauges removidos mas que NÃO foram removidas: {len(pools_in_gauges_not_removed)}")

if len(pools_in_gauges_not_removed) > 0:
    print(f"\nExemplos de pools associadas a gauges removidos mas não removidas:")
    print(f"Essas pools provavelmente são V2 e têm outros gauges V2 associados")
    # Verificar se essas pools são V2
    v2_pools = fsn_data[
        (fsn_data['poolId_v2'].notna()) & 
        (fsn_data['poolId_v2'] != '') & 
        (fsn_data['poolId_v2'] != 'nan')
    ]
    v2_pool_addresses = set(v2_pools['poolId_v2'].astype(str).str.strip().str.lower().unique())
    
    pools_in_gauges_not_removed_that_are_v2 = pools_in_gauges_not_removed & v2_pool_addresses
    print(f"Pools que são V2 mas têm gauges removidos associados: {len(pools_in_gauges_not_removed_that_are_v2)}")
    
    if len(pools_in_gauges_not_removed_that_are_v2) > 0:
        print("\nIsso pode acontecer quando:")
        print("- Uma pool V2 tem múltiplos gauges (um V2 e outro não-V2)")
        print("- Ou há inconsistência nos dados")

# Resumo
print("\n\n=== RESUMO ===\n")
print(f"1. Diferença entre 104 e 97:")
print(f"   - 104 gauges têm poolId_v2 vazio no FSN_data.csv")
print(f"   - {len(non_v2_not_in_votes)} desses gauges NÃO estão nos votos")
print(f"   - {len(non_v2_gauges_set & all_gauges_in_votes_set)} desses gauges ESTÃO nos votos (e foram removidos)")
print(f"   - {len(removed_not_in_fsn)} gauges removidos NÃO estão no FSN_data.csv")
print(f"   - Total removidos: {len(removed_gauges_set)} = {len(non_v2_gauges_set & all_gauges_in_votes_set)} (do FSN) + {len(removed_not_in_fsn)} (não no FSN)")

print(f"\n2. Diferença entre 97 gauges e 63 pools:")
print(f"   - {len(removed_gauges_pools_df[removed_gauges_pools_df['num_pools'] == 0])} gauges removidos NÃO têm pool_address nos votos")
print(f"   - {len(gauges_with_removed_pools)} gauges removidos têm pool_address que também foi removida")
print(f"   - {len(gauges_without_removed_pools)} gauges removidos têm pool_address que NÃO foi removida")
print(f"   - Isso explica por que há mais gauges removidos do que pools removidas")
