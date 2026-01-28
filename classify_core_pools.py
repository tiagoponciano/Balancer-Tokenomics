"""
Script para classificar pools como core ou non-core baseado no histórico do CSV.

Regra lógica:
Uma pool é CORE em uma data D se existir no CSV uma linha tal que:
- address = pool_address
- D >= added_date
- (removed_date IS NULL OR D < removed_date)

Caso contrário, ela é NON-CORE.
"""

import pandas as pd
from datetime import datetime
import numpy as np

def classify_core_pools():
    """
    Classifica pools como core ou non-core baseado no histórico.
    """
    print("📖 Lendo arquivos...")
    
    # Ler o CSV histórico de core pools
    core_pools_df = pd.read_csv('data/core_pools_results.csv')
    
    # Ler o dataset diário
    daily_df = pd.read_csv('data/balancer_v2_financial_master_final.csv')
    
    print(f"✅ Core pools CSV: {len(core_pools_df)} linhas")
    print(f"✅ Dataset diário: {len(daily_df)} linhas")
    
    # Converter datas para datetime
    print("\n🔄 Convertendo datas...")
    core_pools_df['added_date'] = pd.to_datetime(core_pools_df['added_date'], errors='coerce')
    core_pools_df['removed_date'] = pd.to_datetime(core_pools_df['removed_date'], errors='coerce')
    daily_df['block_date'] = pd.to_datetime(daily_df['block_date'], errors='coerce')
    
    # Normalizar timezones - remover timezone se existir (tornar tudo tz-naive)
    # Isso evita problemas de comparação entre tz-aware e tz-naive
    def remove_timezone(series):
        """Remove timezone de uma série de datetime se existir."""
        try:
            if series.dt.tz is not None:
                return series.dt.tz_localize(None)
        except (AttributeError, TypeError):
            pass
        return series
    
    core_pools_df['added_date'] = remove_timezone(core_pools_df['added_date'])
    core_pools_df['removed_date'] = remove_timezone(core_pools_df['removed_date'])
    daily_df['block_date'] = remove_timezone(daily_df['block_date'])
    
    # Remover linhas com datas inválidas
    daily_df = daily_df.dropna(subset=['block_date'])
    core_pools_df = core_pools_df.dropna(subset=['added_date'])
    
    print(f"✅ Dataset diário após limpeza: {len(daily_df)} linhas")
    
    print("\n🔍 Classificando pools...")
    
    # Criar uma função vetorizada para classificação
    def classify_row(row):
        """
        Classifica uma linha do dataset diário como core ou non-core.
        """
        address = row['project_contract_address']
        date = row['block_date']
        
        # Normalizar data para tz-naive se necessário
        if pd.notna(date):
            if isinstance(date, pd.Timestamp) and date.tz is not None:
                date = date.tz_localize(None)
        
        # Filtrar registros do core_pools_df para este address
        pool_records = core_pools_df[core_pools_df['address'] == address]
        
        if len(pool_records) == 0:
            return False
        
        # Verificar se existe algum registro onde:
        # - date >= added_date
        # - (removed_date IS NULL OR date < removed_date)
        for _, record in pool_records.iterrows():
            added_date = record['added_date']
            removed_date = record['removed_date']
            
            # Normalizar added_date se necessário
            if pd.notna(added_date):
                if isinstance(added_date, pd.Timestamp) and added_date.tz is not None:
                    added_date = added_date.tz_localize(None)
            
            # Normalizar removed_date se necessário
            if pd.notna(removed_date):
                if isinstance(removed_date, pd.Timestamp) and removed_date.tz is not None:
                    removed_date = removed_date.tz_localize(None)
            
            # Verificar se a data está dentro do intervalo válido
            if pd.notna(added_date) and date >= added_date:
                # Se removed_date é NULL, a pool ainda é core
                if pd.isna(removed_date):
                    return True
                # Se removed_date não é NULL, verificar se date < removed_date
                elif date < removed_date:
                    return True
        
        return False
    
    # Otimização: processar apenas combinações únicas de address + date
    print("📊 Criando combinações únicas de address + date...")
    unique_combinations = daily_df[['project_contract_address', 'block_date']].drop_duplicates()
    print(f"   Total de combinações únicas: {len(unique_combinations):,}")
    
    # Criar um dicionário para cache de resultados
    print("⏳ Processando classificação (isso pode levar alguns minutos)...")
    classification_cache = {}
    
    # Processar em lotes para melhor performance e feedback
    batch_size = 5000
    total_batches = (len(unique_combinations) + batch_size - 1) // batch_size
    
    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min((batch_idx + 1) * batch_size, len(unique_combinations))
        batch = unique_combinations.iloc[start_idx:end_idx]
        
        # Processar batch usando apply
        batch_results = batch.apply(classify_row, axis=1)
        
        # Armazenar no cache
        for idx, result in zip(batch.index, batch_results):
            address = batch.loc[idx, 'project_contract_address']
            date = batch.loc[idx, 'block_date']
            cache_key = (address, date)
            classification_cache[cache_key] = result
        
        if (batch_idx + 1) % 20 == 0 or (batch_idx + 1) == total_batches:
            print(f"  Processado {end_idx:,}/{len(unique_combinations):,} combinações ({100 * end_idx / len(unique_combinations):.1f}%)")
    
    print("✅ Cache de classificação criado!")
    
    # Aplicar a classificação ao dataset completo usando o cache
    print("\n🔄 Aplicando classificação ao dataset completo...")
    daily_df['is_core'] = daily_df.apply(
        lambda row: classification_cache.get(
            (row['project_contract_address'], row['block_date']), 
            False
        ), 
        axis=1
    )
    
    # Estatísticas
    total_rows = len(daily_df)
    core_rows = daily_df['is_core'].sum()
    non_core_rows = total_rows - core_rows
    
    print(f"\n📊 Estatísticas:")
    print(f"  Total de linhas: {total_rows:,}")
    print(f"  Core: {core_rows:,} ({100 * core_rows / total_rows:.2f}%)")
    print(f"  Non-core: {non_core_rows:,} ({100 * non_core_rows / total_rows:.2f}%)")
    
    # Salvar o resultado
    output_file = 'data/classification_core_pools.csv'
    print(f"\n💾 Salvando resultado em {output_file}...")
    
    # Selecionar apenas as colunas relevantes para o CSV de saída
    # Baseado no exemplo fornecido, parece que precisamos de: address, day, is_core
    output_df = daily_df[['project_contract_address', 'block_date', 'is_core']].copy()
    output_df.columns = ['address', 'day', 'is_core']
    
    # Converter is_core para boolean (True/False) conforme o exemplo
    output_df['is_core'] = output_df['is_core'].astype(bool)
    
    # Ordenar por address e date
    output_df = output_df.sort_values(['address', 'day'])
    
    output_df.to_csv(output_file, index=False)
    
    print(f"✅ Arquivo salvo com sucesso!")
    print(f"   Total de linhas no arquivo de saída: {len(output_df):,}")
    
    # Mostrar algumas amostras
    print("\n📋 Amostra dos resultados:")
    print(output_df.head(20).to_string())
    
    # Verificar alguns casos específicos para validação
    print("\n🔍 Validação - Verificando alguns casos específicos:")
    
    # Pegar alguns addresses únicos para verificar
    sample_addresses = daily_df['project_contract_address'].unique()[:5]
    
    for address in sample_addresses:
        address_data = output_df[output_df['address'] == address].head(5)
        if len(address_data) > 0:
            print(f"\n  Address: {address}")
            print(address_data.to_string(index=False))
    
    return output_df

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Classificação de Core Pools")
    print("=" * 60)
    
    try:
        result_df = classify_core_pools()
        print("\n" + "=" * 60)
        print("✅ Processo concluído com sucesso!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()
