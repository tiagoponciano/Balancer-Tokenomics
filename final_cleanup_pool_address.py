"""
Script para fazer o pente fino final:
- Verificar linhas com pool_address faltante
- Se o gauge_address tem AMBOS poolId e poolId_v2 no FSN_data, usar poolId
- Se NÃO tem ambos, remover essas linhas
"""

import pandas as pd

def final_cleanup():
    """
    Faz o pente fino final nos dados faltantes.
    """
    print("=" * 60)
    print("🔍 Pente Fino Final: Verificação de pool_address")
    print("=" * 60)
    
    print("\n📖 Lendo arquivos...")
    
    # Ler o arquivo principal
    main_df = pd.read_csv('data/balancer_v2_pre_final_merge.csv')
    print(f"✅ balancer_v2_pre_final_merge.csv: {len(main_df):,} linhas")
    
    # Ler o arquivo FSN_data
    fsn_df = pd.read_csv('data/FSN_data.csv')
    print(f"✅ FSN_data.csv: {len(fsn_df):,} linhas")
    
    # Identificar linhas com pool_address faltante
    print("\n🔍 Identificando linhas com pool_address faltante...")
    missing_pool_mask = main_df['pool_address'].isna()
    missing_pool_df = main_df[missing_pool_mask].copy()
    print(f"   Linhas com pool_address faltante: {len(missing_pool_df):,}")
    
    # Verificar gauge_address únicos faltantes
    missing_gauges = missing_pool_df['gauge_address'].unique()
    print(f"   Gauge_address únicos faltantes: {len(missing_gauges):,}")
    
    # Criar um mapeamento do FSN_data
    print("\n🔄 Criando mapeamento do FSN_data...")
    
    # Filtrar linhas que têm AMBOS poolId e poolId_v2 preenchidos
    fsn_both = fsn_df[
        fsn_df['poolId'].notna() & (fsn_df['poolId'] != '') &
        fsn_df['poolId_v2'].notna() & (fsn_df['poolId_v2'] != '')
    ].copy()
    
    print(f"   Linhas no FSN_data com AMBOS poolId e poolId_v2: {len(fsn_both):,}")
    
    # Criar mapeamento: gauge_address (id) -> poolId
    gauge_to_poolid = dict(zip(fsn_both['id'], fsn_both['poolId']))
    print(f"   Mapeamentos criados: {len(gauge_to_poolid):,}")
    
    # Verificar quantos gauge_address faltantes estão no mapeamento
    matching_gauges = [g for g in missing_gauges if g in gauge_to_poolid]
    print(f"   Gauge_address faltantes encontrados no mapeamento: {len(matching_gauges):,}")
    
    # Preencher pool_address com poolId onde disponível
    print("\n✏️  Preenchendo pool_address com poolId...")
    
    filled_count = 0
    for idx in missing_pool_df.index:
        gauge = missing_pool_df.loc[idx, 'gauge_address']
        if gauge in gauge_to_poolid:
            missing_pool_df.loc[idx, 'pool_address'] = gauge_to_poolid[gauge]
            filled_count += 1
    
    print(f"   ✅ pool_address preenchidos: {filled_count:,}")
    
    # Identificar linhas que ainda estão faltando (não têm ambos poolId e poolId_v2)
    still_missing = missing_pool_df['pool_address'].isna()
    to_remove_count = still_missing.sum()
    print(f"\n🗑️  Linhas a serem removidas (sem poolId e poolId_v2): {to_remove_count:,}")
    
    # Mostrar alguns exemplos das linhas que serão removidas
    if to_remove_count > 0:
        print("\n📋 Exemplos de linhas que serão removidas:")
        examples = missing_pool_df[still_missing][['gauge_address', 'pool_address', 'blockchain', 'symbol', 'day']].head(5)
        print(examples.to_string())
        
        # Verificar no FSN_data se esses gauge_address existem
        print("\n🔍 Verificando esses gauge_address no FSN_data:")
        for gauge in examples['gauge_address'].head(3):
            fsn_row = fsn_df[fsn_df['id'] == gauge]
            if len(fsn_row) > 0:
                row = fsn_row.iloc[0]
                print(f"   gauge: {gauge}")
                print(f"     poolId: {row['poolId']}")
                print(f"     poolId_v2: {row['poolId_v2']}")
                print(f"     chain: {row['chain']}")
            else:
                print(f"   gauge: {gauge} - NÃO encontrado no FSN_data")
    
    # Atualizar o arquivo principal
    print("\n🔄 Atualizando arquivo principal...")
    
    # Atualizar pool_address nas linhas que foram preenchidas
    main_df.loc[missing_pool_mask, 'pool_address'] = missing_pool_df['pool_address']
    
    # Remover linhas que ainda têm pool_address faltante
    before_remove = len(main_df)
    main_df = main_df[main_df['pool_address'].notna()].copy()
    after_remove = len(main_df)
    removed_count = before_remove - after_remove
    
    print(f"   Linhas antes: {before_remove:,}")
    print(f"   Linhas removidas: {removed_count:,}")
    print(f"   Linhas depois: {after_remove:,}")
    
    # Estatísticas finais
    print("\n📊 Estatísticas finais:")
    print(f"   Total de linhas: {len(main_df):,}")
    print(f"   Linhas com pool_address faltante: {main_df['pool_address'].isna().sum():,}")
    print(f"   Linhas com blockchain faltante: {main_df['blockchain'].isna().sum():,}")
    
    # Salvar o arquivo atualizado
    output_file = 'data/balancer_v2_pre_final_merge.csv'
    print(f"\n💾 Salvando arquivo atualizado: {output_file}")
    main_df.to_csv(output_file, index=False)
    
    print(f"✅ Arquivo salvo com sucesso!")
    
    # Criar um CSV com as linhas removidas para análise
    if to_remove_count > 0:
        removed_df = missing_pool_df[still_missing].copy()
        removed_file = 'data/removed_lines_no_poolid.csv'
        print(f"\n💾 Salvando linhas removidas em: {removed_file}")
        removed_df.to_csv(removed_file, index=False)
        print(f"   Total de linhas removidas salvas: {len(removed_df):,}")
    
    return main_df

if __name__ == "__main__":
    try:
        result_df = final_cleanup()
        print("\n" + "=" * 60)
        print("✅ Processo concluído com sucesso!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()
