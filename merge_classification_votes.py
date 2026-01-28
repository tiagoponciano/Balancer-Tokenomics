"""
Script para mesclar as informações de classificação core/non-core
do arquivo classification_core_pools.csv com o arquivo vebal_votes_valid.csv.

O merge é feito usando:
- address (classification) = pool_address (vebal_votes)
- day (ambos os arquivos)
"""

import pandas as pd
from datetime import datetime

def merge_classification_votes():
    """
    Mescla as informações de classificação core/non-core com os dados de votos.
    """
    print("=" * 60)
    print("🚀 Merge: Classification Core Pools + veBAL Votes")
    print("=" * 60)
    
    print("\n📖 Lendo arquivos...")
    
    # Ler o arquivo de classificação
    classification_df = pd.read_csv('data/classification_core_pools.csv')
    print(f"✅ Classification CSV: {len(classification_df):,} linhas")
    print(f"   Colunas: {list(classification_df.columns)}")
    
    # Ler o arquivo de votos
    votes_df = pd.read_csv('data/vebal_votes_valid.csv')
    print(f"✅ Votes CSV: {len(votes_df):,} linhas")
    print(f"   Colunas: {list(votes_df.columns)}")
    
    # Converter datas para datetime para garantir compatibilidade
    print("\n🔄 Convertendo datas...")
    classification_df['day'] = pd.to_datetime(classification_df['day'], errors='coerce')
    votes_df['day'] = pd.to_datetime(votes_df['day'], errors='coerce')
    
    # Normalizar datas para apenas a data (sem hora) para garantir correspondência
    classification_df['day'] = classification_df['day'].dt.normalize()
    votes_df['day'] = votes_df['day'].dt.normalize()
    
    # Remover linhas com datas inválidas
    classification_df = classification_df.dropna(subset=['day'])
    votes_df = votes_df.dropna(subset=['day'])
    
    print(f"✅ Classification após limpeza: {len(classification_df):,} linhas")
    print(f"✅ Votes após limpeza: {len(votes_df):,} linhas")
    
    # Reduzir o address para 42 caracteres (endereço base da pool)
    print("\n✂️  Reduzindo addresses do classification para 42 caracteres...")
    print(f"   Formato original: {classification_df['address'].iloc[0]}")
    classification_df['address_short'] = classification_df['address'].str[:42]
    print(f"   Formato reduzido: {classification_df['address_short'].iloc[0]}")
    
    # Verificar valores únicos para entender melhor os dados
    print("\n📊 Estatísticas dos dados:")
    print(f"   Addresses únicos em classification (original): {classification_df['address'].nunique():,}")
    print(f"   Addresses únicos em classification (reduzido): {classification_df['address_short'].nunique():,}")
    print(f"   Pool addresses únicos em votes: {votes_df['pool_address'].nunique():,}")
    print(f"   Datas únicas em classification: {classification_df['day'].nunique():,}")
    print(f"   Datas únicas em votes: {votes_df['day'].nunique():,}")
    
    # Verificar se há valores de is_core
    print(f"\n📊 Valores de is_core:")
    print(classification_df['is_core'].value_counts())
    
    # Verificar correspondência antes do merge
    print("\n🔍 Verificando correspondência de addresses...")
    classification_addresses_set = set(classification_df['address_short'].unique())
    votes_addresses_set = set(votes_df['pool_address'].unique())
    intersection = classification_addresses_set & votes_addresses_set
    print(f"   Addresses em classification (reduzido): {len(classification_addresses_set):,}")
    print(f"   Addresses em votes: {len(votes_addresses_set):,}")
    print(f"   Intersecção (correspondências): {len(intersection):,}")
    
    if len(intersection) > 0:
        print(f"   ✅ Encontradas {len(intersection):,} correspondências!")
    else:
        print(f"   ⚠️  Nenhuma correspondência encontrada. Verificando amostras...")
        print(f"   Sample classification: {list(classification_addresses_set)[:3]}")
        print(f"   Sample votes: {list(votes_addresses_set)[:3]}")
    
    # Fazer o merge
    print("\n🔗 Fazendo merge dos dados...")
    print("   Chaves de merge:")
    print("   - classification['address_short'] = votes['pool_address']")
    print("   - classification['day'] = votes['day']")
    
    # Preparar o classification_df para o merge usando o address reduzido
    classification_renamed = classification_df.rename(columns={'address_short': 'pool_address'})
    
    # Fazer o merge usando left join para manter todas as linhas do votes_df
    merged_df = votes_df.merge(
        classification_renamed[['pool_address', 'day', 'is_core']],
        on=['pool_address', 'day'],
        how='left'
    )
    
    print(f"✅ Merge concluído!")
    print(f"   Linhas no resultado: {len(merged_df):,}")
    
    # Verificar quantas linhas receberam a classificação
    classified_count = merged_df['is_core'].notna().sum()
    unclassified_count = merged_df['is_core'].isna().sum()
    
    print(f"\n📊 Resultado do merge:")
    print(f"   Linhas classificadas (is_core preenchido): {classified_count:,} ({100 * classified_count / len(merged_df):.2f}%)")
    print(f"   Linhas não classificadas (is_core = NaN): {unclassified_count:,} ({100 * unclassified_count / len(merged_df):.2f}%)")
    
    # Verificar valores de is_core após o merge
    print(f"\n📊 Distribuição de is_core após merge:")
    print(merged_df['is_core'].value_counts(dropna=False))
    
    # Preencher valores NaN com False (assumindo que se não está no classification, é non-core)
    print("\n🔄 Preenchendo valores NaN com False (non-core)...")
    merged_df['is_core'] = merged_df['is_core'].fillna(False)
    
    print(f"✅ Valores preenchidos!")
    print(f"\n📊 Distribuição final de is_core:")
    print(merged_df['is_core'].value_counts())
    
    # Verificar algumas amostras
    print("\n📋 Amostra dos dados mesclados:")
    print(merged_df.head(10).to_string())
    
    # Verificar se há algum problema com o merge
    print("\n🔍 Verificando integridade dos dados...")
    
    # Verificar se todas as colunas originais foram preservadas
    original_cols = set(votes_df.columns)
    merged_cols = set(merged_df.columns)
    
    if original_cols.issubset(merged_cols):
        print("✅ Todas as colunas originais foram preservadas")
    else:
        missing_cols = original_cols - merged_cols
        print(f"⚠️  Colunas faltando: {missing_cols}")
    
    # Verificar se a coluna is_core foi adicionada
    if 'is_core' in merged_df.columns:
        print("✅ Coluna 'is_core' adicionada com sucesso")
    else:
        print("❌ Coluna 'is_core' não foi adicionada!")
    
    # Salvar o resultado
    output_file = 'data/balancer_v2_pre_final_merge.csv'
    print(f"\n💾 Salvando resultado em {output_file}...")
    
    # Ordenar por day e pool_address
    merged_df = merged_df.sort_values(['day', 'pool_address'])
    
    # Salvar o CSV
    merged_df.to_csv(output_file, index=False)
    
    print(f"✅ Arquivo salvo com sucesso!")
    print(f"   Total de linhas: {len(merged_df):,}")
    print(f"   Total de colunas: {len(merged_df.columns)}")
    print(f"   Colunas: {list(merged_df.columns)}")
    
    # Estatísticas finais
    print("\n📊 Estatísticas finais:")
    print(f"   Total de linhas: {len(merged_df):,}")
    print(f"   Linhas com is_core = True: {merged_df['is_core'].sum():,} ({100 * merged_df['is_core'].sum() / len(merged_df):.2f}%)")
    print(f"   Linhas com is_core = False: {(~merged_df['is_core']).sum():,} ({100 * (~merged_df['is_core']).sum() / len(merged_df):.2f}%)")
    
    return merged_df

if __name__ == "__main__":
    try:
        result_df = merge_classification_votes()
        print("\n" + "=" * 60)
        print("✅ Processo concluído com sucesso!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()
