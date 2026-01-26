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

df_sim = utils.run_simulation_sidebar(df)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Pool Selection")

if 'selected_pools_weekly' not in st.session_state:
    st.session_state.selected_pools_weekly = []
if 'pool_filter_mode_weekly' not in st.session_state:
    st.session_state.pool_filter_mode_weekly = 'top20'

col_btn1, col_btn2 = st.sidebar.columns(2)

with col_btn1:
    if st.button("Top 20", key="btn_top20_weekly"):
        old_mode = st.session_state.pool_filter_mode_weekly
        st.session_state.pool_filter_mode_weekly = 'top20'
        # Clear selections when mode changes
        if old_mode != 'top20':
            st.session_state.selected_pools_weekly = []
        st.rerun()

with col_btn2:
    if st.button("Worst 20", key="btn_worst20_weekly"):
        old_mode = st.session_state.pool_filter_mode_weekly
        st.session_state.pool_filter_mode_weekly = 'worst20'
        # Clear selections when mode changes
        if old_mode != 'worst20':
            st.session_state.selected_pools_weekly = []
        st.rerun()

if st.session_state.pool_filter_mode_weekly == 'worst20':
    filter_pools = sorted([str(p) for p in utils.get_worst_pools(df, n=20)])
    filter_label = "Select from Worst 20 Pools"
else:
    filter_pools = sorted([str(p) for p in utils.get_top_pools(df, n=20)])
    filter_label = "Select from Top 20 Pools"

# Clear invalid selections when filter mode changes
valid_sel = [p for p in st.session_state.selected_pools_weekly if p in filter_pools]
if len(valid_sel) != len(st.session_state.selected_pools_weekly):
    st.session_state.selected_pools_weekly = valid_sel

# Initialize default selection from session state if valid
default_selection = []
if st.session_state.selected_pools_weekly:
    # Only use session state if all selections are valid for current filter
    if all(p in filter_pools for p in st.session_state.selected_pools_weekly):
        default_selection = st.session_state.selected_pools_weekly

if st.sidebar.button("Select All", key="btn_select_all_weekly"):
    st.session_state.selected_pools_weekly = filter_pools.copy()
    default_selection = filter_pools.copy()
    st.rerun()

# Use dynamic key based on filter mode to force update when mode changes
multiselect_key = f"multiselect_pools_weekly_{st.session_state.pool_filter_mode_weekly}"

selected_pools = st.sidebar.multiselect(
    filter_label,
    options=filter_pools,
    default=default_selection,
    help="Select specific pools to view individual analysis",
    key=multiselect_key
)

# Always sync session state with current selection
st.session_state.selected_pools_weekly = list(selected_pools) if selected_pools else []

filter_by_pools = len(selected_pools) > 0

if filter_by_pools:
    df_display = df_sim[df_sim['pool_symbol'].isin(selected_pools)].copy()
    st.info(f"📊 Showing analysis for {len(selected_pools)} selected pool(s)")
else:
    df_display = df_sim.copy()

# Page Header with logout button
col_title, col_logout = st.columns([1, 0.1])
with col_title:
    st.markdown('<div class="page-title">Weekly Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Weekly aggregation of emissions, votes, and distribution patterns</div>', unsafe_allow_html=True)
with col_logout:
    utils.show_logout_button()

st.markdown("---")

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

if filter_by_pools:
    st.markdown("---")
    st.markdown("### 📋 Selected Pools Weekly Analysis")
    
    for idx, pool in enumerate(selected_pools):
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

st.markdown("---")

st.markdown("### 💡 Notes on Bribe Analysis")

st.info("""
**Bribe Data Structure (Placeholder)**

Bribe data collection is planned for future implementation. When available, this section will include:

- Correlation between bribes and voting patterns
- Analysis of pools receiving bribes vs strategic votes
- Impact of bribes on BAL distribution

**Data Sources to Consider:**
- Votium (votium.app)
- Hidden Hand (hiddenhand.finance)
- Direct on-chain bribe contracts
- Dune Analytics queries for bribe events
""")
