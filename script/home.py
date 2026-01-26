import streamlit as st
import utils
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(
    page_title="Balancer Tokenomics Analysis",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check authentication
if not utils.check_authentication():
    st.stop()

utils.inject_css()

df = utils.load_data()
if df.empty:
    st.stop()

df_sim = utils.run_simulation_sidebar(df)

# Header with logout button
col_title, col_logout = st.columns([1, 0.1])
with col_title:
    st.markdown('<div class="page-title">Balancer Tokenomics Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Historical analysis with simulation controls</div>', unsafe_allow_html=True)
with col_logout:
    utils.show_logout_button()

st.markdown("---")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Pool Selection")

if 'selected_pools' not in st.session_state:
    st.session_state.selected_pools = []
if 'pool_filter_mode' not in st.session_state:
    st.session_state.pool_filter_mode = 'top20'

col_btn1, col_btn2 = st.sidebar.columns(2)

with col_btn1:
    if st.button("Top 20", key="btn_top20"):
        st.session_state.pool_filter_mode = 'top20'
        st.session_state.selected_pools = []

with col_btn2:
    if st.button("Worst 20", key="btn_worst20"):
        st.session_state.pool_filter_mode = 'worst20'
        st.session_state.selected_pools = []

if st.session_state.pool_filter_mode == 'worst20':
    filter_pools = sorted([str(p) for p in utils.get_worst_pools(df, n=20)])
    filter_label = "Select from Worst 20 Pools"
else:
    filter_pools = sorted([str(p) for p in utils.get_top_pools(df, n=20)])
    filter_label = "Select from Top 20 Pools"

# Clear invalid selections when filter mode changes
valid_sel = [p for p in st.session_state.selected_pools if p in filter_pools]
if len(valid_sel) != len(st.session_state.selected_pools):
    st.session_state.selected_pools = valid_sel

# Use session_state directly as default, but sync with filter_pools
if st.session_state.selected_pools and all(p in filter_pools for p in st.session_state.selected_pools):
    default_selection = st.session_state.selected_pools
else:
    default_selection = []

if st.sidebar.button("Select All", key="btn_select_all"):
    st.session_state.selected_pools = filter_pools.copy()
    st.rerun()

# Use dynamic key based on filter mode to force update
multiselect_key = f"multiselect_pools_home_{st.session_state.pool_filter_mode}"

selected_pools = st.sidebar.multiselect(
    filter_label,
    options=filter_pools,
    default=default_selection,
    help="Select specific pools to view individual analysis",
    key=multiselect_key
)

# Always update session state with current selection
st.session_state.selected_pools = selected_pools

filter_by_pools = len(selected_pools) > 0

if filter_by_pools:
    df_display = df_sim[df_sim['pool_symbol'].isin(selected_pools)].copy()
    st.info(f"📊 Showing analysis for {len(selected_pools)} selected pool(s)")
else:
    df_display = df_sim.copy()

total_revenue = df_display['sim_dao_revenue'].sum() + df_display['sim_holders_revenue'].sum() + df_display['sim_incentives_revenue'].sum()
total_dao = df_display['sim_dao_revenue'].sum()
total_holders = df_display['sim_holders_revenue'].sum()
total_incentives = df_display['sim_incentives_revenue'].sum()
total_bal_emitted = df_display['sim_bal_emitted'].sum()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("DAO Revenue", f"${total_dao:,.0f}", help="Total revenue for DAO")

with col2:
    st.metric("Holders Revenue", f"${total_holders:,.0f}", help="Total revenue for veBAL/BAL holders")

with col3:
    st.metric("Incentives Revenue", f"${total_incentives:,.0f}", help="Total revenue for incentives")

with col4:
    st.metric("Total BAL Emitted", f"{total_bal_emitted:,.0f}", help="Total BAL tokens emitted")

st.markdown("---")

st.markdown("### 📈 Revenue Distribution Over Time")

df_daily = df_display.groupby('block_date').agg({
    'sim_dao_revenue': 'sum',
    'sim_holders_revenue': 'sum',
    'sim_incentives_revenue': 'sum'
}).reset_index()

col_chart1, col_chart2, col_chart3 = st.columns(3)

with col_chart1:
    st.markdown("**DAO Revenue**")
    fig_dao = utils.create_minimalist_chart(
        df_daily['block_date'],
        df_daily['sim_dao_revenue'],
        'DAO',
        '#67A2E1'
    )
    st.plotly_chart(fig_dao, use_container_width=True, key="dao_revenue")

with col_chart2:
    st.markdown("**Holders Revenue**")
    fig_holders = utils.create_minimalist_chart(
        df_daily['block_date'],
        df_daily['sim_holders_revenue'],
        'Holders',
        '#E9A97B'
    )
    st.plotly_chart(fig_holders, use_container_width=True, key="holders_revenue")

with col_chart3:
    st.markdown("**Incentives Revenue**")
    fig_incentives = utils.create_minimalist_chart(
        df_daily['block_date'],
        df_daily['sim_incentives_revenue'],
        'Incentives',
        '#B1ACF1'
    )
    st.plotly_chart(fig_incentives, use_container_width=True, key="incentives_revenue")

st.markdown("---")

st.markdown("### 📊 Comparison")

fig_comparison = go.Figure()

fig_comparison.add_trace(go.Scatter(
    x=df_daily['block_date'],
    y=df_daily['sim_dao_revenue'],
    mode='lines',
    name='DAO',
    line=dict(color='#67A2E1', width=1.5)
))

fig_comparison.add_trace(go.Scatter(
    x=df_daily['block_date'],
    y=df_daily['sim_holders_revenue'],
    mode='lines',
    name='Holders',
    line=dict(color='#E9A97B', width=1.5)
))

fig_comparison.add_trace(go.Scatter(
    x=df_daily['block_date'],
    y=df_daily['sim_incentives_revenue'],
    mode='lines',
    name='Incentives',
    line=dict(color='#B1ACF1', width=1.5)
))

fig_comparison.update_layout(
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

st.plotly_chart(fig_comparison, use_container_width=True, key="revenue_comparison")

if filter_by_pools:
    st.markdown("---")
    st.markdown("### 📋 Selected Pools Detailed Analysis")
    
    pool_summary = df_display.groupby('pool_symbol').agg({
        'sim_dao_revenue': 'sum',
        'sim_holders_revenue': 'sum',
        'sim_incentives_revenue': 'sum',
        'sim_bal_emitted': 'sum',
        'protocol_fee_amount_usd': 'sum',
        'direct_incentives': 'sum',
        'dao_profit_usd': 'sum',
        'pool_category': 'first'
    }).round(2)
    
    pool_summary.columns = ['DAO Revenue', 'Holders Revenue', 'Incentives Revenue', 'BAL Emitted', 'Total Revenue', 'Total Incentives', 'DAO Profit', 'Category']
    
    # Format monetary columns for display
    pool_summary_display = pool_summary.copy()
    monetary_cols = ['DAO Revenue', 'Holders Revenue', 'Incentives Revenue', 'Total Revenue', 'Total Incentives', 'DAO Profit']
    for col in monetary_cols:
        if col in pool_summary_display.columns:
            pool_summary_display[col] = pool_summary_display[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
    
    st.dataframe(pool_summary_display, use_container_width=True, hide_index=False)
    
    st.markdown("---")
    st.markdown("### 📊 Individual Pool Analysis")
    
    for idx, pool in enumerate(selected_pools):
        pool_data = df_display[df_display['pool_symbol'] == pool]
        if len(pool_data) > 0:
            category = pool_data['pool_category'].iloc[0] if 'pool_category' in pool_data.columns else 'Unknown'
            
            with st.expander(f"🔍 {pool} ({category})", expanded=False):
                col_p1, col_p2, col_p3, col_p4 = st.columns(4)
                
                with col_p1:
                    st.metric("Total Revenue", f"${pool_data['protocol_fee_amount_usd'].sum():,.0f}")
                with col_p2:
                    st.metric("DAO Revenue", f"${pool_data['sim_dao_revenue'].sum():,.0f}")
                with col_p3:
                    st.metric("Holders Revenue", f"${pool_data['sim_holders_revenue'].sum():,.0f}")
                with col_p4:
                    st.metric("Incentives Revenue", f"${pool_data['sim_incentives_revenue'].sum():,.0f}")
                
                col_p5, col_p6, col_p7 = st.columns(3)
                with col_p5:
                    bal_emitted = pool_data['sim_bal_emitted'].sum() if 'sim_bal_emitted' in pool_data.columns else pool_data['bal_emited_votes'].sum()
                    st.metric("BAL Emitted", f"{bal_emitted:,.0f}")
                with col_p6:
                    st.metric("Total Incentives", f"${pool_data['direct_incentives'].sum():,.0f}")
                with col_p7:
                    st.metric("DAO Profit", f"${pool_data['dao_profit_usd'].sum():,.0f}")
                
                pool_daily = pool_data.groupby('block_date').agg({
                    'sim_dao_revenue': 'sum',
                    'sim_holders_revenue': 'sum',
                    'sim_incentives_revenue': 'sum'
                }).reset_index()
                
                fig_pool = go.Figure()
                fig_pool.add_trace(go.Scatter(
                    x=pool_daily['block_date'],
                    y=pool_daily['sim_dao_revenue'],
                    mode='lines',
                    name='DAO',
                    line=dict(color='#67A2E1', width=1.5)
                ))
                fig_pool.add_trace(go.Scatter(
                    x=pool_daily['block_date'],
                    y=pool_daily['sim_holders_revenue'],
                    mode='lines',
                    name='Holders',
                    line=dict(color='#E9A97B', width=1.5)
                ))
                fig_pool.add_trace(go.Scatter(
                    x=pool_daily['block_date'],
                    y=pool_daily['sim_incentives_revenue'],
                    mode='lines',
                    name='Incentives',
                    line=dict(color='#B1ACF1', width=1.5)
                ))
                
                fig_pool.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=350,
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
                
                st.plotly_chart(fig_pool, use_container_width=True, key=f"pool_detail_{idx}_{hash(pool)}")
