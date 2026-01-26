"""
Script para criar CSVs agregados de bribes para as top 20 e worst 20 pools.
Soma a coluna amount_usdc do arquivo Balancer_Bribes_Gauges_enriched.csv
para as pools identificadas nos arquivos balancer_v2_best_pools.csv e balancer_v2_worst_pools.csv.
"""

import pandas as pd
import numpy as np
import os

def normalize_pool_name(name):
    """Normaliza o nome da pool para facilitar o matching"""
    if pd.isna(name):
        return ""
    name_str = str(name).upper().strip()
    # Remove prefixos comuns
    name_str = name_str.replace('(A)', '').replace('(B)', '').replace('(E)', '').replace('(AV)', '').replace('(O)', '')
    name_str = name_str.replace('POOL', '').replace('LP', '').replace('BPT', '').replace('BSP', '')
    # Normaliza separadores
    name_str = name_str.replace('-', ' ').replace('_', ' ').replace('/', ' ').replace('%', '')
    # Remove espaços extras e números de porcentagem
    name_str = ' '.join(name_str.split())
    # Remove números isolados (como "80 20" de "80/20")
    words = name_str.split()
    filtered_words = [w for w in words if not (w.isdigit() and len(w) <= 2)]
    name_str = ' '.join(filtered_words)
    return name_str

def extract_key_tokens(name):
    """Extrai tokens-chave do nome da pool para matching mais flexível"""
    if pd.isna(name):
        return set()
    name_str = str(name).upper().strip()
    # Remove caracteres especiais
    name_str = name_str.replace('-', ' ').replace('_', ' ').replace('/', ' ').replace('%', '').replace('(', '').replace(')', '')
    # Remove palavras comuns
    stop_words = {'POOL', 'LP', 'BPT', 'BSP', 'WETH', 'ETH', 'WA', 'BAS', 'ARB', 'OPT', 'AVA'}
    tokens = set(name_str.split())
    tokens = tokens - stop_words
    # Remove números pequenos (percentuais)
    tokens = {t for t in tokens if not (t.isdigit() and len(t) <= 2)}
    return tokens

def match_pools_by_id(bribes_df, pools_info_dict, match_col='pool_title'):
    """
    Faz match entre pools usando pool_id como chave primária.
    pools_info_dict: dict com {pool_id: pool_symbol}
    """
    matched_data = []
    
    if 'pool_id' not in bribes_df.columns:
        return pd.DataFrame()
    
    # Debug: verifica formatos de pool_id
    sample_bribe_ids = bribes_df['pool_id'].dropna().astype(str).str.strip().unique()[:3]
    sample_pool_ids = list(pools_info_dict.keys())[:3]
    print(f"    DEBUG: Formato de pool_id no bribes (exemplos): {[str(id)[:50] + '...' if len(str(id)) > 50 else str(id) for id in sample_bribe_ids]}")
    print(f"    DEBUG: Formato de pool_id nas pools (exemplos): {[str(id)[:50] + '...' if len(str(id)) > 50 else str(id) for id in sample_pool_ids]}")
    
    match_count = 0
    for idx, row in bribes_df.iterrows():
        pool_id = str(row['pool_id']).strip() if pd.notna(row['pool_id']) else ""
        if pool_id and pool_id in pools_info_dict:
            matched_pool = pools_info_dict[pool_id]
            matched_data.append({
                'pool_symbol': matched_pool,
                'pool_title': str(row[match_col]) if pd.notna(row[match_col]) else "",
                'amount_usdc': row['amount_usdc'],
                'gauge_address': row.get('gauge_address', ''),
                'blockchain': row.get('blockchain', ''),
                'pool_id': pool_id,
                'pool_name': row.get('pool_name', ''),
            })
            match_count += 1
    
    print(f"    DEBUG: Total de matches por pool_id: {match_count}")
    return pd.DataFrame(matched_data)

