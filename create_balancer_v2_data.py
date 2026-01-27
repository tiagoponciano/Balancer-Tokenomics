"""
Script para criar o arquivo final balancer_v2_data.csv
Seguindo o plano da ata de reunião:
- Separar dados de gauge (votos/emissões) de dados de pool (TVL, volume, fees)
- Trabalhar com dados por round (não históricos agregados)
- Aplicar mapping pool ↔ gauge correto
- Fazer merge final apenas após cada conjunto estar agregado
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# Configuração de paths
DATA_DIR = "data"
OUTPUT_DIR = "data"

def normalize_address(addr):
    """Normaliza endereços para comparação (lowercase, sem espaços)"""
    if pd.isna(addr) or addr == '':
        return None
    return str(addr).lower().strip()

def load_data():
    """Carrega todos os arquivos necessários"""
    print("📂 Carregando arquivos de dados...")
    
    # 1. Dados de votos por gauge e round
    votes_file = os.path.join(DATA_DIR, "veBAL_Valid_Votes_by_Gauge.csv")
    df_votes = pd.read_csv(votes_file)
    print(f"  ✓ veBAL_Valid_Votes_by_Gauge.csv: {len(df_votes)} registros")
    
    # 2. Dados de emissões por gauge e round
    emissions_file = os.path.join(DATA_DIR, "BAL_Emissions_by_GaugePool_valid.csv")
    df_emissions = pd.read_csv(emissions_file)
    print(f"  ✓ BAL_Emissions_by_GaugePool_valid.csv: {len(df_emissions)} registros")
    
    # 3. Mapping de gauges (FSN_data.csv já tem poolId_v2 processado)
    mapping_file = os.path.join(DATA_DIR, "FSN_data.csv")
    df_mapping = pd.read_csv(mapping_file)
    print(f"  ✓ FSN_data.csv: {len(df_mapping)} registros")
    
    # 4. Dados financeiros por pool (diários) - usar arquivo original limpo
    financial_file = os.path.join(DATA_DIR, "veBAL.csv")
    df_financial = pd.read_csv(financial_file)
    print(f"  ✓ veBAL.csv (dados financeiros limpos): {len(df_financial)} registros")
    
    # 5. Core pools mapping
    core_file = os.path.join(DATA_DIR, "core_pools_results.csv")
    df_core = pd.read_csv(core_file)
    print(f"  ✓ core_pools_results.csv: {len(df_core)} registros")
    
    return df_votes, df_emissions, df_mapping, df_financial, df_core

def process_gauge_data(df_votes, df_emissions):
    """
    Etapa 1: Reestruturar os dados de veBAL (gauge)
    Trabalhar os dados de votos e emissões exclusivamente por round e gauge
    """
    print("\n🔧 ETAPA 1: Processando dados de gauge (votos e emissões)...")
    
    # Normalizar gauge addresses
    df_votes['gauge_address'] = df_votes['gauge'].apply(normalize_address)
    df_emissions['gauge_address'] = df_emissions['gauge_address'].apply(normalize_address)
    
    # Normalizar datas - garantir timezone-naive
    df_votes['start_date'] = pd.to_datetime(df_votes['start_date']).dt.tz_localize(None).dt.normalize()
    df_votes['end_date'] = pd.to_datetime(df_votes['end_date']).dt.tz_localize(None).dt.normalize()
    df_emissions['start_date'] = pd.to_datetime(df_emissions['start_date']).dt.tz_localize(None).dt.normalize()
    df_emissions['end_date'] = pd.to_datetime(df_emissions['end_date']).dt.tz_localize(None).dt.normalize()
    
    # Merge votos e emissões por round e gauge
    df_gauge = df_votes.merge(
        df_emissions,
        on=['round_id', 'gauge_address', 'start_date', 'end_date'],
        how='outer',
        suffixes=('_votes', '_emissions')
    )
    
    # Preencher campos que podem estar vazios
    if 'symbol_votes' in df_gauge.columns and 'symbol_emissions' in df_gauge.columns:
        df_gauge['symbol'] = df_gauge['symbol_votes'].fillna(df_gauge['symbol_emissions'])
    elif 'symbol_votes' in df_gauge.columns:
        df_gauge['symbol'] = df_gauge['symbol_votes']
    elif 'symbol_emissions' in df_gauge.columns:
        df_gauge['symbol'] = df_gauge['symbol_emissions']
    
    # Selecionar colunas relevantes
    gauge_cols = [
        'round_id', 'start_date', 'end_date', 'gauge_address', 'blockchain',
        'votes', 'pct_votes', 'symbol',
        'round_emissions', 'round_emissions_usd', 'round_fees',
        'pool_address'  # do df_emissions, pode estar vazio
    ]
    
    df_gauge = df_gauge[[c for c in gauge_cols if c in df_gauge.columns]]
    
    # Preencher valores nulos
    numeric_cols = ['votes', 'pct_votes', 'round_emissions', 'round_emissions_usd', 'round_fees']
    for col in numeric_cols:
        if col in df_gauge.columns:
            df_gauge[col] = df_gauge[col].fillna(0)
    
    print(f"  ✓ Dados de gauge processados: {len(df_gauge)} registros")
    print(f"  ✓ Rounds únicos: {df_gauge['round_id'].nunique()}")
    print(f"  ✓ Gauges únicos: {df_gauge['gauge_address'].nunique()}")
    
    return df_gauge

def process_mapping(df_mapping):
    """
    Etapa 2: Processar mapping gauge → pool
    Filtrar apenas pools v2 (42 caracteres) e mapear chains
    """
    print("\n🔗 ETAPA 2: Processando mapping gauge → pool...")
    
    # Normalizar gauge addresses
    df_mapping['gauge_address'] = df_mapping['id'].apply(normalize_address)
    
    # Filtrar apenas pools v2 (poolId_v2 com 42 caracteres)
    df_mapping['poolId_v2_len'] = df_mapping['poolId_v2'].astype(str).str.len()
    df_mapping_v2 = df_mapping[df_mapping['poolId_v2_len'] == 42].copy()
    
    # Normalizar pool address
    df_mapping_v2['pool_address'] = df_mapping_v2['poolId_v2'].apply(normalize_address)
    
    # Remover linhas sem chain válido
    df_mapping_v2 = df_mapping_v2[df_mapping_v2['chain'].notna()].copy()
    
    # Selecionar colunas relevantes
    mapping_cols = ['gauge_address', 'pool_address', 'chain', 'status', 'poolId']
    df_mapping_v2 = df_mapping_v2[[c for c in mapping_cols if c in df_mapping_v2.columns]]
    
    print(f"  ✓ Mapping processado: {len(df_mapping_v2)} registros")
    print(f"  ✓ Gauges únicos: {df_mapping_v2['gauge_address'].nunique()}")
    print(f"  ✓ Pools únicos: {df_mapping_v2['pool_address'].nunique()}")
    
    return df_mapping_v2

def merge_gauge_with_pool(df_gauge, df_mapping):
    """
    Etapa 3: Aplicar o mapping pool ↔ gauge
    Unir dados de gauge com dados de pool via mapping
    """
    print("\n🔗 ETAPA 3: Aplicando mapping gauge → pool...")
    
    # Merge gauge com mapping
    df_gauge_pool = df_gauge.merge(
        df_mapping,
        on='gauge_address',
        how='left'
    )
    
    # Se pool_address estava vazio no df_gauge, usar do mapping
    df_gauge_pool['pool_address'] = df_gauge_pool['pool_address_x'].fillna(df_gauge_pool['pool_address_y'])
    
    # Se chain estava vazio no df_gauge, usar do mapping
    df_gauge_pool['blockchain'] = df_gauge_pool['blockchain'].fillna(df_gauge_pool['chain'])
    
    # Remover colunas duplicadas
    cols_to_drop = [c for c in df_gauge_pool.columns if c.endswith('_x') or c.endswith('_y')]
    df_gauge_pool = df_gauge_pool.drop(columns=cols_to_drop)
    
    # Remover duplicatas - garantir uma linha por round por gauge
    before_dedup = len(df_gauge_pool)
    key_cols = ['round_id', 'gauge_address']
    df_gauge_pool = df_gauge_pool.drop_duplicates(subset=key_cols, keep='first')
    after_dedup = len(df_gauge_pool)
    if before_dedup != after_dedup:
        print(f"  ⚠️ Removidas {before_dedup - after_dedup} duplicatas no merge gauge-pool")
    
    print(f"  ✓ Merge gauge-pool concluído: {len(df_gauge_pool)} registros")
    print(f"  ✓ Gauges com pool mapeado: {df_gauge_pool['pool_address'].notna().sum()}")
    print(f"  ✓ Gauges sem pool mapeado: {df_gauge_pool['pool_address'].isna().sum()}")
    
    return df_gauge_pool

def process_financial_data(df_financial):
    """
    Etapa 4: Manter os dados de pool separados
    Processar dados financeiros por pool e data
    Usar apenas dados financeiros limpos (sem votos/emissões)
    """
    print("\n💰 ETAPA 4: Processando dados financeiros por pool...")
    
    # Filtrar apenas dados a partir de 2024-01-01 (mesmo filtro usado antes)
    cutoff_date = '2024-01-01'
    df_financial['block_date'] = pd.to_datetime(df_financial['block_date'])
    df_financial = df_financial[df_financial['block_date'] >= cutoff_date].copy()
    
    # Normalizar endereços (primeiros 42 caracteres para pools v2)
    df_financial['pool_address'] = df_financial['project_contract_address'].apply(
        lambda x: normalize_address(str(x)[:42]) if pd.notna(x) else None
    )
    
    # Normalizar datas - garantir timezone-naive
    df_financial['block_date'] = pd.to_datetime(df_financial['block_date']).dt.tz_localize(None).dt.normalize()
    
    # Remover colunas que não são financeiras (votos/emissões)
    cols_to_drop = ['bal_emited_votes', 'votes_received', 'direct_incentives', 'core_non_core']
    df_financial = df_financial.drop(columns=[c for c in cols_to_drop if c in df_financial.columns])
    
    print(f"  ✓ Dados financeiros processados: {len(df_financial)} registros")
    print(f"  ✓ Pools únicos: {df_financial['pool_address'].nunique()}")
    print(f"  ✓ Datas únicas: {df_financial['block_date'].nunique()}")
    
    return df_financial

def apply_core_pool_mapping(df_final, df_core):
    """
    Etapa 5: Aplicar mapeamento de Core Pools com lógica temporal
    """
    print("\n⭐ ETAPA 5: Aplicando mapeamento de Core Pools...")
    
    # Normalizar endereços
    df_core['address'] = df_core['address'].apply(lambda x: normalize_address(str(x)[:42]) if pd.notna(x) else None)
    df_final['pool_address_normalized'] = df_final['pool_address'].apply(normalize_address)
    
    # Normalizar datas - garantir que todas sejam timezone-naive
    df_core['added_date'] = pd.to_datetime(df_core['added_date']).dt.tz_localize(None).dt.normalize()
    df_core['removed_date'] = pd.to_datetime(df_core['removed_date']).dt.tz_localize(None).dt.normalize()
    df_core['removed_date'] = df_core['removed_date'].fillna(pd.Timestamp.max)
    
    # Garantir que start_date e block_date também sejam timezone-naive
    if 'start_date' in df_final.columns:
        df_final['start_date'] = pd.to_datetime(df_final['start_date']).dt.tz_localize(None).dt.normalize()
    if 'end_date' in df_final.columns:
        df_final['end_date'] = pd.to_datetime(df_final['end_date']).dt.tz_localize(None).dt.normalize()
    if 'block_date' in df_final.columns:
        df_final['block_date'] = pd.to_datetime(df_final['block_date']).dt.tz_localize(None).dt.normalize()
    
    # Criar lookup temporal
    merged_core = df_final[['pool_address_normalized', 'start_date']].merge(
        df_core[['address', 'added_date', 'removed_date', 'chain']],
        left_on='pool_address_normalized',
        right_on='address',
        how='inner'
    )
    
    # Validar: pool é Core APENAS se a data está dentro da janela
    valid_core = merged_core[
        (merged_core['start_date'] >= merged_core['added_date']) &
        (merged_core['start_date'] <= merged_core['removed_date'])
    ]
    
    # Criar lookup set para performance
    core_lookup = set(zip(valid_core['pool_address_normalized'], valid_core['start_date']))
    
    # Aplicar flag is_core_pool
    df_final['is_core_pool'] = df_final.apply(
        lambda x: 1 if (x['pool_address_normalized'], x['start_date']) in core_lookup else 0,
        axis=1
    )
    
    print(f"  ✓ Core pools mapeados: {df_final['is_core_pool'].sum()}")
    print(f"  ✓ Total de registros: {len(df_final)}")
    
    # Remover coluna auxiliar
    df_final = df_final.drop(columns=['pool_address_normalized'])
    
    return df_final

def merge_final(df_gauge_pool, df_financial):
    """
    Etapa 6: Refazer o merge final
    Unir dados de gauge (votos/emissões) com dados financeiros de pool
    Mantém dados agregados por round (não expande para dias)
    """
    print("\n🔗 ETAPA 6: Fazendo merge final gauge + pool...")
    
    # Filtrar apenas registros com pool_address válido
    df_gauge_pool_valid = df_gauge_pool[df_gauge_pool['pool_address'].notna()].copy()
    
    if len(df_gauge_pool_valid) == 0:
        print("  ⚠️ Nenhum registro com pool_address válido!")
        return df_gauge_pool
    
    # Calcular duração do round
    df_gauge_pool_valid['duration_days'] = (
        (df_gauge_pool_valid['end_date'] - df_gauge_pool_valid['start_date']).dt.days
    ).clip(lower=1)
    
    # Agregar dados financeiros por round (média ou soma, dependendo da métrica)
    # Usar a data de início do round para fazer o merge
    df_gauge_pool_valid['block_date'] = df_gauge_pool_valid['start_date']
    
    # Garantir que os endereços estão normalizados antes do merge
    df_gauge_pool_valid['pool_address_norm'] = df_gauge_pool_valid['pool_address'].apply(normalize_address)
    df_financial['pool_address_norm'] = df_financial['pool_address'].apply(normalize_address)
    
    # Agregar dados financeiros por pool e round (soma para fees, média para TVL)
    # Primeiro, expandir rounds para pegar todos os dias do período
    round_financial_rows = []
    for _, row in df_gauge_pool_valid.iterrows():
        if pd.isna(row['start_date']) or pd.isna(row['end_date']):
            continue
        
        try:
            start_date = pd.to_datetime(row['start_date']).tz_localize(None) if pd.notna(row['start_date']) else None
            end_date = pd.to_datetime(row['end_date']).tz_localize(None) if pd.notna(row['end_date']) else None
            
            if start_date is None or end_date is None:
                continue
                
            # Filtrar dados financeiros do período do round
            pool_financial = df_financial[
                (df_financial['pool_address_norm'] == row['pool_address_norm']) &
                (df_financial['blockchain'] == row['blockchain']) &
                (df_financial['block_date'] >= start_date) &
                (df_financial['block_date'] < end_date)
            ]
            
            if len(pool_financial) > 0:
                # Agregar dados financeiros do período
                financial_agg = {
                    'tvl_usd': pool_financial['tvl_usd'].mean() if 'tvl_usd' in pool_financial.columns else 0,
                    'swap_amount_usd': pool_financial['swap_amount_usd'].sum() if 'swap_amount_usd' in pool_financial.columns else 0,
                    'protocol_fee_amount_usd': pool_financial['protocol_fee_amount_usd'].sum() if 'protocol_fee_amount_usd' in pool_financial.columns else 0,
                    'swap_fee_usd': pool_financial['swap_fee_usd'].sum() if 'swap_fee_usd' in pool_financial.columns else 0,
                    'yield_fee_usd': pool_financial['yield_fee_usd'].sum() if 'yield_fee_usd' in pool_financial.columns else 0,
                    'pool_symbol': pool_financial['pool_symbol'].iloc[0] if 'pool_symbol' in pool_financial.columns and len(pool_financial) > 0 else '',
                    'pool_type': pool_financial['pool_type'].iloc[0] if 'pool_type' in pool_financial.columns and len(pool_financial) > 0 else '',
                }
            else:
                financial_agg = {
                    'tvl_usd': 0,
                    'swap_amount_usd': 0,
                    'protocol_fee_amount_usd': 0,
                    'swap_fee_usd': 0,
                    'yield_fee_usd': 0,
                    'pool_symbol': '',
                    'pool_type': '',
                }
            
            # Adicionar dados agregados ao round
            round_financial_rows.append({
                'round_id': row['round_id'],
                'gauge_address': row['gauge_address'],
                'pool_address': row['pool_address'],
                'blockchain': row['blockchain'],
                **financial_agg
            })
        except Exception as e:
            continue
    
    df_round_financial = pd.DataFrame(round_financial_rows)
    
    if len(df_round_financial) > 0:
        # Merge com dados de gauge
        df_final = df_gauge_pool_valid.merge(
            df_round_financial,
            on=['round_id', 'gauge_address', 'pool_address', 'blockchain'],
            how='left',
            suffixes=('', '_agg')
        )
        
        # Preencher valores nulos
        financial_cols = [
            'tvl_usd', 'swap_amount_usd', 'protocol_fee_amount_usd',
            'swap_fee_usd', 'yield_fee_usd', 'pool_symbol', 'pool_type'
        ]
        for col in financial_cols:
            if col in df_final.columns:
                if df_final[col].dtype in [np.float64, np.int64]:
                    df_final[col] = df_final[col].fillna(0)
                else:
                    df_final[col] = df_final[col].fillna('')
    else:
        df_final = df_gauge_pool_valid.copy()
        # Adicionar colunas financeiras vazias
        for col in ['tvl_usd', 'swap_amount_usd', 'protocol_fee_amount_usd', 'swap_fee_usd', 'yield_fee_usd', 'pool_symbol', 'pool_type']:
            if col not in df_final.columns:
                df_final[col] = 0 if col not in ['pool_symbol', 'pool_type'] else ''
    
    # Remover coluna auxiliar
    if 'pool_address_norm' in df_final.columns:
        df_final = df_final.drop(columns=['pool_address_norm'])
    if 'block_date' in df_final.columns:
        df_final = df_final.drop(columns=['block_date'])
    
    # Remover duplicatas - garantir uma linha por round por gauge por pool
    # Se houver duplicatas, manter a primeira (ou a que tem mais dados financeiros)
    before_dedup = len(df_final)
    
    # Ordenar para manter registros com mais dados financeiros primeiro
    if 'protocol_fee_amount_usd' in df_final.columns:
        df_final = df_final.sort_values('protocol_fee_amount_usd', ascending=False, na_position='last')
    
    # Remover duplicatas baseado nas chaves únicas
    key_cols = ['round_id', 'gauge_address', 'pool_address', 'blockchain']
    df_final = df_final.drop_duplicates(subset=key_cols, keep='first')
    
    after_dedup = len(df_final)
    if before_dedup != after_dedup:
        print(f"  ⚠️ Removidas {before_dedup - after_dedup} duplicatas")
    
    print(f"  ✓ Merge final concluído: {len(df_final)} registros (agregados por round)")
    print(f"  ✓ Registros com dados financeiros: {df_final['tvl_usd'].notna().sum() if 'tvl_usd' in df_final.columns else 0}")
    
    return df_final

def calculate_kpis(df_final):
    """
    Etapa 7: Calcular KPIs finais
    """
    print("\n📊 ETAPA 7: Calculando KPIs...")
    
    # Usar valores do round (não diários)
    if 'votes' in df_final.columns:
        df_final['votes_received'] = df_final['votes'].fillna(0)
    
    if 'round_emissions' in df_final.columns:
        df_final['bal_emited_votes'] = df_final['round_emissions'].fillna(0)
    
    # Calcular direct_incentives (emissões em USD do round)
    df_final['direct_incentives'] = df_final['round_emissions_usd'].fillna(0)
    
    # Calcular dao_profit_usd
    protocol_fee = df_final['protocol_fee_amount_usd'].fillna(0) if 'protocol_fee_amount_usd' in df_final.columns else 0
    df_final['dao_profit_usd'] = protocol_fee - df_final['direct_incentives']
    
    # Calcular emissions_roi
    df_final['emissions_roi'] = np.where(
        df_final['direct_incentives'] > 0,
        protocol_fee / df_final['direct_incentives'],
        0
    )
    
    print("  ✓ KPIs calculados")
    
    return df_final

def validate_data(df_final):
    """
    Etapa 8: Validar os resultados
    """
    print("\n✅ ETAPA 8: Validando dados...")
    
    # Validar votos por round somam 100%
    votes_by_round = df_final.groupby('round_id')['pct_votes'].sum()
    invalid_rounds = votes_by_round[abs(votes_by_round - 1.0) > 0.01]
    
    if len(invalid_rounds) > 0:
        print(f"  ⚠️ {len(invalid_rounds)} rounds com percentuais de votos != 100%")
        print(f"     Exemplos: {invalid_rounds.head().to_dict()}")
    else:
        print("  ✓ Votos por round somam 100%")
    
    # Validar emissões
    if 'round_emissions_usd' in df_final.columns:
        total_round_emissions = df_final['round_emissions_usd'].sum()
        print(f"  ✓ Total de emissões por round (USD): ${total_round_emissions:,.2f}")
    
    # Validar pools sem gauge
    pools_without_gauge = df_final[df_final['gauge_address'].isna()]
    print(f"  ✓ Pools sem gauge: {len(pools_without_gauge)}")
    
    # Validar gauges sem pool
    gauges_without_pool = df_final[df_final['pool_address'].isna()]
    print(f"  ✓ Gauges sem pool: {len(gauges_without_pool)}")
    
    return df_final

def main():
    """Função principal"""
    print("=" * 80)
    print("CRIAÇÃO DO ARQUIVO FINAL: balancer_v2_data.csv")
    print("=" * 80)
    
    # Carregar dados
    df_votes, df_emissions, df_mapping, df_financial, df_core = load_data()
    
    # Processar dados de gauge
    df_gauge = process_gauge_data(df_votes, df_emissions)
    
    # Processar mapping
    df_mapping_v2 = process_mapping(df_mapping)
    
    # Merge gauge com pool
    df_gauge_pool = merge_gauge_with_pool(df_gauge, df_mapping_v2)
    
    # Processar dados financeiros
    df_financial_processed = process_financial_data(df_financial)
    
    # Merge final
    df_final = merge_final(df_gauge_pool, df_financial_processed)
    
    # Aplicar core pools
    df_final = apply_core_pool_mapping(df_final, df_core)
    
    # Calcular KPIs
    df_final = calculate_kpis(df_final)
    
    # Validar
    df_final = validate_data(df_final)
    
    # Selecionar colunas finais (removendo block_date pois não expandimos mais para dias)
    final_cols = [
        'round_id', 'start_date', 'end_date',
        'gauge_address', 'pool_address', 'blockchain',
        'pool_symbol', 'pool_type',
        'votes_received', 'pct_votes', 'symbol',
        'bal_emited_votes', 'round_emissions', 'round_emissions_usd',
        'direct_incentives', 'round_fees',
        'tvl_usd', 'swap_amount_usd', 'protocol_fee_amount_usd',
        'swap_fee_usd', 'yield_fee_usd',
        'dao_profit_usd', 'emissions_roi',
        'is_core_pool'
    ]
    
    # Manter apenas colunas que existem
    available_cols = [c for c in final_cols if c in df_final.columns]
    df_final = df_final[available_cols]
    
    # Salvar arquivo final
    output_file = os.path.join(OUTPUT_DIR, "balancer_v2_data.csv")
    df_final.to_csv(output_file, index=False)
    
    print("\n" + "=" * 80)
    print(f"✅ ARQUIVO FINAL CRIADO: {output_file}")
    print(f"   Total de registros: {len(df_final):,}")
    print(f"   Rounds únicos: {df_final['round_id'].nunique()}")
    print(f"   Gauges únicos: {df_final['gauge_address'].nunique()}")
    print(f"   Pools únicos: {df_final['pool_address'].nunique()}")
    print("=" * 80)

if __name__ == "__main__":
    main()
