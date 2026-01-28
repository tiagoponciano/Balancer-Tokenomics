"""
Script para remover duplicatas do arquivo final.
O problema ocorreu porque o classification_core_pools.csv tinha duplicatas,
que ao fazer merge criaram múltiplas linhas para o mesmo gauge_address + day.
"""

import pandas as pd

def remove_duplicates():
    """
    Remove duplicatas do arquivo final, mantendo apenas uma linha por gauge_address + day.
    """
    print("=" * 60)
    print("🔧 Remoção de Duplicatas")
    print("=" * 60)
    
    input_file = 'data/balancer_v2_pre_final_merge.csv'
    
    print(f"\n📖 Lendo arquivo: {input_file}")
    df = pd.read_csv(input_file)
    
    print(f"✅ Arquivo lido: {len(df):,} linhas")
    print(f"   Soma total_votes antes: {df['total_votes'].sum():,.2f}")
    
    # Verificar duplicatas
    duplicates = df.duplicated(subset=['gauge_address', 'day']).sum()
    print(f"\n🔍 Duplicatas encontradas: {duplicates:,}")
    
    if duplicates > 0:
        # Mostrar algumas duplicatas antes de remover
        dup_rows = df[df.duplicated(subset=['gauge_address', 'day'], keep=False)]
        print(f"   Total de linhas duplicadas: {len(dup_rows):,}")
        
        # Ver exemplos
        print("\n📋 Exemplos de duplicatas:")
        sample = dup_rows.groupby(['gauge_address', 'day']).size().head(5)
        print(sample)
        
        # Remover duplicatas, mantendo a primeira ocorrência
        print("\n🗑️  Removendo duplicatas...")
        df_clean = df.drop_duplicates(subset=['gauge_address', 'day'], keep='first')
        
        removed_count = len(df) - len(df_clean)
        print(f"   Linhas removidas: {removed_count:,}")
        print(f"   Linhas restantes: {len(df_clean):,}")
        print(f"   Soma total_votes depois: {df_clean['total_votes'].sum():,.2f}")
        
        # Verificar se ainda há duplicatas
        remaining_dups = df_clean.duplicated(subset=['gauge_address', 'day']).sum()
        print(f"   Duplicatas restantes: {remaining_dups:,}")
        
        # Salvar arquivo limpo
        output_file = 'data/balancer_v2_pre_final_merge.csv'
        print(f"\n💾 Salvando arquivo limpo: {output_file}")
        df_clean.to_csv(output_file, index=False)
        
        print(f"✅ Arquivo salvo com sucesso!")
        
        # Comparar com arquivo original de votos
        print("\n📊 Comparação com arquivo original:")
        df_original = pd.read_csv('data/votes_balancer_v2.csv')
        print(f"   votes_balancer_v2.csv: {len(df_original):,} linhas")
        print(f"   balancer_v2_pre_final_merge.csv: {len(df_clean):,} linhas")
        print(f"   Diferença: {len(df_clean) - len(df_original):,} linhas")
        print(f"\n   Soma total_votes:")
        print(f"     votes_balancer_v2.csv: {df_original['total_votes'].sum():,.2f}")
        print(f"     balancer_v2_pre_final_merge.csv: {df_clean['total_votes'].sum():,.2f}")
        print(f"     Diferença: {df_clean['total_votes'].sum() - df_original['total_votes'].sum():,.2f}")
        
        return df_clean
    else:
        print("\n✅ Nenhuma duplicata encontrada!")
        return df

if __name__ == "__main__":
    try:
        result_df = remove_duplicates()
        print("\n" + "=" * 60)
        print("✅ Processo concluído com sucesso!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()
