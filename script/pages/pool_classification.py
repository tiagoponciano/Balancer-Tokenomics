import streamlit as st
import utils
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Pool Classification", layout="wide", page_icon="🏷️")

# Check authentication
if not utils.check_authentication():
    st.stop()

utils.inject_css()

# Script para aplicar IDs específicos aos botões
import streamlit.components.v1 as components

components.html("""
<script>
console.log('[Button IDs] Script carregado via components.html (pool_classification.py)!');

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

if 'selected_pools_class' not in st.session_state:
    st.session_state.selected_pools_class = []
if 'pool_filter_mode_class' not in st.session_state:
    st.session_state.pool_filter_mode_class = 'top20'

col_btn1, col_btn2 = st.sidebar.columns(2)

with col_btn1:
    if st.button("Top 20", key="btn_top20_class"):
        old_mode = st.session_state.pool_filter_mode_class
        st.session_state.pool_filter_mode_class = 'top20'
        # Clear selections when mode changes
        if old_mode != 'top20':
            st.session_state.selected_pools_class = []
        st.rerun()

with col_btn2:
    if st.button("Worst 20", key="btn_worst20_class"):
        old_mode = st.session_state.pool_filter_mode_class
        st.session_state.pool_filter_mode_class = 'worst20'
        # Clear selections when mode changes
        if old_mode != 'worst20':
            st.session_state.selected_pools_class = []
        st.rerun()

if st.session_state.pool_filter_mode_class == 'worst20':
    filter_pools = sorted([str(p) for p in utils.get_worst_pools(df, n=20)])
    filter_label = "Select from Worst 20 Pools"
else:
    filter_pools = sorted([str(p) for p in utils.get_top_pools(df, n=20)])
    filter_label = "Select from Top 20 Pools"

# Clear invalid selections when filter mode changes
valid_sel = [p for p in st.session_state.selected_pools_class if p in filter_pools]
if len(valid_sel) != len(st.session_state.selected_pools_class):
    st.session_state.selected_pools_class = valid_sel

# Initialize default selection from session state if valid
default_selection = []
if st.session_state.selected_pools_class:
    # Only use session state if all selections are valid for current filter
    if all(p in filter_pools for p in st.session_state.selected_pools_class):
        default_selection = st.session_state.selected_pools_class

if st.sidebar.button("Select All", key="btn_select_all_class"):
    st.session_state.selected_pools_class = filter_pools.copy()
    default_selection = filter_pools.copy()
    st.rerun()

# Use dynamic key based on filter mode to force update when mode changes
multiselect_key = f"multiselect_pools_class_{st.session_state.pool_filter_mode_class}"

selected_pools = st.sidebar.multiselect(
    filter_label,
    options=filter_pools,
    default=default_selection,
    help="Select specific pools to view individual analysis",
    key=multiselect_key
)

# Always sync session state with current selection
st.session_state.selected_pools_class = list(selected_pools) if selected_pools else []

filter_by_pools = len(selected_pools) > 0

if filter_by_pools:
    df_display = df_sim[df_sim['pool_symbol'].isin(selected_pools)].copy()
    st.info(f"📊 Showing analysis for {len(selected_pools)} selected pool(s)")
else:
    df_display = df_sim.copy()

# Page Header with logout button
col_title, col_logout = st.columns([1, 0.1])
with col_title:
    st.markdown('<div class="page-title">Pool Classification Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Legitimate vs Mercenary pools classification and historical BAL distribution</div>', unsafe_allow_html=True)
with col_logout:
    utils.show_logout_button()

st.markdown("---")

if 'pool_category' not in df_display.columns:
    st.error("Pool classification not found.")
    st.stop()

category_stats = df_display.groupby('pool_category').agg({
    'pool_symbol': 'nunique',
    'protocol_fee_amount_usd': 'sum',
    'direct_incentives': 'sum',
    'dao_profit_usd': 'sum',
    'bal_emited_votes': 'sum'
}).round(2)

category_stats.columns = ['Pool Count', 'Total Revenue', 'Total Incentives', 'Total DAO Profit', 'Total BAL Emitted']

total_incentives = category_stats['Total Incentives'].sum()
total_bal = category_stats['Total BAL Emitted'].sum()

if total_incentives > 0:
    category_stats['% of Total Incentives'] = (category_stats['Total Incentives'] / total_incentives * 100).round(2)
if total_bal > 0:
    category_stats['% of Total BAL'] = (category_stats['Total BAL Emitted'] / total_bal * 100).round(2)

st.markdown("### 📊 Classification Summary")

col1, col2, col3 = st.columns(3)

with col1:
    legit_count = category_stats.loc['Legitimate', 'Pool Count'] if 'Legitimate' in category_stats.index else 0
    st.metric("Legitimate Pools", f"{legit_count:.0f}")

with col2:
    merc_count = category_stats.loc['Mercenary', 'Pool Count'] if 'Mercenary' in category_stats.index else 0
    st.metric("Mercenary Pools", f"{merc_count:.0f}")

with col3:
    undef_count = category_stats.loc['Undefined', 'Pool Count'] if 'Undefined' in category_stats.index else 0
    st.metric("Undefined Pools", f"{undef_count:.0f}")

st.markdown("---")

# Format monetary columns for display
category_stats_display = category_stats.copy()
for col in ['Total Revenue', 'Total Incentives', 'Total DAO Profit']:
    if col in category_stats_display.columns:
        category_stats_display[col] = category_stats_display[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")

# Format percentage columns
for col in ['% of Total Incentives', '% of Total BAL']:
    if col in category_stats_display.columns:
        category_stats_display[col] = category_stats_display[col].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "0.00%")

st.dataframe(category_stats_display, use_container_width=True, hide_index=False)

st.markdown("---")

st.markdown("### 📈 Historical Distribution by Category")

df_monthly = df_display.groupby([df_display['block_date'].dt.to_period('M'), 'pool_category']).agg({
    'direct_incentives': 'sum',
    'dao_profit_usd': 'sum'
}).reset_index()

df_monthly['block_date'] = df_monthly['block_date'].astype(str)

pivot_incentives = df_monthly.pivot(index='block_date', columns='pool_category', values='direct_incentives').fillna(0)
pivot_profit = df_monthly.pivot(index='block_date', columns='pool_category', values='dao_profit_usd').fillna(0)

pivot_incentives.index = pd.to_datetime(pivot_incentives.index)
pivot_profit.index = pd.to_datetime(pivot_profit.index)

colors = {'Legitimate': '#2ecc71', 'Mercenary': '#e74c3c', 'Undefined': '#95a5a6'}

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("**Monthly Incentives Distribution**")
    
    fig1 = go.Figure()
    
    for category in pivot_incentives.columns:
        fig1.add_trace(go.Scatter(
            x=pivot_incentives.index,
            y=pivot_incentives[category],
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
    
    st.plotly_chart(fig1, use_container_width=True, key="monthly_incentives")

with col_chart2:
    st.markdown("**Monthly DAO Profit by Category**")
    
    fig2 = go.Figure()
    
    for category in pivot_profit.columns:
        fig2.add_trace(go.Scatter(
            x=pivot_profit.index,
            y=pivot_profit[category],
            mode='lines',
            name=category,
            line=dict(color=colors.get(category, '#3498db'), width=1.5)
        ))
    
    fig2.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)", line_width=1)
    
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
    
    st.plotly_chart(fig2, use_container_width=True, key="monthly_profit")

if filter_by_pools:
    st.markdown("---")
    st.markdown("### 📋 Selected Pools by Category")
    
    for idx, pool in enumerate(selected_pools):
        pool_data = df_display[df_display['pool_symbol'] == pool]
        if len(pool_data) > 0:
            category = pool_data['pool_category'].iloc[0]
            total_profit = pool_data['dao_profit_usd'].sum()
            total_rev = pool_data['protocol_fee_amount_usd'].sum()
            total_inc = pool_data['direct_incentives'].sum()
            
            with st.expander(f"{pool} ({category})"):
                col_p1, col_p2, col_p3 = st.columns(3)
                col_p1.metric("Total Revenue", f"${total_rev:,.0f}")
                col_p2.metric("Total Incentives", f"${total_inc:,.0f}")
                col_p3.metric("DAO Profit", f"${total_profit:,.0f}")
                
                pool_daily = pool_data.groupby('block_date').agg({
                    'protocol_fee_amount_usd': 'sum',
                    'direct_incentives': 'sum',
                    'dao_profit_usd': 'sum'
                }).reset_index()
                
                fig_pool = go.Figure()
                fig_pool.add_trace(go.Scatter(
                    x=pool_daily['block_date'],
                    y=pool_daily['protocol_fee_amount_usd'],
                    mode='lines',
                    name='Revenue',
                    line=dict(color='#67A2E1', width=1.5)
                ))
                fig_pool.add_trace(go.Scatter(
                    x=pool_daily['block_date'],
                    y=pool_daily['dao_profit_usd'],
                    mode='lines',
                    name='DAO Profit',
                    line=dict(color='#2ecc71', width=1.5)
                ))
                
                fig_pool.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=300,
                    margin=dict(l=40, r=20, t=20, b=40),
                    xaxis=dict(
                        showgrid=False,
                        showline=True,
                        linecolor='rgba(255,255,255,0.1)',
                        title="",
                        tickfont=dict(size=10, color='#8B95A6')
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(255,255,255,0.05)',
                        showline=False,
                        title="",
                        tickfont=dict(size=10, color='#8B95A6')
                    ),
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=1.05,
                        xanchor="left",
                        x=0,
                        font=dict(size=10, color='#8B95A6')
                    )
                )
                
                st.plotly_chart(fig_pool, use_container_width=True, key=f"pool_class_{idx}_{hash(pool)}")
