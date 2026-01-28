"""
Script para preencher dados faltantes no balancer_v2_pre_final_merge.csv
usando informações do FSN_data.csv.

O FSN_data.csv contém:
- id: gauge_address
- chain: blockchain
- poolId_v2: pool_address (42 caracteres)
"""

import pandas as pd

def fill_missing_data():
    """
    Preenche dados faltantes usando FSN_data.csv.
    """
    print("=" * 60)
    print("🔧 Preenchimento de Dados Faltantes")
    print("=" * 60)
    
    print("\n📖 Lendo arquivos...")
    
    # Ler o arquivo principal
    main_df = pd.read_csv('data/balancer_v2_pre_final_merge.csv')
    print(f"✅ balancer_v2_pre_final_merge.csv: {len(main_df):,} linhas")
    
    # Ler o arquivo FSN_data
    fsn_df = pd.read_csv('data/FSN_data.csv')
    print(f"✅ FSN_data.csv: {len(fsn_df):,} linhas")
    print(f"   Colunas: {list(fsn_df.columns)}")
    
    # Verificar dados faltantes
    print("\n📊 Verificando dados faltantes:")
    missing_pool_address = main_df['pool_address'].isna().sum()
    missing_blockchain = main_df['blockchain'].isna().sum()
    print(f"   Linhas com pool_address faltante: {missing_pool_address:,}")
    print(f"   Linhas com blockchain faltante: {missing_blockchain:,}")
    
    # Preparar o mapeamento do FSN_data
    print("\n🔄 Preparando mapeamento do FSN_data...")
    
    # Criar dicionários de mapeamento
    # id (gauge_address) -> poolId_v2 (pool_address)
    # id (gauge_address) -> chain (blockchain)
    
    # Filtrar apenas linhas com poolId_v2 válido
    fsn_valid = fsn_df[fsn_df['poolId_v2'].notna() & (fsn_df['poolId_v2'] != '')].copy()
    print(f"   Linhas válidas no FSN_data: {len(fsn_valid):,}")
    
    # Criar mapeamentos
    gauge_to_pool = dict(zip(fsn_valid['id'], fsn_valid['poolId_v2']))
    gauge_to_chain = dict(zip(fsn_valid['id'], fsn_valid['chain']))
    
    print(f"   Mapeamentos criados:")
    print(f"     gauge_address -> pool_address: {len(gauge_to_pool):,}")
    print(f"     gauge_address -> blockchain: {len(gauge_to_chain):,}")
    
    # Mostrar alguns exemplos
    print("\n📋 Exemplos de mapeamento:")
    sample_gauges = list(gauge_to_pool.keys())[:3]
    for gauge in sample_gauges:
        print(f"   gauge: {gauge}")
        print(f"     -> pool_address: {gauge_to_pool[gauge]}")
        print(f"     -> blockchain: {gauge_to_chain[gauge]}")
    
    # Filtrar linhas com dados faltantes
    print("\n🔍 Filtrando linhas com dados faltantes...")
    missing_mask = main_df['pool_address'].isna() | main_df['blockchain'].isna()
    missing_df = main_df[missing_mask].copy()
    print(f"   Linhas com dados faltantes: {len(missing_df):,}")
    
    # Verificar quantos gauge_address das linhas faltantes estão no mapeamento
    missing_gauges = missing_df['gauge_address'].unique()
    matching_gauges = [g for g in missing_gauges if g in gauge_to_pool]
    print(f"   Gauge_address únicos faltantes: {len(missing_gauges):,}")
    print(f"   Gauge_address encontrados no FSN_data: {len(matching_gauges):,}")
    
    # Preencher os dados faltantes
    print("\n✏️  Preenchendo dados faltantes...")
    
    filled_count_pool = 0
    filled_count_chain = 0
    
    for idx in missing_df.index:
        gauge = missing_df.loc[idx, 'gauge_address']
        
        # Preencher pool_address se faltar e existir no mapeamento
        if pd.isna(missing_df.loc[idx, 'pool_address']) and gauge in gauge_to_pool:
            missing_df.loc[idx, 'pool_address'] = gauge_to_pool[gauge]
            filled_count_pool += 1
        
        # Preencher blockchain se faltar e existir no mapeamento
        if pd.isna(missing_df.loc[idx, 'blockchain']) and gauge in gauge_to_chain:
            missing_df.loc[idx, 'blockchain'] = gauge_to_chain[gauge]
            filled_count_chain += 1
    
    print(f"   ✅ pool_address preenchidos: {filled_count_pool:,}")
    print(f"   ✅ blockchain preenchidos: {filled_count_chain:,}")
    
    # Verificar quantos ainda estão faltando
    still_missing_pool = missing_df['pool_address'].isna().sum()
    still_missing_chain = missing_df['blockchain'].isna().sum()
    print(f"\n📊 Após preenchimento:")
    print(f"   pool_address ainda faltantes: {still_missing_pool:,}")
    print(f"   blockchain ainda faltantes: {still_missing_chain:,}")
    
    # Estatísticas finais
    print("\n📊 Estatísticas finais do dataset preenchido:")
    print(f"   Total de linhas: {len(missing_df):,}")
    print(f"   Linhas com pool_address preenchido: {(missing_df['pool_address'].notna()).sum():,}")
    print(f"   Linhas com blockchain preenchido: {(missing_df['blockchain'].notna()).sum():,}")
    
    # Mostrar amostra
    print("\n📋 Amostra dos dados preenchidos:")
    sample_cols = ['gauge_address', 'pool_address', 'blockchain', 'symbol', 'day']
    print(missing_df[sample_cols].head(10).to_string())
    
    # Salvar o arquivo
    output_file = 'data/missing_data_filled.csv'
    print(f"\n💾 Salvando arquivo: {output_file}")
    missing_df.to_csv(output_file, index=False)
    
    print(f"✅ Arquivo salvo com sucesso!")
    print(f"   Total de linhas: {len(missing_df):,}")
    
    # Também atualizar o arquivo original
    print(f"\n🔄 Atualizando arquivo original...")
    main_df.loc[missing_mask, 'pool_address'] = missing_df['pool_address']
    main_df.loc[missing_mask, 'blockchain'] = missing_df['blockchain']
    
    original_output = 'data/balancer_v2_pre_final_merge.csv'
    main_df.to_csv(original_output, index=False)
    print(f"✅ Arquivo original atualizado: {original_output}")
    
    # Estatísticas do arquivo original atualizado
    print(f"\n📊 Estatísticas do arquivo original após atualização:")
    print(f"   Total de linhas: {len(main_df):,}")
    print(f"   Linhas com pool_address faltante: {main_df['pool_address'].isna().sum():,}")
    print(f"   Linhas com blockchain faltante: {main_df['blockchain'].isna().sum():,}")
    
    return missing_df, main_df

if __name__ == "__main__":
    try:
        missing_df, main_df = fill_missing_data()
        print("\n" + "=" * 60)
        print("✅ Processo concluído com sucesso!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()
