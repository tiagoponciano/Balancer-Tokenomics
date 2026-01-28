"""
Script para converter a coluna is_core de boolean para inteiro (1/0).
"""

import pandas as pd

def convert_is_core_to_int():
    """
    Converte a coluna is_core de boolean para inteiro.
    """
    print("=" * 60)
    print("🔄 Conversão: is_core de boolean para inteiro")
    print("=" * 60)
    
    input_file = 'data/balancer_v2_pre_final_merge.csv'
    output_file = 'data/balancer_v2_pre_final_merge.csv'
    
    print(f"\n📖 Lendo arquivo: {input_file}")
    df = pd.read_csv(input_file)
    
    print(f"✅ Arquivo lido: {len(df):,} linhas")
    
    # Verificar o tipo atual da coluna is_core
    print(f"\n📊 Tipo atual da coluna is_core: {df['is_core'].dtype}")
    print(f"   Valores únicos: {df['is_core'].unique()}")
    print(f"   Distribuição:")
    print(df['is_core'].value_counts())
    
    # Converter boolean para inteiro (True -> 1, False -> 0)
    print("\n🔄 Convertendo is_core de boolean para inteiro...")
    df['is_core'] = df['is_core'].astype(int)
    
    print(f"✅ Conversão concluída!")
    print(f"   Novo tipo: {df['is_core'].dtype}")
    print(f"   Valores únicos: {df['is_core'].unique()}")
    print(f"   Distribuição:")
    print(df['is_core'].value_counts())
    
    # Mostrar amostra
    print("\n📋 Amostra dos dados:")
    print(df[['pool_address', 'day', 'is_core']].head(10).to_string())
    
    # Salvar o arquivo
    print(f"\n💾 Salvando arquivo: {output_file}")
    df.to_csv(output_file, index=False)
    
    print(f"✅ Arquivo salvo com sucesso!")
    print(f"   Total de linhas: {len(df):,}")
    print(f"   Linhas com is_core = 1: {(df['is_core'] == 1).sum():,} ({100 * (df['is_core'] == 1).sum() / len(df):.2f}%)")
    print(f"   Linhas com is_core = 0: {(df['is_core'] == 0).sum():,} ({100 * (df['is_core'] == 0).sum() / len(df):.2f}%)")
    
    return df

if __name__ == "__main__":
    try:
        result_df = convert_is_core_to_int()
        print("\n" + "=" * 60)
        print("✅ Processo concluído com sucesso!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()
