import pandas as pd

# Top 20
print('='*60)
print('TOP 20 POOLS (melhores por dao_profit_usd agregado):')
print('='*60)
df_best = pd.read_csv('data/balancer_v2_best_pools.csv')
pool_agg_best = df_best.groupby('pool_symbol')['dao_profit_usd'].sum().sort_values(ascending=False)
top20 = pool_agg_best.head(20)
for i, (pool, value) in enumerate(top20.items(), 1):
    print(f'{i:2d}. {pool:40s} -> ${value:,.2f}')

print('\n' + '='*60)
print('WORST 20 POOLS (piores por dao_profit_usd agregado):')
print('='*60)
df_worst = pd.read_csv('data/balancer_v2_worst_pools.csv')
pool_agg_worst = df_worst.groupby('pool_symbol')['dao_profit_usd'].sum().sort_values(ascending=True)
worst20 = pool_agg_worst.head(20)
for i, (pool, value) in enumerate(worst20.items(), 1):
    print(f'{i:2d}. {pool:40s} -> ${value:,.2f}')
