"""
Script para criar CSVs agregados de votos para as top 20 e worst 20 pools.
Baseado em dao_profit_usd do dataset principal, faz match com votos via gauge_address.
"""

import pandas as pd
import numpy as np
import os
import re

def normalize_gauge_addr(addr):
    """Normalize gauge address for matching"""
    if pd.isna(addr):
        return ""
    addr_str = str(addr).lower().strip()
    if addr_str.startswith('0x'):
        return addr_str
    return addr_str

def clean_symbol(symbol):
    """Extract pool name from HTML links in symbol column"""
    if pd.isna(symbol):
        return ""
    # Remove HTML tags and extract text
    text = re.sub(r'<[^>]+>', '', str(symbol))
    # Remove the ↗ emoji if present
    text = text.replace('↗', '').strip()
    return text

def main():
    print("=" * 80)
    print("Script para criar CSVs agregados de votos (Top 20 e Worst 20)")
    print("Baseado em dao_profit_usd do dataset principal")
    print("=" * 80)
    
    # Caminhos dos arquivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    
    main_data_file = os.path.join(data_dir, 'balancer_v2_financial_master_final.csv')
    votes_file = os.path.join(data_dir, 'veBAL_votes.csv')
    bribes_file = os.path.join(data_dir, 'Balancer_Bribes_Gauges_enriched.csv')
    output_top20 = os.path.join(data_dir, 'top20_pools_votes_aggregated.csv')
    output_worst20 = os.path.join(data_dir, 'worst20_pools_votes_aggregated.csv')
    
    # Verifica se os arquivos existem
    if not os.path.exists(main_data_file):
        print(f"❌ Erro: Arquivo não encontrado: {main_data_file}")
        return
    
    if not os.path.exists(votes_file):
        print(f"❌ Erro: Arquivo não encontrado: {votes_file}")
        return
    
    if not os.path.exists(bribes_file):
        print(f"❌ Erro: Arquivo não encontrado: {bribes_file}")
        return
    
    print(f"\n📂 Lendo dataset principal: {main_data_file}")
    try:
        df_main = pd.read_csv(main_data_file)
        print(f"✅ Dataset principal lido. Total de linhas: {len(df_main)}")
    except Exception as e:
        print(f"❌ Erro ao ler dataset principal: {e}")
        return
    
    # Verifica colunas necessárias
    if 'pool_symbol' not in df_main.columns or 'dao_profit_usd' not in df_main.columns:
        print(f"❌ Erro: Colunas necessárias não encontradas no dataset principal")
        print(f"   Colunas disponíveis: {df_main.columns.tolist()}")
        return
    
    # Identifica Top 20 e Worst 20 pools baseado em dao_profit_usd agregado
    print(f"\n🔄 Identificando Top 20 e Worst 20 pools baseado em dao_profit_usd...")
    
    # Agrega por pool_symbol e soma dao_profit_usd
    pool_agg = df_main.groupby('pool_symbol')['dao_profit_usd'].sum().reset_index()
    pool_agg = pool_agg.sort_values('dao_profit_usd', ascending=False)
    
    top20_pools = pool_agg.head(20)['pool_symbol'].tolist()
    worst20_pools = pool_agg.tail(20)['pool_symbol'].tolist()
    
    print(f"✅ Top 20 pools identificadas (dao_profit_usd total):")
    for i, (_, row) in enumerate(pool_agg.head(5).iterrows(), 1):
        print(f"   {i}. {row['pool_symbol']}: ${row['dao_profit_usd']:,.2f}")
    
    print(f"✅ Worst 20 pools identificadas (dao_profit_usd total):")
    for i, (_, row) in enumerate(pool_agg.tail(5).iterrows(), 1):
        print(f"   {i}. {row['pool_symbol']}: ${row['dao_profit_usd']:,.2f}")
    
    # Carrega dados de bribes para fazer match via gauge_address
    print(f"\n📂 Lendo dados de bribes para match: {bribes_file}")
    try:
        df_bribes = pd.read_csv(bribes_file)
        print(f"✅ Bribes lido. Total de linhas: {len(df_bribes)}")
    except Exception as e:
        print(f"❌ Erro ao ler bribes: {e}")
        return
    
    if 'gauge_address' not in df_bribes.columns:
        print(f"❌ Erro: Coluna 'gauge_address' não encontrada em bribes")
        return
    
    # Cria mapeamento: gauge_address -> pool_symbol (apenas para pools Top/Worst 20)
    print(f"\n🔄 Criando mapeamento gauge_address -> pool_symbol...")
    
    # Normaliza gauge addresses
    df_bribes['gauge_address_normalized'] = df_bribes['gauge_address'].apply(normalize_gauge_addr)
    
    # Cria mapeamento: para cada pool_symbol nas Top/Worst 20, pega todos os gauge_address relacionados
    gauge_to_pool = {}
    
    # Função para normalizar nomes de pools
    def normalize_pool_name(name):
        if pd.isna(name):
            return ""
        name_str = str(name).upper().strip()
        name_str = name_str.replace('(A)', '').replace('(B)', '').replace('(E)', '').replace('(AV)', '').replace('(O)', '')
        name_str = name_str.replace('POOL', '').replace('LP', '').replace('BPT', '').replace('BSP', '')
        name_str = name_str.replace('-', ' ').replace('_', ' ').replace('/', ' ').replace('%', '')
        name_str = ' '.join(name_str.split())
        return name_str
    
    # Cria mapeamento de nomes normalizados para pool_symbol
    pool_name_to_symbol = {}
    for pool_sym in top20_pools + worst20_pools:
        pool_name_to_symbol[normalize_pool_name(pool_sym)] = pool_sym
    
    # Estratégia 1: Match por pool_symbol direto no bribes
    if 'pool_symbol' in df_bribes.columns:
        for _, row in df_bribes.iterrows():
            pool_sym = str(row.get('pool_symbol', '')).strip()
            gauge = normalize_gauge_addr(row.get('gauge_address', ''))
            if pool_sym in top20_pools + worst20_pools and gauge:
                if gauge not in gauge_to_pool:
                    gauge_to_pool[gauge] = pool_sym
    
    # Estratégia 2: Match por pool_id (project_contract_address)
    # Cria mapeamento pool_id -> pool_symbol do dataset principal
    if 'project_contract_address' in df_main.columns:
        pool_id_to_symbol = {}
        for _, row in df_main.iterrows():
            pool_id = str(row.get('project_contract_address', '')).strip()
            pool_sym = str(row.get('pool_symbol', '')).strip()
            if pool_id and pool_sym and pool_sym in top20_pools + worst20_pools:
                pool_id_to_symbol[pool_id] = pool_sym
        
        # Tenta match por pool_id no bribes
        if 'pool_id' in df_bribes.columns:
            for _, row in df_bribes.iterrows():
                pool_id = str(row.get('pool_id', '')).strip()
                gauge = normalize_gauge_addr(row.get('gauge_address', ''))
                if pool_id in pool_id_to_symbol and gauge:
                    if gauge not in gauge_to_pool:
                        gauge_to_pool[gauge] = pool_id_to_symbol[pool_id]
    
    # Estratégia 3: Match por pool_title (normalizando)
    if 'pool_title' in df_bribes.columns:
        for _, row in df_bribes.iterrows():
            pool_title = str(row.get('pool_title', '')).strip()
            pool_title_norm = normalize_pool_name(pool_title)
            gauge = normalize_gauge_addr(row.get('gauge_address', ''))
            if pool_title_norm in pool_name_to_symbol and gauge:
                if gauge not in gauge_to_pool:
                    gauge_to_pool[gauge] = pool_name_to_symbol[pool_title_norm]
    
    # Estratégia 4: Match por pool_name (normalizando)
    if 'pool_name' in df_bribes.columns:
        for _, row in df_bribes.iterrows():
            pool_name = str(row.get('pool_name', '')).strip()
            pool_name_norm = normalize_pool_name(pool_name)
            gauge = normalize_gauge_addr(row.get('gauge_address', ''))
            if pool_name_norm in pool_name_to_symbol and gauge:
                if gauge not in gauge_to_pool:
                    gauge_to_pool[gauge] = pool_name_to_symbol[pool_name_norm]
    
    print(f"✅ Mapeamento criado: {len(gauge_to_pool)} gauges mapeados para pools Top/Worst 20")
    
    # Carrega dados de votos
    print(f"\n📂 Lendo dados de votos: {votes_file}")
    try:
        df_votes = pd.read_csv(votes_file)
        print(f"✅ Votos lido. Total de linhas: {len(df_votes)}")
    except Exception as e:
        print(f"❌ Erro ao ler votos: {e}")
        return
    
    # Verifica colunas necessárias
    required_cols = ['gauge', 'votes', 'pct_votes', 'symbol']
    missing_cols = [col for col in required_cols if col not in df_votes.columns]
    if missing_cols:
        print(f"❌ Erro: Colunas faltando em votos: {missing_cols}")
        return
    
    # Extrai gauge_address dos votos
    def extract_gauge_address(gauge_str):
        if pd.isna(gauge_str):
            return ""
        gauge_str = str(gauge_str)
        if gauge_str.startswith('0x'):
            return gauge_str.lower().strip()
        return gauge_str.lower().strip()
    
    df_votes['gauge_address'] = df_votes['gauge'].apply(extract_gauge_address)
    df_votes['gauge_address_normalized'] = df_votes['gauge_address'].apply(normalize_gauge_addr)
    df_votes['symbol_clean'] = df_votes['symbol'].apply(clean_symbol)
    
    # Adiciona pool_symbol aos votos baseado no mapeamento
    df_votes['pool_symbol'] = df_votes['gauge_address_normalized'].map(gauge_to_pool)
    
    # Filtra apenas votos que têm match com Top/Worst 20 pools
    df_votes_matched = df_votes[df_votes['pool_symbol'].notna()].copy()
    print(f"✅ Votos com match: {len(df_votes_matched)} de {len(df_votes)} ({len(df_votes_matched)/len(df_votes)*100:.1f}%)")
    
    # Agrega votos por pool_symbol para Top 20
    print(f"\n🔄 Agregando votos para Top 20 pools...")
    top20_votes = df_votes_matched[df_votes_matched['pool_symbol'].isin(top20_pools)].copy()
    
    if not top20_votes.empty:
        top20_agg = top20_votes.groupby('pool_symbol').agg({
            'votes': 'sum',
            'pct_votes': 'sum',
            'gauge_address': 'count',  # Conta quantos gauges
            'symbol_clean': 'first'  # Pega o primeiro nome como exemplo
        }).reset_index()
        top20_agg.columns = ['pool_symbol', 'total_votes', 'total_pct_votes', 'gauge_count', 'pool_name_example']
        
        # Adiciona informações do dataset principal
        agg_dict = {
            'dao_profit_usd': 'sum',
            'protocol_fee_amount_usd': 'sum',
            'direct_incentives': 'sum'
        }
        # Adiciona colunas opcionais se existirem
        if 'pool_title' in df_main.columns:
            agg_dict['pool_title'] = 'first'
        if 'pool_name' in df_main.columns:
            agg_dict['pool_name'] = 'first'
        
        top20_info = df_main[df_main['pool_symbol'].isin(top20_pools)].groupby('pool_symbol').agg(agg_dict).reset_index()
        
        top20_final = top20_agg.merge(top20_info, on='pool_symbol', how='left')
        top20_final = top20_final.sort_values('total_votes', ascending=False)
        top20_final['rank'] = range(1, len(top20_final) + 1)
        
        # Reordena colunas (apenas as que existem)
        cols_order = ['rank', 'pool_symbol', 'total_votes', 'total_pct_votes', 
                     'gauge_count', 'dao_profit_usd', 'protocol_fee_amount_usd', 'direct_incentives', 'pool_name_example']
        if 'pool_title' in top20_final.columns:
            cols_order.insert(2, 'pool_title')
        if 'pool_name' in top20_final.columns:
            cols_order.insert(3, 'pool_name')
        top20_final = top20_final[[col for col in cols_order if col in top20_final.columns]]
        
        print(f"✅ Top 20 agregado: {len(top20_final)} pools")
        print(f"   Total de votos: {top20_final['total_votes'].sum():,.0f}")
    else:
        print(f"⚠️ Nenhum voto encontrado para Top 20 pools")
        top20_final = pd.DataFrame()
    
    # Agrega votos por pool_symbol para Worst 20
    print(f"\n🔄 Agregando votos para Worst 20 pools...")
    worst20_votes = df_votes_matched[df_votes_matched['pool_symbol'].isin(worst20_pools)].copy()
    
    if not worst20_votes.empty:
        worst20_agg = worst20_votes.groupby('pool_symbol').agg({
            'votes': 'sum',
            'pct_votes': 'sum',
            'gauge_address': 'count',  # Conta quantos gauges
            'symbol_clean': 'first'  # Pega o primeiro nome como exemplo
        }).reset_index()
        worst20_agg.columns = ['pool_symbol', 'total_votes', 'total_pct_votes', 'gauge_count', 'pool_name_example']
        
        # Adiciona informações do dataset principal
        agg_dict = {
            'dao_profit_usd': 'sum',
            'protocol_fee_amount_usd': 'sum',
            'direct_incentives': 'sum'
        }
        # Adiciona colunas opcionais se existirem
        if 'pool_title' in df_main.columns:
            agg_dict['pool_title'] = 'first'
        if 'pool_name' in df_main.columns:
            agg_dict['pool_name'] = 'first'
        
        worst20_info = df_main[df_main['pool_symbol'].isin(worst20_pools)].groupby('pool_symbol').agg(agg_dict).reset_index()
        
        worst20_final = worst20_agg.merge(worst20_info, on='pool_symbol', how='left')
        worst20_final = worst20_final.sort_values('total_votes', ascending=True)  # Menor primeiro
        worst20_final['rank'] = range(1, len(worst20_final) + 1)
        
        # Reordena colunas (apenas as que existem)
        cols_order = ['rank', 'pool_symbol', 'total_votes', 'total_pct_votes', 
                     'gauge_count', 'dao_profit_usd', 'protocol_fee_amount_usd', 'direct_incentives', 'pool_name_example']
        if 'pool_title' in worst20_final.columns:
            cols_order.insert(2, 'pool_title')
        if 'pool_name' in worst20_final.columns:
            cols_order.insert(3, 'pool_name')
        worst20_final = worst20_final[[col for col in cols_order if col in worst20_final.columns]]
        
        print(f"✅ Worst 20 agregado: {len(worst20_final)} pools")
        print(f"   Total de votos: {worst20_final['total_votes'].sum():,.0f}")
    else:
        print(f"⚠️ Nenhum voto encontrado para Worst 20 pools")
        worst20_final = pd.DataFrame()
    
    # Salva os CSVs
    print(f"\n💾 Salvando CSVs...")
    try:
        if not top20_final.empty:
            top20_final.to_csv(output_top20, index=False)
            print(f"✅ Top 20 salvo em: {output_top20}")
            print(f"   - Linhas: {len(top20_final)}")
        else:
            print(f"⚠️ Top 20 está vazio, não foi salvo")
        
        if not worst20_final.empty:
            worst20_final.to_csv(output_worst20, index=False)
            print(f"✅ Worst 20 salvo em: {output_worst20}")
            print(f"   - Linhas: {len(worst20_final)}")
        else:
            print(f"⚠️ Worst 20 está vazio, não foi salvo")
    except Exception as e:
        print(f"❌ Erro ao salvar CSVs: {e}")
        return
    
    # Estatísticas finais
    print(f"\n📈 Estatísticas:")
    print(f"   - Total de pools no dataset principal: {df_main['pool_symbol'].nunique()}")
    print(f"   - Top 20 pools (dao_profit_usd): {len(top20_pools)}")
    print(f"   - Worst 20 pools (dao_profit_usd): {len(worst20_pools)}")
    print(f"   - Gauges mapeados: {len(gauge_to_pool)}")
    print(f"   - Votos com match: {len(df_votes_matched)} de {len(df_votes)}")
    
    if not top20_final.empty:
        print(f"   - Top 20 pools com votos: {len(top20_final)}")
        print(f"   - Total votos (Top 20): {top20_final['total_votes'].sum():,.0f}")
    
    if not worst20_final.empty:
        print(f"   - Worst 20 pools com votos: {len(worst20_final)}")
        print(f"   - Total votos (Worst 20): {worst20_final['total_votes'].sum():,.0f}")
    
    print(f"\n✅ Processo concluído com sucesso!")
    print("=" * 80)

if __name__ == "__main__":
    main()
