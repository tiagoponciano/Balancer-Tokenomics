"""Verificar se todas as linhas do veBAL sem gauge foram incluídas no merged final"""

import pandas as pd

vebal = pd.read_csv('data/vebal_pre_merge_2.csv')
merged = pd.read_csv('data/balancer_v2_merged.csv', low_memory=False)

# Preparar dados
vebal['_date'] = pd.to_datetime(vebal['block_date'], errors='coerce').dt.date
vebal['_pool_norm'] = vebal['project_contract_address'].astype(str).str.strip().str.lower()

merged['_date'] = pd.to_datetime(merged['block_date'], errors='coerce').dt.date
merged['_pool_norm'] = merged['project_contract_address'].astype(str).str.strip().str.lower()

# Linhas sem gauge do veBAL
vebal_no_gauge = vebal[vebal['gauge_address'].isna()]
vebal_no_gauge_agg = vebal_no_gauge.groupby(['_pool_norm', '_date'], as_index=False).agg({
    'swap_fee_usd': 'sum'
})

# Criar chaves
vebal_keys = set(vebal_no_gauge_agg.apply(lambda x: (x['_pool_norm'], x['_date']), axis=1))
merged_keys = set(merged[merged['_pool_norm'].notna()].apply(
    lambda x: (x['_pool_norm'], x['_date']), axis=1
))

not_included = vebal_keys - merged_keys

print(f"Chaves do veBAL sem gauge: {len(vebal_keys):,}")
print(f"Chaves no merged: {len(merged_keys):,}")
print(f"Chaves não incluídas: {len(not_included):,}")

if len(not_included) > 0:
    not_included_df = vebal_no_gauge_agg[
        vebal_no_gauge_agg.apply(lambda x: (x['_pool_norm'], x['_date']) in not_included, axis=1)
    ]
    print(f"swap_fee_usd não incluído: {not_included_df['swap_fee_usd'].sum():,.2f}")
    
    # Verificar por que não foram incluídas
    print(f"\nVerificando linhas adicionadas...")
    # Linhas adicionadas devem ter votes_received = 0
    added_rows = merged[merged['votes_received'] == 0]
    print(f"Linhas com votes_received = 0: {len(added_rows):,}")
    print(f"swap_fee_usd nessas linhas: {added_rows['swap_fee_usd'].sum():,.2f}")
    
    # Verificar se essas linhas têm swap_fee_usd
    added_with_swap_fee = added_rows[added_rows['swap_fee_usd'].notna() & (added_rows['swap_fee_usd'] > 0)]
    print(f"Linhas adicionadas com swap_fee_usd > 0: {len(added_with_swap_fee):,}")
    print(f"swap_fee_usd nessas linhas: {added_with_swap_fee['swap_fee_usd'].sum():,.2f}")
