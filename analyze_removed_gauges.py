import pandas as pd
import numpy as np

# Ler os arquivos CSV
print("Lendo arquivos...")
fsn_data = pd.read_csv('./data/FSN_data.csv')
vebal_votes = pd.read_csv('./data/vebal_votes_valid.csv')
removed_gauges = pd.read_csv('./data/removed_gauge.csv')

print(f"\n=== ANÁLISE DE GAUGES REMOVIDOS ===\n")

# Verificar quantos gauges têm poolId_v2 vazio no FSN_data
fsn_data['poolId_v2'] = fsn_data['poolId_v2'].astype(str).str.strip()
non_v2_in_fsn = fsn_data[
    (fsn_data['poolId_v2'].isna()) | 
    (fsn_data['poolId_v2'] == '') | 
    (fsn_data['poolId_v2'] == 'nan')
]

print(f"Total de gauges no FSN_data.csv: {len(fsn_data)}")
print(f"Gauges com poolId_v2 vazio no FSN_data.csv: {len(non_v2_in_fsn)}")
print(f"Gauges removidos no removed_gauge.csv: {len(removed_gauges)}")

# Normalizar gauge_address para comparação
fsn_data['id_normalized'] = fsn_data['id'].astype(str).str.strip().str.lower()
non_v2_in_fsn['id_normalized'] = non_v2_in_fsn['id'].astype(str).str.strip().str.lower()
removed_gauges['gauge_address_normalized'] = removed_gauges['gauge_address'].astype(str).str.strip().str.lower()
vebal_votes['gauge_address_normalized'] = vebal_votes['gauge_address'].astype(str).str.strip().str.lower()

# Verificar quais gauges não-V2 do FSN estão nos votos
non_v2_gauges_in_fsn = set(non_v2_in_fsn['id_normalized'].unique())
all_gauges_in_votes = set(vebal_votes['gauge_address_normalized'].unique())
removed_gauges_set = set(removed_gauges['gauge_address_normalized'].unique())

print(f"\nGauges únicos nos votos: {len(all_gauges_in_votes)}")
print(f"Gauges não-V2 do FSN que estão nos votos: {len(non_v2_gauges_in_fsn & all_gauges_in_votes)}")

# Verificar quais gauges removidos estão no FSN mas não são V2
removed_that_are_in_fsn = removed_gauges_set & non_v2_gauges_in_fsn
print(f"Gauges removidos que estão no FSN (mas não são V2): {len(removed_that_are_in_fsn)}")

# Verificar quais gauges removidos NÃO estão no FSN (só estão nos votos)
removed_not_in_fsn = removed_gauges_set - set(fsn_data['id_normalized'].unique())
print(f"Gauges removidos que NÃO estão no FSN_data.csv: {len(removed_not_in_fsn)}")

# Criar DataFrame detalhado dos gauges removidos
removed_gauges_detailed = []

for gauge in removed_gauges['gauge_address'].values:
    gauge_norm = str(gauge).strip().lower()
    
    # Buscar informações do FSN_data
    fsn_match = fsn_data[fsn_data['id_normalized'] == gauge_norm]
    
    # Buscar informações dos votos
    votes_match = vebal_votes[vebal_votes['gauge_address_normalized'] == gauge_norm]
    
    info = {
        'gauge_address': gauge,
        'in_fsn_data': 'Sim' if len(fsn_match) > 0 else 'Não',
        'poolId': fsn_match['poolId'].values[0] if len(fsn_match) > 0 else '',
        'poolId_v2': fsn_match['poolId_v2'].values[0] if len(fsn_match) > 0 else '',
        'status': fsn_match['status'].values[0] if len(fsn_match) > 0 else '',
        'chain': fsn_match['chain'].values[0] if len(fsn_match) > 0 else '',
        'total_votes_in_data': len(votes_match),
        'total_votes_sum': votes_match['total_votes'].sum() if len(votes_match) > 0 else 0,
        'last_vote_date': votes_match['day'].max() if len(votes_match) > 0 else '',
    }
    
    removed_gauges_detailed.append(info)

removed_gauges_df = pd.DataFrame(removed_gauges_detailed)

# Salvar CSV detalhado
output_file = './data/removed_gauge_detailed.csv'
removed_gauges_df.to_csv(output_file, index=False)
print(f"\nCSV detalhado criado: {output_file}")

# Estatísticas
print("\n=== ESTATÍSTICAS DETALHADAS ===")
print(f"\nGauges removidos que estão no FSN_data.csv:")
print(f"  - Total: {len(removed_gauges_df[removed_gauges_df['in_fsn_data'] == 'Sim'])}")
print(f"  - Status KILLED: {len(removed_gauges_df[(removed_gauges_df['in_fsn_data'] == 'Sim') & (removed_gauges_df['status'] == 'KILLED')])}")
print(f"  - Status ACTIVE: {len(removed_gauges_df[(removed_gauges_df['in_fsn_data'] == 'Sim') & (removed_gauges_df['status'] == 'ACTIVE')])}")

print(f"\nGauges removidos que NÃO estão no FSN_data.csv:")
print(f"  - Total: {len(removed_gauges_df[removed_gauges_df['in_fsn_data'] == 'Não'])}")

print(f"\nTotal de votos dos gauges removidos: {removed_gauges_df['total_votes_sum'].sum():,.2f}")
print(f"Total de registros de votos dos gauges removidos: {removed_gauges_df['total_votes_in_data'].sum()}")

# Mostrar primeiras linhas
print("\n=== PRIMEIRAS 20 LINHAS DO CSV DETALHADO ===")
print(removed_gauges_df.head(20).to_string())
