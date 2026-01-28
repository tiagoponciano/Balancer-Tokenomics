"""
Script completo para fazer merge usando votes_balancer_v2.csv como base.
Processo:
1. Merge com classification_core_pools.csv para adicionar is_core
2. Preencher dados faltantes usando FSN_data.csv
3. Remover duplicatas
4. Remover linhas sem poolId e poolId_v2
"""

import pandas as pd

def merge_with_votes_v2():
    """
    Refaz o merge completo usando votes_balancer_v2.csv como base.
    """
    print("=" * 60)
    print("🔄 Merge Completo com votes_balancer_v2.csv")
    print("=" * 60)
    
    # Passo 1: Ler arquivos
    print("\n📖 Passo 1: Lendo arquivos...")
    votes_df = pd.read_csv('data/votes_balancer_v2.csv')
    classification_df = pd.read_csv('data/classification_core_pools.csv')
    fsn_df = pd.read_csv('data/FSN_data.csv')
    
    print(f"✅ votes_balancer_v2.csv: {len(votes_df):,} linhas")
    print(f"✅ classification_core_pools.csv: {len(classification_df):,} linhas")
    print(f"✅ FSN_data.csv: {len(fsn_df):,} linhas")
    print(f"   Soma total_votes inicial: {votes_df['total_votes'].sum():,.2f}")
    
    # Passo 2: Preparar classification para merge
    print("\n🔄 Passo 2: Preparando classification para merge...")
    classification_df['day'] = pd.to_datetime(classification_df['day'], errors='coerce')
    classification_df['day'] = classification_df['day'].dt.normalize()
    classification_df['address_short'] = classification_df['address'].str[:42]
    classification_df = classification_df.dropna(subset=['day'])
    
    # Converter is_core para inteiro (0/1)
    classification_df['is_core'] = classification_df['is_core'].astype(int)
    
    print(f"   Addresses únicos: {classification_df['address_short'].nunique():,}")
    
    # Passo 3: Preparar votes para merge
    print("\n🔄 Passo 3: Preparando votes para merge...")
    votes_df['day'] = pd.to_datetime(votes_df['day'], errors='coerce')
    votes_df['day'] = votes_df['day'].dt.normalize()
    votes_df = votes_df.dropna(subset=['day'])
    
    # Passo 4: Merge com classification
    print("\n🔗 Passo 4: Fazendo merge com classification...")
    classification_renamed = classification_df.rename(columns={'address_short': 'pool_address'})
    
    merged_df = votes_df.merge(
        classification_renamed[['pool_address', 'day', 'is_core']],
        on=['pool_address', 'day'],
        how='left'
    )
    
    # Preencher NaN com 0 (non-core)
    merged_df['is_core'] = merged_df['is_core'].fillna(0).astype(int)
    
    print(f"   Linhas após merge: {len(merged_df):,}")
    print(f"   Linhas classificadas: {(merged_df['is_core'] == 1).sum():,}")
    print(f"   Soma total_votes: {merged_df['total_votes'].sum():,.2f}")
    
    # Passo 5: Preencher dados faltantes com FSN_data
    print("\n✏️  Passo 5: Preenchendo dados faltantes com FSN_data...")
    
    # Mapeamento poolId_v2 -> pool_address
    fsn_valid_v2 = fsn_df[fsn_df['poolId_v2'].notna() & (fsn_df['poolId_v2'] != '')].copy()
    gauge_to_pool_v2 = dict(zip(fsn_valid_v2['id'], fsn_valid_v2['poolId_v2']))
    gauge_to_chain = dict(zip(fsn_valid_v2['id'], fsn_valid_v2['chain']))
    
    # Preencher pool_address faltantes
    missing_pool_mask = merged_df['pool_address'].isna()
    filled_pool = 0
    for idx in merged_df[missing_pool_mask].index:
        gauge = merged_df.loc[idx, 'gauge_address']
        if gauge in gauge_to_pool_v2:
            merged_df.loc[idx, 'pool_address'] = gauge_to_pool_v2[gauge]
            filled_pool += 1
    
    # Preencher blockchain faltantes
    missing_chain_mask = merged_df['blockchain'].isna()
    filled_chain = 0
    for idx in merged_df[missing_chain_mask].index:
        gauge = merged_df.loc[idx, 'gauge_address']
        if gauge in gauge_to_chain:
            merged_df.loc[idx, 'blockchain'] = gauge_to_chain[gauge]
            filled_chain += 1
    
    print(f"   pool_address preenchidos: {filled_pool:,}")
    print(f"   blockchain preenchidos: {filled_chain:,}")
    
    # Passo 6: Preencher com poolId quando tem ambos poolId e poolId_v2
    print("\n✏️  Passo 6: Preenchendo com poolId (quando tem ambos)...")
    
    fsn_both = fsn_df[
        fsn_df['poolId'].notna() & (fsn_df['poolId'] != '') &
        fsn_df['poolId_v2'].notna() & (fsn_df['poolId_v2'] != '')
    ].copy()
    gauge_to_poolid = dict(zip(fsn_both['id'], fsn_both['poolId']))
    
    missing_pool_mask = merged_df['pool_address'].isna()
    filled_poolid = 0
    for idx in merged_df[missing_pool_mask].index:
        gauge = merged_df.loc[idx, 'gauge_address']
        if gauge in gauge_to_poolid:
            merged_df.loc[idx, 'pool_address'] = gauge_to_poolid[gauge]
            filled_poolid += 1
    
    print(f"   pool_address preenchidos com poolId: {filled_poolid:,}")
    
    # Passo 7: Remover linhas sem pool_address (sem poolId e poolId_v2)
    print("\n🗑️  Passo 7: Removendo linhas sem pool_address...")
    before_remove = len(merged_df)
    merged_df = merged_df[merged_df['pool_address'].notna()].copy()
    removed_count = before_remove - len(merged_df)
    print(f"   Linhas removidas: {removed_count:,}")
    print(f"   Linhas restantes: {len(merged_df):,}")
    
    # Passo 8: Remover duplicatas
    print("\n🗑️  Passo 8: Removendo duplicatas...")
    before_dedup = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=['gauge_address', 'day'], keep='first')
    dup_removed = before_dedup - len(merged_df)
    print(f"   Duplicatas removidas: {dup_removed:,}")
    print(f"   Linhas restantes: {len(merged_df):,}")
    
    # Estatísticas finais
    print("\n📊 Estatísticas finais:")
    print(f"   Total de linhas: {len(merged_df):,}")
    print(f"   Linhas com is_core = 1: {(merged_df['is_core'] == 1).sum():,}")
    print(f"   Linhas com is_core = 0: {(merged_df['is_core'] == 0).sum():,}")
    print(f"   Linhas com pool_address faltante: {merged_df['pool_address'].isna().sum():,}")
    print(f"   Linhas com blockchain faltante: {merged_df['blockchain'].isna().sum():,}")
    print(f"   Soma total_votes: {merged_df['total_votes'].sum():,.2f}")
    
    # Comparação com arquivo original
    print("\n📊 Comparação com arquivo original:")
    print(f"   votes_balancer_v2.csv: {len(votes_df):,} linhas")
    print(f"   balancer_v2_pre_final_merge.csv: {len(merged_df):,} linhas")
    print(f"   Diferença: {len(merged_df) - len(votes_df):,} linhas")
    print(f"\n   Soma total_votes:")
    print(f"     votes_balancer_v2.csv: {votes_df['total_votes'].sum():,.2f}")
    print(f"     balancer_v2_pre_final_merge.csv: {merged_df['total_votes'].sum():,.2f}")
    print(f"     Diferença: {merged_df['total_votes'].sum() - votes_df['total_votes'].sum():,.2f}")
    
    # Salvar arquivo
    output_file = 'data/balancer_v2_pre_final_merge.csv'
    print(f"\n💾 Salvando arquivo: {output_file}")
    merged_df.to_csv(output_file, index=False)
    
    print(f"✅ Arquivo salvo com sucesso!")
    
    return merged_df

if __name__ == "__main__":
    try:
        result_df = merge_with_votes_v2()
        print("\n" + "=" * 60)
        print("✅ Processo concluído com sucesso!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()