def match_pools_by_name(bribes_df, pool_symbols, match_col='pool_title'):
    """
    Faz match entre pools usando nome como fallback.
    pool_symbols: lista de pool_symbols para fazer match
    """
    matched_data = []
    pool_symbols_normalized = {normalize_pool_name(p): p for p in pool_symbols}
    # Cria também um dict de tokens para matching mais flexível
    pool_symbols_tokens = {p: extract_key_tokens(p) for p in pool_symbols}
    matched_indices = set()  # Para evitar duplicatas
    
    for idx, row in bribes_df.iterrows():
        pool_name = str(row[match_col]) if pd.notna(row[match_col]) else ""
        pool_name_normalized = normalize_pool_name(pool_name)
        pool_name_tokens = extract_key_tokens(pool_name)
        
        # Tenta match por nome normalizado
        matched_pool = None
        
        # 1. Match exato normalizado
        for norm_name, original_pool in pool_symbols_normalized.items():
            if norm_name and pool_name_normalized and norm_name == pool_name_normalized:
                matched_pool = original_pool
                break
        
        # 2. Match por tokens (pelo menos 2 tokens em comum)
        if not matched_pool and pool_name_tokens:
            best_match = None
            best_score = 0
            for pool_symbol, tokens in pool_symbols_tokens.items():
                if tokens:
                    common_tokens = pool_name_tokens.intersection(tokens)
                    if len(common_tokens) >= 2:  # Pelo menos 2 tokens em comum
                        score = len(common_tokens) / max(len(tokens), len(pool_name_tokens))
                        if score > best_score:
                            best_score = score
                            best_match = pool_symbol
            if best_match:
                matched_pool = best_match
        
        # 3. Match parcial (um contém o outro) - mais flexível
        if not matched_pool:
            for norm_name, original_pool in pool_symbols_normalized.items():
                if norm_name and pool_name_normalized:
                    # Remove espaços para matching mais flexível
                    norm_clean = norm_name.replace(' ', '')
                    name_clean = pool_name_normalized.replace(' ', '')
                    if norm_clean in name_clean or name_clean in norm_clean:
                        if len(norm_clean) > 4 and len(name_clean) > 4:  # Evita matches muito genéricos
                            matched_pool = original_pool
                            break
        
        # 4. Match direto (case-insensitive) - último recurso
        if not matched_pool:
            pool_name_upper = str(row[match_col]).upper().strip() if pd.notna(row[match_col]) else ""
            for pool_symbol in pool_symbols:
                pool_symbol_upper = str(pool_symbol).upper().strip()
                if pool_symbol_upper == pool_name_upper:
                    matched_pool = pool_symbol
                    break
                # Match parcial direto
                if len(pool_symbol_upper) > 4 and len(pool_name_upper) > 4:
                    if pool_symbol_upper in pool_name_upper or pool_name_upper in pool_symbol_upper:
                        matched_pool = pool_symbol
                        break
        
        if matched_pool and idx not in matched_indices:
            matched_indices.add(idx)
            matched_data.append({
                'pool_symbol': matched_pool,
                'pool_title': pool_name,
                'amount_usdc': row['amount_usdc'],
                'gauge_address': row.get('gauge_address', ''),
                'blockchain': row.get('blockchain', ''),
                'pool_id': str(row.get('pool_id', '')).strip() if pd.notna(row.get('pool_id')) else '',
                'pool_name': row.get('pool_name', ''),
            })
    
    return pd.DataFrame(matched_data)

def aggregate_bribes_by_pool(bribes_matched_df):
    """Agrega os bribes por pool, somando amount_usdc"""
    if bribes_matched_df.empty:
        return pd.DataFrame()
    
    agg_dict = {
        'amount_usdc': 'sum',
        'gauge_address': 'first',  # Pega o primeiro (assumindo que é o mesmo para a mesma pool)
        'blockchain': 'first',
        'pool_id': 'first',
        'pool_title': 'first',
        'pool_name': 'first',
    }
    
    aggregated = bribes_matched_df.groupby('pool_symbol').agg(agg_dict).reset_index()
    aggregated = aggregated.sort_values('amount_usdc', ascending=False)
    
    return aggregated

