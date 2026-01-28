"""
Script para adicionar gauge_address ao veBAL_pre_merge.csv
Cruzando com FSN_data.csv para vincular project_contract_address com gauge_address
Apenas pools V2 são consideradas (onde AMBOS poolId e poolId_v2 estão preenchidos)
"""

import pandas as pd
import numpy as np
import os

DATA_DIR = "data"
OUTPUT_DIR = "data"

def normalize_address(addr):
    """Normaliza endereços para comparação (lowercase, sem espaços)"""
    if pd.isna(addr) or addr == '':
        return None
    addr_str = str(addr).strip()
    # Se o endereço tem mais de 42 caracteres, pegar apenas os primeiros 42 chars
    if len(addr_str) > 42:
        addr_str = addr_str[:42]
    return addr_str.lower()

def main():
    print("=" * 80)
    print("ADICIONANDO GAUGE_ADDRESS AO veBAL_pre_merge.csv")
    print("=" * 80)
    
    # 1. Carregar arquivos
    print("\n📂 Carregando arquivos...")
    vebal_file = os.path.join(DATA_DIR, "veBAL_pre_merge.csv")
    fsn_file = os.path.join(DATA_DIR, "FSN_data.csv")
    
    df_vebal = pd.read_csv(vebal_file)
    df_fsn = pd.read_csv(fsn_file)
    
    print(f"  ✓ veBAL_pre_merge.csv: {len(df_vebal)} registros")
    print(f"  ✓ FSN_data.csv: {len(df_fsn)} registros")
    
    # 2. Criar mapeamento pool_address -> gauge_address usando FSN_data.csv
    print("\n🔧 Criando mapeamento pool_address -> gauge_address via FSN_data...")
    
    # Normalizar endereços no FSN
    df_fsn['gauge_address_norm'] = df_fsn['id'].apply(normalize_address)
    df_fsn['poolId_norm'] = df_fsn['poolId'].apply(normalize_address)
    df_fsn['poolId_v2_norm'] = df_fsn['poolId_v2'].apply(normalize_address)
    
    # Criar mapeamento: pool_address -> gauge_address
    # IMPORTANTE: Só mapear pools V2 (onde AMBOS poolId e poolId_v2 estão preenchidos)
    pool_to_gauge_dict = {}
    
    skipped_pools = 0
    
    # Validar e filtrar apenas pools V2 (ambos campos preenchidos)
    for idx, row in df_fsn.iterrows():
        poolId = row['poolId']
        poolId_v2 = row['poolId_v2']
        gauge_address = row['id']  # formato original
        
        # Verificar se ambos estão preenchidos (garante que é pool V2)
        poolId_str = str(poolId) if pd.notna(poolId) else ''
        poolId_v2_str = str(poolId_v2) if pd.notna(poolId_v2) else ''
        
        poolId_valid = poolId_str.strip() != '' and poolId_str.strip().lower() != 'nan'
        poolId_v2_valid = poolId_v2_str.strip() != '' and poolId_v2_str.strip().lower() != 'nan'
        
        # Só processar se AMBOS estiverem preenchidos (pools V2)
        if not (poolId_valid and poolId_v2_valid):
            skipped_pools += 1
            continue
        
        # Mapear usando poolId_v2 primeiro (primeiros 42 caracteres)
        if pd.notna(row['poolId_v2_norm']) and pd.notna(row['gauge_address_norm']):
            key = (row['poolId_v2_norm'], row['chain'])
            pool_to_gauge_dict[key] = gauge_address  # manter formato original
        
        # Mapear usando poolId completo (se não estiver já mapeado)
        key = (row['poolId_norm'], row['chain'])
        if key not in pool_to_gauge_dict and pd.notna(row['poolId_norm']) and pd.notna(row['gauge_address_norm']):
            pool_to_gauge_dict[key] = gauge_address  # manter formato original
    
    print(f"  ✓ Pools V2 válidas (ambos poolId e poolId_v2): {len(pool_to_gauge_dict)}")
    print(f"  ⚠️ Pools ignoradas (sem poolId_v2 ou poolId): {skipped_pools}")
    
    # 3. Adicionar gauge_address ao veBAL_pre_merge
    print("\n🔗 Adicionando gauge_address ao veBAL_pre_merge...")
    
    # Normalizar project_contract_address no veBAL
    df_vebal['project_contract_address_norm'] = df_vebal['project_contract_address'].apply(normalize_address)
    
    # Criar coluna gauge_address
    if 'gauge_address' not in df_vebal.columns:
        df_vebal['gauge_address'] = None
    
    # Mapear usando project_contract_address + blockchain
    def get_gauge_address(row):
        project_norm = row['project_contract_address_norm']
        blockchain = row['blockchain']
        
        if pd.notna(project_norm):
            # Tentar match direto
            key = (project_norm, blockchain)
            if key in pool_to_gauge_dict:
                return pool_to_gauge_dict[key]
        
        return None
    
    df_vebal['gauge_address'] = df_vebal.apply(get_gauge_address, axis=1)
    
    # Estatísticas
    total_records = len(df_vebal)
    records_with_gauge = df_vebal['gauge_address'].notna().sum()
    records_without_gauge = total_records - records_with_gauge
    
    print(f"  ✓ Total de registros: {total_records:,}")
    print(f"  ✓ Registros com gauge_address: {records_with_gauge:,} ({records_with_gauge/total_records*100:.1f}%)")
    print(f"  ⚠️ Registros sem gauge_address: {records_without_gauge:,} ({records_without_gauge/total_records*100:.1f}%)")
    
    # 4. Estatísticas por blockchain
    print("\n📊 Estatísticas por blockchain:")
    for blockchain in df_vebal['blockchain'].unique():
        df_chain = df_vebal[df_vebal['blockchain'] == blockchain]
        total_chain = len(df_chain)
        with_gauge_chain = df_chain['gauge_address'].notna().sum()
        pct = (with_gauge_chain / total_chain * 100) if total_chain > 0 else 0
        print(f"  {blockchain}: {with_gauge_chain:,}/{total_chain:,} ({pct:.1f}%)")
    
    # 5. Salvar arquivo atualizado
    print("\n💾 Salvando arquivo atualizado...")
    
    # IMPORTANTE: Manter TODOS os registros, mesmo os sem gauge_address
    # Apenas adicionar a coluna gauge_address (será None/NaN para registros sem match)
    output_file = os.path.join(OUTPUT_DIR, "veBAL_pre_merge_2.csv")
    df_vebal.to_csv(output_file, index=False)
    
    print("\n" + "=" * 80)
    print(f"✅ ARQUIVO ATUALIZADO: {output_file}")
    print(f"   Total de registros (TODOS mantidos): {len(df_vebal):,}")
    print(f"   Registros com gauge_address: {records_with_gauge:,}")
    print(f"   Registros sem gauge_address (mantidos com None): {records_without_gauge:,}")
    print("=" * 80)
    
    # 6. Criar arquivo com registros sem gauge_address (para análise)
    if records_without_gauge > 0:
        df_no_gauge = df_vebal[df_vebal['gauge_address'].isna()].copy()
        
        # Agregar por project_contract_address
        no_gauge_summary = df_no_gauge.groupby(['project_contract_address', 'blockchain', 'pool_symbol']).agg({
            'block_date': ['min', 'max', 'count'],
            'tvl_usd': 'sum'
        }).reset_index()
        
        # Flatten column names
        no_gauge_summary.columns = [
            'project_contract_address', 'blockchain', 'pool_symbol',
            'first_date', 'last_date', 'record_count', 'total_tvl_usd'
        ]
        
        no_gauge_file = os.path.join(OUTPUT_DIR, "veBAL_pre_merge_no_gauge.csv")
        no_gauge_summary.to_csv(no_gauge_file, index=False)
        print(f"\n📄 Arquivo com registros sem gauge_address salvo: {no_gauge_file}")
        print(f"   Total de pools únicas sem gauge: {len(no_gauge_summary)}")

if __name__ == "__main__":
    main()
