"""
Script para comparar only_in_nans_por_contrato.csv com FSN_data.csv
e identificar pools diferentes entre eles
"""

import pandas as pd
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
    print("COMPARANDO only_in_nans_por_contrato.csv COM FSN_data.csv")
    print("=" * 80)
    
    # 1. Carregar arquivos
    print("\n📂 Carregando arquivos...")
    only_nans_file = os.path.join(DATA_DIR, "only_in_nans_por_contrato.csv")
    fsn_file = os.path.join(DATA_DIR, "FSN_data.csv")
    
    df_only_nans = pd.read_csv(only_nans_file)
    df_fsn = pd.read_csv(fsn_file)
    
    print(f"  ✓ only_in_nans_por_contrato.csv: {len(df_only_nans)} registros")
    print(f"  ✓ FSN_data.csv: {len(df_fsn)} registros")
    
    # 2. Normalizar endereços
    print("\n🔧 Normalizando endereços...")
    df_only_nans['project_contract_address_norm'] = df_only_nans['project_contract_address'].apply(normalize_address)
    
    # Normalizar poolId e poolId_v2 no FSN
    df_fsn['poolId_norm'] = df_fsn['poolId'].apply(normalize_address)
    df_fsn['poolId_v2_norm'] = df_fsn['poolId_v2'].apply(normalize_address)
    df_fsn['gauge_address_norm'] = df_fsn['id'].apply(normalize_address)
    
    # 3. Criar conjunto de endereços únicos do only_nans
    only_nans_addresses = set(df_only_nans['project_contract_address_norm'].dropna())
    
    # 4. Criar conjunto de endereços do FSN (poolId, poolId_v2 e gauge_address)
    fsn_poolId_addresses = set(df_fsn['poolId_norm'].dropna())
    fsn_poolId_v2_addresses = set(df_fsn['poolId_v2_norm'].dropna())
    fsn_gauge_addresses = set(df_fsn['gauge_address_norm'].dropna())
    
    # Unir todos os endereços do FSN
    fsn_all_addresses = fsn_poolId_addresses | fsn_poolId_v2_addresses | fsn_gauge_addresses
    
    print(f"  ✓ Endereços únicos em only_in_nans_por_contrato.csv: {len(only_nans_addresses)}")
    print(f"  ✓ Endereços únicos em FSN_data.csv (poolId): {len(fsn_poolId_addresses)}")
    print(f"  ✓ Endereços únicos em FSN_data.csv (poolId_v2): {len(fsn_poolId_v2_addresses)}")
    print(f"  ✓ Endereços únicos em FSN_data.csv (gauge_address): {len(fsn_gauge_addresses)}")
    print(f"  ✓ Total de endereços únicos em FSN_data.csv: {len(fsn_all_addresses)}")
    
    # 5. Encontrar diferenças
    print("\n🔍 Analisando diferenças...")
    
    # Pools que estão em only_nans mas não em FSN
    only_in_nans_not_in_fsn = only_nans_addresses - fsn_all_addresses
    
    # Pools que estão em FSN mas não em only_nans
    only_in_fsn_not_in_nans = fsn_all_addresses - only_nans_addresses
    
    # Pools que estão em ambos
    in_both = only_nans_addresses & fsn_all_addresses
    
    print(f"  ✓ Pools em ambos arquivos: {len(in_both)}")
    print(f"  ⚠️ Pools apenas em only_in_nans_por_contrato.csv (não estão no FSN): {len(only_in_nans_not_in_fsn)}")
    print(f"  ⚠️ Pools no FSN mas não em only_in_nans_por_contrato.csv: {len(only_in_fsn_not_in_nans)}")
    
    # 6. Criar DataFrames com as diferenças
    print("\n💾 Criando arquivos com diferenças...")
    
    # 6.1. Pools em only_nans mas não no FSN
    if len(only_in_nans_not_in_fsn) > 0:
        df_not_in_fsn = df_only_nans[df_only_nans['project_contract_address_norm'].isin(only_in_nans_not_in_fsn)].copy()
        df_not_in_fsn = df_not_in_fsn[['project_contract_address', 'gauge_address']].drop_duplicates()
        
        not_in_fsn_file = os.path.join(OUTPUT_DIR, "only_nans_not_in_fsn.csv")
        df_not_in_fsn.to_csv(not_in_fsn_file, index=False)
        print(f"  📄 Arquivo criado: {not_in_fsn_file}")
        print(f"     Total de pools: {len(df_not_in_fsn)}")
    
    # 6.2. Pools em ambos (para referência)
    if len(in_both) > 0:
        df_both_nans = df_only_nans[df_only_nans['project_contract_address_norm'].isin(in_both)].copy()
        
        # Tentar encontrar correspondência no FSN
        def find_fsn_match(address_norm):
            # Buscar por poolId
            match_poolId = df_fsn[df_fsn['poolId_norm'] == address_norm]
            if len(match_poolId) > 0:
                return match_poolId.iloc[0]
            
            # Buscar por poolId_v2
            match_poolId_v2 = df_fsn[df_fsn['poolId_v2_norm'] == address_norm]
            if len(match_poolId_v2) > 0:
                return match_poolId_v2.iloc[0]
            
            # Buscar por gauge_address
            match_gauge = df_fsn[df_fsn['gauge_address_norm'] == address_norm]
            if len(match_gauge) > 0:
                return match_gauge.iloc[0]
            
            return None
        
        matches = []
        for _, row in df_both_nans.iterrows():
            address_norm = row['project_contract_address_norm']
            fsn_match = find_fsn_match(address_norm)
            
            if fsn_match is not None:
                matches.append({
                    'project_contract_address': row['project_contract_address'],
                    'gauge_address_nans': row['gauge_address'],
                    'gauge_address_fsn': fsn_match['id'],
                    'chain_fsn': fsn_match['chain'],
                    'status_fsn': fsn_match['status'],
                    'poolId_fsn': fsn_match['poolId'],
                    'poolId_v2_fsn': fsn_match['poolId_v2']
                })
        
        if len(matches) > 0:
            df_both_merged = pd.DataFrame(matches)
            both_file = os.path.join(OUTPUT_DIR, "only_nans_in_fsn.csv")
            df_both_merged.to_csv(both_file, index=False)
            print(f"  📄 Arquivo criado: {both_file}")
            print(f"     Total de pools: {len(df_both_merged)}")
    
    # 7. Análise detalhada: verificar se pools do only_nans são V2 ou V3
    print("\n🔍 Analisando se pools do only_nans são V2 ou V3...")
    
    # Verificar no FSN quais têm ambos poolId e poolId_v2 (V2) vs apenas poolId (V3)
    df_fsn_v2 = df_fsn[
        (df_fsn['poolId'].notna()) & 
        (df_fsn['poolId'].astype(str).str.strip() != '') &
        (df_fsn['poolId_v2'].notna()) & 
        (df_fsn['poolId_v2'].astype(str).str.strip() != '')
    ]
    
    df_fsn_v3 = df_fsn[
        (df_fsn['poolId'].notna()) & 
        (df_fsn['poolId'].astype(str).str.strip() != '') &
        ((df_fsn['poolId_v2'].isna()) | (df_fsn['poolId_v2'].astype(str).str.strip() == ''))
    ]
    
    print(f"  ✓ Pools V2 no FSN (ambos poolId e poolId_v2): {len(df_fsn_v2)}")
    print(f"  ✓ Pools V3 no FSN (apenas poolId, sem poolId_v2): {len(df_fsn_v3)}")
    
    # Verificar matches do only_nans
    if len(in_both) > 0:
        df_both_nans = df_only_nans[df_only_nans['project_contract_address_norm'].isin(in_both)].copy()
        
        v2_matches = 0
        v3_matches = 0
        unknown_matches = 0
        
        for _, row in df_both_nans.iterrows():
            address_norm = row['project_contract_address_norm']
            
            # Verificar se está em V2
            match_v2 = df_fsn_v2[
                (df_fsn_v2['poolId_norm'] == address_norm) | 
                (df_fsn_v2['poolId_v2_norm'] == address_norm) |
                (df_fsn_v2['gauge_address_norm'] == address_norm)
            ]
            
            if len(match_v2) > 0:
                v2_matches += 1
            else:
                # Verificar se está em V3
                match_v3 = df_fsn_v3[
                    (df_fsn_v3['poolId_norm'] == address_norm) |
                    (df_fsn_v3['gauge_address_norm'] == address_norm)
                ]
                
                if len(match_v3) > 0:
                    v3_matches += 1
                else:
                    unknown_matches += 1
        
        print(f"\n  📊 Pools do only_nans que estão no FSN:")
        print(f"     V2 (ambos poolId e poolId_v2): {v2_matches}")
        print(f"     V3 (apenas poolId): {v3_matches}")
        print(f"     Desconhecido: {unknown_matches}")
    
    # 8. Resumo final
    print("\n" + "=" * 80)
    print("📊 RESUMO DA COMPARAÇÃO")
    print("=" * 80)
    print(f"Total de pools em only_in_nans_por_contrato.csv: {len(only_nans_addresses)}")
    print(f"Total de endereços únicos em FSN_data.csv: {len(fsn_all_addresses)}")
    print(f"Pools em ambos: {len(in_both)}")
    print(f"Pools apenas em only_in_nans_por_contrato.csv (não estão no FSN): {len(only_in_nans_not_in_fsn)}")
    print(f"Pools no FSN mas não em only_in_nans_por_contrato.csv: {len(only_in_fsn_not_in_nans)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
