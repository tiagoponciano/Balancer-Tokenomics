import streamlit as st
import utils
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(page_title="Weekly Analysis", layout="wide", page_icon="📅")

# Check authentication
if not utils.check_authentication():
    st.stop()

utils.inject_css()

# Script para aplicar IDs específicos aos botões
import streamlit.components.v1 as components

components.html("""
<script>
console.log('[Button IDs] Script carregado via components.html (weekly_analysis.py)!');

function applyButtonIds() {
    const contexts = [
        { doc: document, name: 'document' },
        { doc: window.parent?.document, name: 'parent' },
        { doc: window.top?.document, name: 'top' }
    ];
    
    contexts.forEach(({ doc, name }) => {
        if (!doc) return;
        
        try {
            const buttons = doc.querySelectorAll('button[data-testid*="stBaseButton"], button');
            
            buttons.forEach((button) => {
                let text = '';
                try {
                    text = (button.textContent || button.innerText || '').trim();
                    if (!text || text.length === 0) {
                        const markdownEl = button.querySelector('[data-testid="stMarkdownContainer"]');
                        if (markdownEl) {
                            text = (markdownEl.textContent || markdownEl.innerText || '').trim();
                        }
                    }
                    if (!text || text.length === 0) {
                        const pEl = button.querySelector('p');
                        if (pEl) {
                            text = (pEl.textContent || pEl.innerText || '').trim();
                        }
                    }
                } catch(e) {}
                
                const textLower = text.toLowerCase();
                
                // Aplica IDs que começam com os prefixos corretos
                if (text === 'Top 20' || textLower === 'top 20') {
                    if (!button.id || !button.id.startsWith('btn_top20')) {
                        button.id = 'btn_top20';
                    }
                } else if (text === 'Worst 20' || textLower === 'worst 20') {
                    if (!button.id || !button.id.startsWith('btn_worst20')) {
                        button.id = 'btn_worst20';
                    }
                } else if (text === 'Select All' || textLower === 'select all') {
                    if (!button.id || !button.id.startsWith('btn_select_all')) {
                        button.id = 'btn_select_all';
                    }
                } else if (text.includes('Logout') || text.includes('🚪') || textLower.includes('logout')) {
                    if (!button.id || !button.id.startsWith('btn_logout')) {
                        button.id = 'btn_logout';
                    }
                }
            });
        } catch(e) {
            console.error(`[Button IDs] Erro no contexto ${name}:`, e);
        }
    });
}

// Executa imediatamente e após delays
applyButtonIds();
setTimeout(applyButtonIds, 100);
setTimeout(applyButtonIds, 500);
setTimeout(applyButtonIds, 1000);
setInterval(applyButtonIds, 2000);

// Observa mudanças no DOM
if (window.MutationObserver) {
    const observer = new MutationObserver(() => {
        setTimeout(applyButtonIds, 100);
    });
    
    if (document.body) {
        observer.observe(document.body, { childList: true, subtree: true });
    }
}
</script>
""", height=0)

df = utils.load_data()
if df.empty:
    st.error("❌ Unable to load data.")
    st.stop()

if 'selected_pools_weekly' not in st.session_state:
    st.session_state.selected_pools_weekly = []
if 'pool_filter_mode_weekly' not in st.session_state:
    st.session_state.pool_filter_mode_weekly = 'all'  # Default: show all pools

# Pool filters at the top of sidebar (FIRST - before any other sidebar content)
def clear_weekly_selections():
    """Clear selections when filter changes"""
    st.session_state.selected_pools_weekly = []

utils.show_pool_filters('pool_filter_mode_weekly', on_change_callback=clear_weekly_selections)

# Date filter: Year + Quarter
filter_year, filter_quarter = utils.show_date_filter_sidebar(df, key_prefix="date_filter_weekly")
df = utils.apply_date_filter(df, filter_year, filter_quarter)
if df.empty:
    st.warning("No data in selected period. Adjust Year/Quarter or select «All».")

df_sim = utils.run_simulation_sidebar(df)

# Page Header with logout button
col_title, col_logout = st.columns([1, 0.1])
with col_title:
    st.markdown('<div class="page-title">Weekly Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Weekly aggregation of emissions, votes, and distribution patterns</div>', unsafe_allow_html=True)
with col_logout:
    utils.show_logout_button()

st.markdown("---")

# Filter data based on mode
if st.session_state.pool_filter_mode_weekly == 'top20':
    # Get top 20 pools
    top_pools = utils.get_top_pools(df, n=20)
    top_pools_list = [str(p) for p in top_pools]
    df_display = df_sim[df_sim['pool_symbol'].isin(top_pools_list)].copy()
    # Clear selections when mode changes
    if st.session_state.selected_pools_weekly:
        st.session_state.selected_pools_weekly = []
elif st.session_state.pool_filter_mode_weekly == 'worst20':
    # Get worst 20 pools
    worst_pools = utils.get_worst_pools(df, n=20)
    worst_pools_list = [str(p) for p in worst_pools]
    df_display = df_sim[df_sim['pool_symbol'].isin(worst_pools_list)].copy()
    # Clear selections when mode changes
    if st.session_state.selected_pools_weekly:
        st.session_state.selected_pools_weekly = []
else:
    # 'all' mode - show everything
    df_display = df_sim.copy()

if 'pool_category' not in df_display.columns:
    df_display['pool_category'] = 'Undefined'
else:
    df_display['pool_category'] = df_display['pool_category'].fillna('Undefined').astype(str)
if 'direct_incentives' not in df_display.columns:
    df_display['direct_incentives'] = 0.0

df_display['week'] = df_display['block_date'].dt.to_period('W').dt.start_time