def process_pools(pools_file, bribes_file, output_file, pool_type='top'):
    """
    Processa as pools e cria CSV agregado.
    
    Args:
        pools_file: Caminho para o arquivo CSV com as pools (best ou worst)
        bribes_file: Caminho para o arquivo CSV com os bribes
        output_file: Caminho para o arquivo CSV de saída
        pool_type: 'top' ou 'worst' para identificar o tipo (top = melhor dao_profit, worst = pior dao_profit)
    """
    print(f"\n{'='*60}")
    print(f"Processando {pool_type.upper()} 20 pools...")
    print(f"{'='*60}")
    
    # Carrega as pools
    print(f"Carregando pools de: {pools_file}")
    try:
        pools_df = pd.read_csv(pools_file)
        print(f"  ✓ Carregado: {len(pools_df)} linhas")
        print(f"  DEBUG: Colunas disponíveis no arquivo de pools: {pools_df.columns.tolist()}")
    except Exception as e:
        print(f"  ✗ Erro ao carregar {pools_file}: {e}")
        return
    
    # Pega as primeiras 20 pools únicas baseado na agregação de dao_profit_usd
    # IMPORTANTE: Agrupa por pool_symbol e SOMA dao_profit_usd antes de ordenar
    # Isso garante que pools repetidas (múltiplas linhas) sejam somadas corretamente
    if 'pool_symbol' in pools_df.columns:
        # Primeiro, mostra quantas linhas existem e quantas pools únicas
        total_rows = len(pools_df)
        unique_pool_count = pools_df['pool_symbol'].nunique()
        print(f"  DEBUG: Total de linhas: {total_rows}, Pools únicas: {unique_pool_count}")
        
        # Agrega por pool_symbol para garantir que pegamos as top/worst 20 baseado em dao_profit_usd TOTAL
        if 'dao_profit_usd' in pools_df.columns:
            print(f"  Agregando dao_profit_usd por pool_symbol (somando ocorrências repetidas)...")
            
            # Mostra exemplo de pool repetida antes da agregação
            if total_rows > unique_pool_count:
                example_pool = pools_df['pool_symbol'].value_counts().index[0]
                example_count = pools_df['pool_symbol'].value_counts().iloc[0]
                example_sum = pools_df[pools_df['pool_symbol'] == example_pool]['dao_profit_usd'].sum()
                print(f"  DEBUG: Exemplo - Pool '{example_pool}' aparece {example_count} vezes")
                print(f"  DEBUG: Soma total de dao_profit_usd para '{example_pool}': ${example_sum:,.2f}")
            
            pool_agg = pools_df.groupby('pool_symbol')['dao_profit_usd'].sum()
            print(f"  ✓ Agregado: {len(pool_agg)} pools únicas (soma de todas as ocorrências)")
            
            if pool_type == 'top':
                # Top = maior dao_profit (ascending=False)
                pool_agg_sorted = pool_agg.sort_values(ascending=False)
            else:
                # Worst = menor dao_profit (ascending=True)
                pool_agg_sorted = pool_agg.sort_values(ascending=True)
            
            # Pega as top 20 pools baseado na soma agregada
            unique_pools = pool_agg_sorted.head(20).index.tolist()
            print(f"  DEBUG: Top 5 pools por dao_profit_usd agregado ({pool_type}):")
            for i, (pool, value) in enumerate(pool_agg_sorted.head(5).items()):
                print(f"    {i+1}. {pool}: ${value:,.2f}")
        else:
            # Se não tiver dao_profit_usd, pega as primeiras 20 únicas
            unique_pools = pools_df['pool_symbol'].unique()[:20]
            print(f"  ⚠ Coluna 'dao_profit_usd' não encontrada, usando primeiras 20 únicas")
        
        print(f"  ✓ Selecionadas {len(unique_pools)} pools únicas ({pool_type} 20)")
        print(f"  Primeiras 5 pools selecionadas: {list(unique_pools[:5])}")
    else:
        print(f"  ✗ Coluna 'pool_symbol' não encontrada. Colunas disponíveis: {pools_df.columns.tolist()}")
        return
    
    # Carrega os bribes
    print(f"\nCarregando bribes de: {bribes_file}")
    try:
        bribes_df = pd.read_csv(bribes_file)
        print(f"  ✓ Carregado: {len(bribes_df)} linhas")
        print(f"  Colunas disponíveis: {bribes_df.columns.tolist()}")
    except Exception as e:
        print(f"  ✗ Erro ao carregar {bribes_file}: {e}")
        return
    
    # Verifica se a coluna amount_usdc existe
    if 'amount_usdc' not in bribes_df.columns:
        print(f"  ✗ Coluna 'amount_usdc' não encontrada no arquivo de bribes")
        return
    
    # Prepara dicts para matching por múltiplas chaves
    print(f"\nPreparando informações de pools para matching...")
    pools_info_dict = {}  # {pool_id: pool_symbol} - usando project_contract_address como pool_id
    pools_join_address_dict = {}  # {join_address: pool_symbol}
    
    # Verifica se as colunas existem (case-insensitive)
    pool_id_col = None
    pool_symbol_col = None
    join_address_col = None
    project_contract_address_col = None
    
    for col in pools_df.columns:
        if col.lower() == 'pool_id':
            pool_id_col = col
        if col.lower() == 'pool_symbol':
            pool_symbol_col = col
        if col.lower() == 'join_address':
            join_address_col = col
        if col.lower() == 'project_contract_address':
            project_contract_address_col = col
    
    if pool_symbol_col:
        print(f"  ✓ Encontrada coluna: {pool_symbol_col}")
        
        # Tenta usar project_contract_address como pool_id (parece ser o ID completo da pool)
        if project_contract_address_col:
            print(f"  ✓ Encontrada coluna: {project_contract_address_col} (usando como pool_id)")
            for _, row in pools_df.iterrows():
                pool_id = str(row[project_contract_address_col]).strip() if pd.notna(row[project_contract_address_col]) else ""
                pool_symbol = str(row[pool_symbol_col]).strip() if pd.notna(row[pool_symbol_col]) else ""
                if pool_id and pool_symbol and pool_symbol in unique_pools:
                    pools_info_dict[pool_id] = pool_symbol
            print(f"  ✓ Criado mapeamento pool_id (project_contract_address) para {len(pools_info_dict)} pools")
        
        # Também cria mapeamento por join_address
        if join_address_col:
            print(f"  ✓ Encontrada coluna: {join_address_col}")
            for _, row in pools_df.iterrows():
                join_addr = str(row[join_address_col]).strip() if pd.notna(row[join_address_col]) else ""
                pool_symbol = str(row[pool_symbol_col]).strip() if pd.notna(row[pool_symbol_col]) else ""
                if join_addr and pool_symbol and pool_symbol in unique_pools:
                    pools_join_address_dict[join_addr.lower()] = pool_symbol  # Normaliza para lowercase
            print(f"  ✓ Criado mapeamento join_address para {len(pools_join_address_dict)} pools")
        
        if len(pools_info_dict) < len(unique_pools) and len(pools_join_address_dict) < len(unique_pools):
            missing = [p for p in unique_pools if p not in pools_info_dict.values() and p not in pools_join_address_dict.values()]
            if missing:
                print(f"  ⚠ Pools sem endereço/ID mapeado (primeiras 5): {missing[:5]}")
    else:
        print(f"  ⚠ Coluna pool_symbol não encontrada")
        print(f"  DEBUG: Procurando colunas similares...")
        similar_cols = [col for col in pools_df.columns if 'pool' in col.lower() or 'id' in col.lower()]
        print(f"  DEBUG: Colunas similares encontradas: {similar_cols}")
    
    # Tenta fazer match usando pool_id primeiro (mais confiável), depois por nome
    print(f"\nFazendo match entre pools e bribes...")
    matched_df = None
    matched_pool_ids = set()  # Para rastrear quais pools já foram matchadas
    
    # Debug: mostra alguns pool_ids do arquivo de bribes
    if 'pool_id' in bribes_df.columns:
        unique_bribe_ids = set(bribes_df['pool_id'].dropna().astype(str).str.strip())
        sample_bribe_ids = list(unique_bribe_ids)[:5]
        print(f"  DEBUG: Total de pool_ids únicos no arquivo de bribes: {len(unique_bribe_ids)}")
        print(f"  DEBUG: Exemplos de pool_id no arquivo de bribes: {sample_bribe_ids}")
    
    # Debug: mostra alguns pool_ids das pools que estamos procurando
    if pools_info_dict:
        unique_pool_ids = set(pools_info_dict.keys())
        sample_pool_ids = list(unique_pool_ids)[:5]
        print(f"  DEBUG: Total de pool_ids únicos das pools procuradas: {len(unique_pool_ids)}")
        print(f"  DEBUG: Exemplos de pool_id das pools procuradas: {sample_pool_ids}")
        
        # Verifica se há pool_ids em comum
        if 'pool_id' in bribes_df.columns:
            common_ids = unique_pool_ids.intersection(unique_bribe_ids)
            print(f"  DEBUG: Pool_ids em comum entre os dois arquivos: {len(common_ids)}")
            if len(common_ids) > 0:
                print(f"  DEBUG: Primeiros 5 pool_ids em comum: {list(common_ids)[:5]}")
                # Mostra quais pools correspondem a esses IDs
                for pid in list(common_ids)[:3]:
                    pool_symbol = pools_info_dict.get(pid, 'N/A')
                    print(f"    - pool_id {pid[:30]}... -> pool_symbol: {pool_symbol}")
    
    # Primeiro tenta match por pool_id (project_contract_address)
    if pools_info_dict and 'pool_id' in bribes_df.columns:
        print(f"  Tentando match por pool_id (project_contract_address)...")
        matched_df = match_pools_by_id(bribes_df, pools_info_dict, 'pool_title')
        if not matched_df.empty:
            matched_pool_ids = set(matched_df['pool_id'].unique())
            matched_pools_by_id = matched_df['pool_symbol'].unique()
            print(f"  ✓ Encontrados {len(matched_df)} registros de bribes correspondentes por pool_id")
            print(f"  ✓ Matchadas {len(matched_pools_by_id)} pools únicas por pool_id: {list(matched_pools_by_id)}")
        else:
            print(f"  ⚠ Nenhum match por pool_id encontrado")
            print(f"  DEBUG: Verificando se há pool_ids em comum...")
            if pools_info_dict:
                bribe_ids = set(bribes_df['pool_id'].dropna().astype(str).str.strip())
                pool_ids = set(pools_info_dict.keys())
                common = bribe_ids.intersection(pool_ids)
                print(f"  DEBUG: {len(common)} pool_ids em comum entre os dois arquivos")
                if len(common) > 0:
                    print(f"  DEBUG: Primeiros 5 pool_ids em comum: {list(common)[:5]}")
    
    # Tenta match por derived_pool_address (bribes) vs join_address (pools)
    if pools_join_address_dict and 'derived_pool_address' in bribes_df.columns:
        print(f"  Tentando match por derived_pool_address (bribes) vs join_address (pools)...")
        matched_by_address = []
        for idx, row in bribes_df.iterrows():
            derived_addr = str(row['derived_pool_address']).strip().lower() if pd.notna(row['derived_pool_address']) else ""
            if derived_addr and derived_addr in pools_join_address_dict:
                matched_pool = pools_join_address_dict[derived_addr]
                # Só adiciona se ainda não foi matchada por pool_id
                if matched_df.empty or matched_pool not in matched_df['pool_symbol'].values:
                    matched_by_address.append({
                        'pool_symbol': matched_pool,
                        'pool_title': str(row['pool_title']) if pd.notna(row['pool_title']) else "",
                        'amount_usdc': row['amount_usdc'],
                        'gauge_address': row.get('gauge_address', ''),
                        'blockchain': row.get('blockchain', ''),
                        'pool_id': str(row.get('pool_id', '')).strip() if pd.notna(row.get('pool_id')) else '',
                        'pool_name': row.get('pool_name', ''),
                    })
        
        if matched_by_address:
            matched_by_address_df = pd.DataFrame(matched_by_address)
            if matched_df.empty:
                matched_df = matched_by_address_df
            else:
                matched_df = pd.concat([matched_df, matched_by_address_df], ignore_index=True)
            matched_pools_by_addr = matched_by_address_df['pool_symbol'].unique()
            print(f"  ✓ Encontrados {len(matched_by_address_df)} registros adicionais por derived_pool_address")
            print(f"  ✓ Matchadas {len(matched_pools_by_addr)} pools adicionais: {list(matched_pools_by_addr)}")
        else:
            print(f"  ⚠ Nenhum match por derived_pool_address encontrado")
    
    # Se ainda faltam pools, tenta match por nome (apenas para pools não matchadas)
    if matched_df is None or matched_df.empty:
        matched_df = pd.DataFrame()
    
    remaining_pools = [p for p in unique_pools if p not in (matched_df['pool_symbol'].unique() if not matched_df.empty else [])]
    
    if remaining_pools:
        print(f"  Tentando match por nome para {len(remaining_pools)} pools restantes...")
        print(f"  DEBUG: Pools restantes (primeiras 10): {remaining_pools[:10]}")
        
        # Debug: mostra alguns nomes do arquivo de bribes
        if 'pool_title' in bribes_df.columns:
            sample_titles = bribes_df['pool_title'].dropna().unique()[:10]
            print(f"  DEBUG: Exemplos de pool_title no arquivo de bribes: {list(sample_titles)}")
        
        for match_col in ['pool_title', 'pool_name']:
            if match_col in bribes_df.columns:
                print(f"    Tentando match usando coluna: {match_col}")
                # Filtra apenas registros que ainda não foram matchados por pool_id
                if not matched_df.empty and 'pool_id' in matched_df.columns:
                    unmatched_bribes = bribes_df[~bribes_df['pool_id'].isin(matched_pool_ids)]
                else:
                    unmatched_bribes = bribes_df
                
                print(f"    DEBUG: {len(unmatched_bribes)} registros de bribes disponíveis para match por nome")
                temp_matched = match_pools_by_name(unmatched_bribes, remaining_pools, match_col)
                if not temp_matched.empty:
                    matched_pools_by_name = temp_matched['pool_symbol'].unique()
                    print(f"    ✓ Encontrados {len(temp_matched)} registros adicionais por {match_col}")
                    print(f"    ✓ Pools matchadas por {match_col}: {list(matched_pools_by_name)}")
                    if matched_df.empty:
                        matched_df = temp_matched
                    else:
                        matched_df = pd.concat([matched_df, temp_matched], ignore_index=True)
                else:
                    print(f"    ⚠ Nenhum match encontrado por {match_col}")
                    # Debug: mostra tentativas de match para algumas pools
                    print(f"    DEBUG: Tentando match manual para primeiras 3 pools...")
                    for pool in remaining_pools[:3]:
                        pool_upper = str(pool).upper()
                        matches = unmatched_bribes[unmatched_bribes[match_col].astype(str).str.upper().str.contains(pool_upper, na=False)]
                        if not matches.empty:
                            print(f"      - '{pool}' -> encontrou {len(matches)} matches: {matches[match_col].unique()[:3]}")
                        else:
                            print(f"      - '{pool}' -> nenhum match encontrado")
        
        if matched_df.empty:
            print(f"  ✗ Nenhum match encontrado")
            print(f"  Pools procuradas (primeiras 10): {list(unique_pools[:10])}")
            print(f"  Exemplos de pool_id no arquivo de bribes: {bribes_df['pool_id'].dropna().unique()[:10] if 'pool_id' in bribes_df.columns else 'N/A'}")
            print(f"  Exemplos de pools no arquivo de bribes: {bribes_df['pool_title'].unique()[:10] if 'pool_title' in bribes_df.columns else 'N/A'}")
            return
    
    if matched_df.empty:
        print(f"  ✗ Nenhum match encontrado")
        return
    
    # Debug: mostra quais pools das top 20 não foram encontradas
    matched_pool_symbols = set(matched_df['pool_symbol'].unique() if not matched_df.empty else [])
    unmatched_pools = [p for p in unique_pools if p not in matched_pool_symbols]
    
    if unmatched_pools:
        print(f"\n  ⚠ Pools das {pool_type} 20 que NÃO foram encontradas nos bribes ({len(unmatched_pools)} pools):")
        for i, pool in enumerate(unmatched_pools, 1):
            print(f"    {i}. {pool}")
        
        # Verifica se essas pools têm pool_id e se esse pool_id existe no arquivo de bribes
        print(f"\n  🔍 Analisando por que não foram encontradas...")
        if pools_info_dict:
            # Cria dict reverso: pool_symbol -> pool_id
            symbol_to_id = {v: k for k, v in pools_info_dict.items()}
            
            for pool in unmatched_pools[:10]:  # Analisa as primeiras 10
                pool_id = symbol_to_id.get(pool, None)
                if pool_id:
                    # Verifica se esse pool_id existe no arquivo de bribes
                    if 'pool_id' in bribes_df.columns:
                        exists_in_bribes = bribes_df['pool_id'].astype(str).str.strip().eq(str(pool_id).strip()).any()
                        if exists_in_bribes:
                            count = bribes_df['pool_id'].astype(str).str.strip().eq(str(pool_id).strip()).sum()
                            total_amount = bribes_df[bribes_df['pool_id'].astype(str).str.strip() == str(pool_id).strip()]['amount_usdc'].sum()
                            print(f"    '{pool}' -> pool_id EXISTE no arquivo de bribes! ({count} registros, ${total_amount:,.2f})")
                            print(f"      ⚠ PROBLEMA: O match por pool_id não funcionou!")
                        else:
                            print(f"    '{pool}' -> pool_id NÃO existe no arquivo de bribes (pool_id: {pool_id[:30]}...)")
                else:
                    print(f"    '{pool}' -> Não tem pool_id no arquivo de pools")
        
        # Tenta encontrar essas pools no arquivo de bribes usando busca mais ampla por nome
        print(f"\n  🔍 Tentando busca mais ampla por NOME para pools não encontradas...")
        for pool in unmatched_pools[:5]:  # Testa apenas as primeiras 5 para não sobrecarregar
            pool_upper = str(pool).upper()
            # Remove caracteres especiais para busca mais flexível
            pool_clean = pool_upper.replace('/', ' ').replace('-', ' ').replace('_', ' ')
            pool_tokens = set([t for t in pool_clean.split() if len(t) > 2])
            
            # Busca no pool_title
            if 'pool_title' in bribes_df.columns:
                matches_title = []
                for idx, row in bribes_df.iterrows():
                    title = str(row['pool_title']).upper() if pd.notna(row['pool_title']) else ""
                    title_tokens = set([t for t in title.replace('-', ' ').replace('/', ' ').replace('%', '').replace('(', '').replace(')', '').split() if len(t) > 2])
                    common = pool_tokens.intersection(title_tokens)
                    if len(common) >= 2:  # Pelo menos 2 tokens em comum
                        matches_title.append((row['pool_title'], row.get('pool_id', ''), row['amount_usdc']))
                
                if matches_title:
                    print(f"    '{pool}' -> Encontrou {len(matches_title)} possíveis matches em pool_title:")
                    for title, pid, amount in matches_title[:3]:
                        print(f"      - '{title}' (pool_id: {pid[:30] if pid else 'N/A'}..., amount: ${amount:,.2f})")
                else:
                    print(f"    '{pool}' -> Nenhum match encontrado mesmo com busca ampla por nome")
                    print(f"      Tokens procurados: {pool_tokens}")
    
    # Agrega por pool
    print(f"\nAgregando bribes por pool...")
    if matched_df.empty:
        print(f"  ✗ Nenhum dado para agregar")
        return
    
    print(f"  DEBUG: Total de registros antes da agregação: {len(matched_df)}")
    print(f"  DEBUG: Pools únicas encontradas: {matched_df['pool_symbol'].unique()}")
    print(f"  DEBUG: Contagem por pool:")
    for pool in matched_df['pool_symbol'].unique():
        count = len(matched_df[matched_df['pool_symbol'] == pool])
        total_amount = matched_df[matched_df['pool_symbol'] == pool]['amount_usdc'].sum()
        print(f"    - {pool}: {count} registros, ${total_amount:,.2f}")
    
    aggregated_df = aggregate_bribes_by_pool(matched_df)
    
    if aggregated_df.empty:
        print(f"  ✗ Nenhum dado agregado")
        return
    
    print(f"  ✓ Agregado: {len(aggregated_df)} pools")
    print(f"  Total amount_usdc: ${aggregated_df['amount_usdc'].sum():,.2f}")
    print(f"  DEBUG: Pools agregadas: {list(aggregated_df['pool_symbol'].values)}")
    
    # Adiciona informações adicionais das pools originais se disponível
    if 'pool_symbol' in pools_df.columns:
        pools_info = pools_df.groupby('pool_symbol').agg({
            'dao_profit_usd': 'sum',
            'protocol_fee_amount_usd': 'sum',
            'direct_incentives': 'sum',
            'tvl_usd': 'mean',  # Média do TVL
        }).reset_index()
        
        aggregated_df = aggregated_df.merge(pools_info, on='pool_symbol', how='left')
    
    # Salva o CSV
    print(f"\nSalvando resultado em: {output_file}")
    try:
        aggregated_df.to_csv(output_file, index=False)
        print(f"  ✓ CSV criado com sucesso!")
        print(f"  Total de linhas: {len(aggregated_df)}")
        print(f"\nPrimeiras 5 linhas:")
        print(aggregated_df.head().to_string())
    except Exception as e:
        print(f"  ✗ Erro ao salvar CSV: {e}")

