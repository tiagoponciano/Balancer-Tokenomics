import streamlit as st
import utils
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(page_title="Bribes Analysis", layout="wide", page_icon="💰")
utils.inject_css()

df = utils.load_data()
if df.empty:
    st.error("❌ Unable to load data.")
    st.stop()

df_sim = utils.run_simulation_sidebar(df)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Pool Selection")

if 'selected_pools_bribes' not in st.session_state:
    st.session_state.selected_pools_bribes = []
if 'pool_filter_mode_bribes' not in st.session_state:
    st.session_state.pool_filter_mode_bribes = 'top20'

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("TOP 20", key="btn_top20_bribes"):
        st.session_state.pool_filter_mode_bribes = 'top20'
        st.session_state.selected_pools_bribes = []
with col_btn2:
    if st.button("WORST 20", key="btn_worst20_bribes"):
        st.session_state.pool_filter_mode_bribes = 'worst20'
        st.session_state.selected_pools_bribes = []

if st.session_state.pool_filter_mode_bribes == 'top20':
    filter_pools = sorted([str(p) for p in utils.get_top_pools(df, n=20)])
    filter_label = "Select from TOP 20 Pools"
else:
    filter_pools = sorted([str(p) for p in utils.get_worst_pools(df, n=20)])
    filter_label = "Select from WORST 20 Pools"

valid_sel = [p for p in st.session_state.selected_pools_bribes if p in filter_pools]
default_selection = valid_sel if valid_sel else []

if st.sidebar.button("Selecionar tudo", key="btn_select_all_bribes"):
    st.session_state.selected_pools_bribes = filter_pools
    st.rerun()

selected_pools = st.sidebar.multiselect(
    filter_label,
    options=filter_pools,
    default=default_selection,
    help="Select specific pools to view individual analysis"
)
st.session_state.selected_pools_bribes = selected_pools

filter_by_pools = len(selected_pools) > 0

if filter_by_pools:
    df_display = df_sim[df_sim['pool_symbol'].isin(selected_pools)].copy()
    st.info(f"📊 Showing analysis for {len(selected_pools)} selected pool(s)")
else:
    df_display = df_sim.copy()

st.markdown('<div class="page-title">Bribes Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Analysis of bribes, voting patterns, and their impact on BAL distribution</div>', unsafe_allow_html=True)

st.markdown("---")

st.warning("⚠️ **Bribe Data Collection in Progress**\n\nBribe data is currently being collected and will be integrated into this analysis. The structure is ready to receive data from:\n\n- Votium (votium.app)\n- Hidden Hand (hiddenhand.finance)\n- Direct on-chain bribe contracts\n- Dune Analytics queries for bribe events")

st.markdown("---")

st.markdown("### 📊 Planned Analysis Structure")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📈 Metrics to Track")
    st.markdown("""
    - **Total Bribes Received**: Sum of all bribes per pool
    - **Bribe-to-Vote Ratio**: Correlation between bribes and votes received
    - **Bribe Efficiency**: BAL received per USD of bribe
    - **Strategic vs Mercenary Votes**: Classification based on bribe patterns
    """)

with col2:
    st.markdown("#### 🔍 Analysis Features")
    st.markdown("""
    - **Bribe Timeline**: Historical bribe distribution over time
    - **Voting Correlation**: Relationship between bribes and voting patterns
    - **Pool Comparison**: Compare pools with and without bribes
    - **Impact Assessment**: Effect of bribes on BAL distribution
    """)

st.markdown("---")

st.markdown("### 📋 Data Structure (Placeholder)")

bribe_structure = pd.DataFrame({
    'Pool': ['Pool A', 'Pool B', 'Pool C'],
    'Total Bribes (USD)': [0, 0, 0],
    'Bribes Count': [0, 0, 0],
    'Votes Received': [0, 0, 0],
    'Bribe per Vote': [0, 0, 0],
    'BAL Received': [0, 0, 0],
    'Bribe Efficiency': [0, 0, 0]
})

st.dataframe(bribe_structure, use_container_width=True, hide_index=True)

st.markdown("---")

st.markdown("### 💡 Integration Plan")

st.info("""
**Data Collection Strategy:**

1. **On-Chain Data**: Query bribe contracts directly from blockchain
2. **Platform Integration**: Connect to Votium and Hidden Hand APIs
3. **Historical Analysis**: Aggregate historical bribe data by pool and week
4. **Voting Correlation**: Match bribes with voting patterns and BAL distribution

**Expected Timeline**: Data collection and integration in progress
""")

if filter_by_pools:
    st.markdown("---")
    st.markdown("### 📋 Selected Pools Bribe Analysis (Placeholder)")
    
    for pool in selected_pools:
        pool_data = df_display[df_display['pool_symbol'] == pool]
        if len(pool_data) > 0:
            with st.expander(f"{pool}"):
                st.markdown("**Bribe data will be displayed here once available**")
                
                col_p1, col_p2, col_p3 = st.columns(3)
                col_p1.metric("Total Revenue", f"${pool_data['protocol_fee_amount_usd'].sum():,.0f}")
                col_p2.metric("Total Incentives", f"${pool_data['direct_incentives'].sum():,.0f}")
                col_p3.metric("DAO Profit", f"${pool_data['dao_profit_usd'].sum():,.0f}")