df_weekly = df_display.groupby(['week', 'pool_category']).agg({
    'bal_emited_votes': 'sum',
    'direct_incentives': 'sum',
    'votes_received': 'sum',
    'protocol_fee_amount_usd': 'sum',
    'dao_profit_usd': 'sum'
}).reset_index()

weekly_totals = df_weekly.groupby('week').agg({
    'bal_emited_votes': 'sum',
    'direct_incentives': 'sum'
}).reset_index()

df_weekly = df_weekly.merge(
    weekly_totals,
    on='week',
    suffixes=('', '_total')
)

df_weekly['pct_of_weekly_emissions'] = np.where(
    df_weekly['bal_emited_votes_total'] > 0,
    (df_weekly['bal_emited_votes'] / df_weekly['bal_emited_votes_total'] * 100).round(2),
    0
)

st.markdown("### 📊 Weekly Summary")

summary_stats = df_weekly.groupby('pool_category').agg({
    'bal_emited_votes': 'sum',
    'direct_incentives': 'sum',
    'week': 'nunique'
}).round(2)

summary_stats.columns = ['Total BAL Emitted', 'Total USD Value', 'Weeks Active']

# Format monetary column for display
summary_stats_display = summary_stats.copy()
if 'Total USD Value' in summary_stats_display.columns:
    summary_stats_display['Total USD Value'] = summary_stats_display['Total USD Value'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")

st.dataframe(summary_stats_display, use_container_width=True, hide_index=False)

st.markdown("---")

st.markdown("### 📈 Weekly Trends")

pivot_weekly = df_weekly.pivot(index='week', columns='pool_category', values='bal_emited_votes').fillna(0)
pivot_weekly_incentives = df_weekly.pivot(index='week', columns='pool_category', values='direct_incentives').fillna(0)

colors = {'Legitimate': '#2ecc71', 'Mercenary': '#e74c3c', 'Undefined': '#95a5a6'}

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("**Weekly BAL Emissions by Category**")
    
    fig1 = go.Figure()
    
    for category in pivot_weekly.columns:
        fig1.add_trace(go.Scatter(
            x=pivot_weekly.index,
            y=pivot_weekly[category],
            mode='lines',
            name=category,
            line=dict(color=colors.get(category, '#3498db'), width=1.5),
            stackgroup='one'
        ))
    
    fig1.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor='rgba(255,255,255,0.1)',
            title="",
            tickfont=dict(size=11, color='#8B95A6')
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            showline=False,
            title="",
            tickfont=dict(size=11, color='#8B95A6')
        ),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.05,
            xanchor="left",
            x=0,
            font=dict(size=11, color='#8B95A6')
        )
    )
    
    st.plotly_chart(fig1, use_container_width=True, key="weekly_bal_emissions")

with col_chart2:
    st.markdown("**Weekly Incentives Distribution (USD)**")
    
    fig2 = go.Figure()
    
    for category in pivot_weekly_incentives.columns:
        fig2.add_trace(go.Scatter(
            x=pivot_weekly_incentives.index,
            y=pivot_weekly_incentives[category],
            mode='lines',
            name=category,
            line=dict(color=colors.get(category, '#3498db'), width=1.5),
            stackgroup='one'
        ))
    
    fig2.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor='rgba(255,255,255,0.1)',
            title="",
            tickfont=dict(size=11, color='#8B95A6')
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            showline=False,
            title="",
            tickfont=dict(size=11, color='#8B95A6')
        ),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.05,
            xanchor="left",
            x=0,
            font=dict(size=11, color='#8B95A6')
        )
    )
    
    st.plotly_chart(fig2, use_container_width=True, key="weekly_incentives")

# Show individual pool analysis only when Top 20 or Worst 20 filter is active
if st.session_state.pool_filter_mode_weekly in ['top20', 'worst20']:
    filtered_pools = sorted(df_display['pool_symbol'].unique())
    
    if len(filtered_pools) > 0:
        st.markdown("---")
        st.markdown("### 📋 Pools Weekly Analysis")
        
        for idx, pool in enumerate(filtered_pools):
            pool_weekly = df_weekly[df_weekly['week'].isin(
                df_display[df_display['pool_symbol'] == pool]['week'].unique()
            )]
        
        if len(pool_weekly) > 0:
            with st.expander(f"{pool}"):
                pool_weekly_summary = pool_weekly.groupby('week').agg({
                    'bal_emited_votes': 'sum',
                    'direct_incentives': 'sum'
                }).reset_index()
                
                fig_pool = utils.create_minimalist_chart(
                    pool_weekly_summary['week'],
                    pool_weekly_summary['bal_emited_votes'],
                    'BAL Emitted',
                    '#67A2E1',
                    height=300
                )
                st.plotly_chart(fig_pool, use_container_width=True, key=f"weekly_pool_{idx}_{hash(pool)}")

st.markdown("---")

st.markdown("### 📋 Weekly Distribution Table")

display_columns = ['week', 'pool_category', 'bal_emited_votes', 'direct_incentives', 'pct_of_weekly_emissions']
df_display_table = df_weekly[display_columns].copy()
df_display_table.columns = ['Week', 'Category', 'BAL Emitted', 'Incentives (USD)', '% of Weekly Emissions']
df_display_table = df_display_table.sort_values(['Week', 'Category'])

# Format monetary and percentage columns
if 'Incentives (USD)' in df_display_table.columns:
    df_display_table['Incentives (USD)'] = df_display_table['Incentives (USD)'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
if '% of Weekly Emissions' in df_display_table.columns:
    df_display_table['% of Weekly Emissions'] = df_display_table['% of Weekly Emissions'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "0.00%")

st.dataframe(df_display_table, use_container_width=True, hide_index=True)