def main():
    """Função principal"""
    # Define os caminhos dos arquivos
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    
    best_pools_file = os.path.join(data_dir, 'balancer_v2_best_pools.csv')
    worst_pools_file = os.path.join(data_dir, 'balancer_v2_worst_pools.csv')
    bribes_file = os.path.join(data_dir, 'Balancer_Bribes_Gauges_enriched.csv')
    
    top20_output = os.path.join(data_dir, 'top20_pools_bribes_aggregated.csv')
    worst20_output = os.path.join(data_dir, 'worst20_pools_bribes_aggregated.csv')
    
    # Verifica se os arquivos existem
    for file_path, name in [(best_pools_file, 'best_pools'), 
                            (worst_pools_file, 'worst_pools'),
                            (bribes_file, 'bribes')]:
        if not os.path.exists(file_path):
            print(f"✗ Arquivo não encontrado: {file_path}")
            return
        else:
            print(f"✓ Arquivo encontrado: {name}")
    
    # Processa top 20
    process_pools(best_pools_file, bribes_file, top20_output, 'top')
    
    # Processa worst 20
    process_pools(worst_pools_file, bribes_file, worst20_output, 'worst')
    
    print(f"\n{'='*60}")
    print("Processamento concluído!")
    print(f"{'='*60}")
    print(f"\nArquivos criados:")
    print(f"  - {top20_output}")
    print(f"  - {worst20_output}")

if __name__ == "__main__":
    main()
