import streamlit as st
import utils
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
import traceback

st.set_page_config(page_title="Bribes Analysis", layout="wide", page_icon="💰")
utils.inject_css()

try:
    # Load data
    df = utils.load_data()
    df_bribes = utils.load_bribes_data()

    if df.empty:
        st.error("❌ Unable to load main data.")
        st.info("Please ensure `data/balancer_v2_financial_master_final.csv` exists.")
        st.stop()

    if df_bribes.empty:
        st.warning("⚠️ Bribes data file not found. Please ensure the bribes CSV file is in the `data/` folder.")
        st.info("Looking for files like: `data/Balancer_Bribes_Gauges_enriched.csv` or `data/balancer_bribes_gauges_enriched.csv`")
        st.info("Available files in data/:")
        import os
        if os.path.exists('data'):
            files = [f for f in os.listdir('data') if f.endswith('.csv')]
            for f in files[:10]:
                st.text(f"  - {f}")
        st.stop()

    df_sim = utils.run_simulation_sidebar(df)
except Exception as e:
    st.error(f"❌ Error loading data: {str(e)}")
    st.code(traceback.format_exc())
    st.stop()

# Sidebar - Pool Selection
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

# Prepare data
if filter_by_pools:
    df_display = df_sim[df_sim['pool_symbol'].isin(selected_pools)].copy()
    # Try to match pools - check multiple possible pool columns
    pool_match_col = None
    for col in ['pool_title', 'pool_name', 'pool_symbol', 'pool']:
        if col in df_bribes.columns:
            pool_match_col = col
            break
    
    if pool_match_col:
        # Try exact match first, then case-insensitive
        df_bribes_display = df_bribes[
            df_bribes[pool_match_col].astype(str).str.upper().isin([p.upper() for p in selected_pools])
        ].copy()
    else:
        df_bribes_display = df_bribes.copy()
    st.info(f"📊 Showing analysis for {len(selected_pools)} selected pool(s)")
else:
    df_display = df_sim.copy()
    df_bribes_display = df_bribes.copy()

# Page Header
st.markdown('<div class="page-title">💰 Bribes Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Comprehensive analysis of bribes, voting patterns, and their impact on BAL distribution</div>', unsafe_allow_html=True)

st.markdown("---")

try:
    # Identify pool column in bribes data
    pool_col = None
    for col in ['pool_title', 'pool_name', 'pool_symbol', 'pool', 'gauge', 'gauge_address', 'symbol', 'name', 'Pool', 'POOL']:
        if col in df_bribes.columns:
            pool_col = col
            break

    if pool_col is None:
        st.error("❌ Could not identify pool column in bribes data.")
        st.info(f"Available columns: {', '.join(df_bribes.columns.tolist())}")
        st.dataframe(df_bribes.head(5))
        st.stop()
except Exception as e:
    st.error(f"❌ Error identifying pool column: {str(e)}")
    st.code(traceback.format_exc())
    st.stop()

# Debug: Show column info
if st.sidebar.checkbox("🔍 Show Data Info", value=False):
    st.sidebar.write(f"**Pool Column:** {pool_col}")
    st.sidebar.write(f"**Total Rows:** {len(df_bribes)}")
    st.sidebar.write(f"**Columns:** {len(df_bribes.columns)}")
    st.sidebar.dataframe(df_bribes.head(3))

try:
    # Identify bribe-related columns
    bribe_col = None
    votes_col = None
    bal_col = None

    # Try to find bribe amount column (case-insensitive search)
    df_cols_lower = {col.lower(): col for col in df_bribes.columns}
    for col_lower in ['amount_usdc', 'bribe_amount_usd', 'total_bribes_usd', 'bribe_amount', 'bribes_usd', 'amount_usd', 'bribe', 'bribes', 'amount']:
        if col_lower in df_cols_lower:
            bribe_col = df_cols_lower[col_lower]
            break

    # Try to find votes column (may not exist in this dataset)
    for col_lower in ['votes_received', 'votes', 'total_votes', 'vote_count', 'vote']:
        if col_lower in df_cols_lower:
            votes_col = df_cols_lower[col_lower]
            break

    # Try to find BAL column (may not exist in this dataset)
    for col_lower in ['bal_received', 'bal_emitted', 'bal', 'bal_amount', 'bal_tokens', 'bal_emissions']:
        if col_lower in df_cols_lower:
            bal_col = df_cols_lower[col_lower]
            break
    
    # Also check for total_bribes_periodo which might be useful
    total_bribes_col = None
    if 'total_bribes_periodo' in df_bribes.columns:
        total_bribes_col = 'total_bribes_periodo'

    if bribe_col is None:
        st.error("❌ Could not find bribe amount column in the data.")
        st.info(f"Available columns: {', '.join(df_bribes.columns.tolist())}")
        st.dataframe(df_bribes.head(5))
        st.stop()
except Exception as e:
    st.error(f"❌ Error identifying columns: {str(e)}")
    st.code(traceback.format_exc())
    st.stop()

try:
    # Aggregate bribes data by pool
    agg_dict = {bribe_col: 'sum'}
    if votes_col:
        agg_dict[votes_col] = 'sum'
    if bal_col:
        agg_dict[bal_col] = 'sum'
    # Include total_bribes_periodo if available
    if 'total_bribes_periodo' in df_bribes_display.columns:
        agg_dict['total_bribes_periodo'] = 'max'  # Use max since it's per periodo

    # Calculate metrics
    pool_bribes = df_bribes_display.groupby(pool_col).agg(agg_dict).reset_index()
except Exception as e:
    st.error(f"❌ Error aggregating data: {str(e)}")
    st.code(traceback.format_exc())
    st.stop()

# Calculate derived metrics
if votes_col and votes_col in pool_bribes.columns:
    pool_bribes['bribe_per_vote'] = np.where(
        pool_bribes[votes_col] > 0,
        pool_bribes[bribe_col] / pool_bribes[votes_col],
        0
    )

if bal_col and bal_col in pool_bribes.columns:
    pool_bribes['bribe_efficiency'] = np.where(
        pool_bribes[bribe_col] > 0,
        pool_bribes[bal_col] / pool_bribes[bribe_col],
        0
    )
else:
    # If no BAL column, create efficiency metrics based on available data
    if votes_col and votes_col in pool_bribes.columns:
        # Votes per USD as proxy for efficiency
        pool_bribes['bribe_efficiency'] = np.where(
            pool_bribes[bribe_col] > 0,
            pool_bribes[votes_col] / pool_bribes[bribe_col] * 1000,  # Votes per USD as proxy
            0
        )
    elif 'total_bribes_periodo' in pool_bribes.columns:
        # Use total_bribes_periodo / amount_usdc as a ratio metric
        pool_bribes['bribe_efficiency'] = np.where(
            pool_bribes[bribe_col] > 0,
            pool_bribes['total_bribes_periodo'] / pool_bribes[bribe_col],
            0
        )
    else:
        # No efficiency metric available
        pool_bribes['bribe_efficiency'] = 0

# Merge with main data for additional context (if pool_symbol exists in main data)
if 'pool_symbol' in df_display.columns:
    main_agg = df_display.groupby('pool_symbol').agg({
        'dao_profit_usd': 'sum',
        'protocol_fee_amount_usd': 'sum',
        'direct_incentives': 'sum'
    }).reset_index()
    
    # Try to match pools (case-insensitive match)
    # The bribes data uses pool_title/pool_name, main data uses pool_symbol
    # Try to match by converting both to uppercase and matching
    pool_bribes['pool_symbol_matched'] = pool_bribes[pool_col].astype(str).str.upper().str.strip()
    main_agg['pool_symbol_upper'] = main_agg['pool_symbol'].astype(str).str.upper().str.strip()
    
    pool_bribes = pool_bribes.merge(
        main_agg,
        left_on='pool_symbol_matched',
        right_on='pool_symbol_upper',
        how='left'
    )

# Main Metrics
st.markdown("### 📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

total_bribes = pool_bribes[bribe_col].sum() if bribe_col in pool_bribes.columns else 0
total_votes = pool_bribes[votes_col].sum() if votes_col and votes_col in pool_bribes.columns else 0
total_bal = pool_bribes[bal_col].sum() if bal_col and bal_col in pool_bribes.columns else 0
avg_efficiency = pool_bribes['bribe_efficiency'].mean() if 'bribe_efficiency' in pool_bribes.columns else 0

with col1:
    st.metric(
        "Total Bribes",
        f"${total_bribes:,.0f}",
        help="Total USD value of all bribes received"
    )

with col2:
    st.metric(
        "Total Votes",
        f"{total_votes:,.0f}",
        help="Total votes received across all pools"
    )

with col3:
    st.metric(
        "Total BAL Received",
        f"{total_bal:,.0f}",
        help="Total BAL tokens received from bribes"
    )

with col4:
    st.metric(
        "Avg Bribe Efficiency",
        f"{avg_efficiency:.2f}",
        help="Average BAL received per USD of bribe"
    )

st.markdown("---")

# Rankings
st.markdown("### 🏆 Pool Rankings")

tab1, tab2, tab3, tab4 = st.tabs(["💰 Top Bribes", "⚡ Best Efficiency", "📈 Most Votes", "❌ Worst Performance"])

with tab1:
    if bribe_col in pool_bribes.columns:
        top_bribes = pool_bribes.nlargest(20, bribe_col)[[pool_col, bribe_col]].copy()
        top_bribes.columns = ['Pool', 'Total Bribes (USD)']
        top_bribes['Total Bribes (USD)'] = top_bribes['Total Bribes (USD)'].apply(lambda x: f"${x:,.0f}")
        st.dataframe(top_bribes, use_container_width=True, hide_index=True)
    else:
        st.info("Bribe amount data not available")

with tab2:
    if 'bribe_efficiency' in pool_bribes.columns:
        top_efficiency = pool_bribes[pool_bribes['bribe_efficiency'] > 0].nlargest(20, 'bribe_efficiency')[[pool_col, 'bribe_efficiency']].copy()
        top_efficiency.columns = ['Pool', 'Bribe Efficiency']
        top_efficiency['Bribe Efficiency'] = top_efficiency['Bribe Efficiency'].apply(lambda x: f"{x:.3f}")
        st.dataframe(top_efficiency, use_container_width=True, hide_index=True)
    else:
        st.info("Efficiency data not available")

with tab3:
    if votes_col and votes_col in pool_bribes.columns:
        top_votes = pool_bribes.nlargest(20, votes_col)[[pool_col, votes_col]].copy()
        top_votes.columns = ['Pool', 'Total Votes']
        top_votes['Total Votes'] = top_votes['Total Votes'].apply(lambda x: f"{x:,.0f}")
        st.dataframe(top_votes, use_container_width=True, hide_index=True)
    else:
        st.info("Votes data not available")

with tab4:
    if 'bribe_efficiency' in pool_bribes.columns and bribe_col in pool_bribes.columns:
        worst = pool_bribes[(pool_bribes[bribe_col] > 0) & (pool_bribes['bribe_efficiency'] > 0)].nsmallest(20, 'bribe_efficiency')[[pool_col, bribe_col, 'bribe_efficiency']].copy()
        worst.columns = ['Pool', 'Total Bribes (USD)', 'Bribe Efficiency']
        worst['Total Bribes (USD)'] = worst['Total Bribes (USD)'].apply(lambda x: f"${x:,.0f}")
        worst['Bribe Efficiency'] = worst['Bribe Efficiency'].apply(lambda x: f"{x:.3f}")
        st.dataframe(worst, use_container_width=True, hide_index=True)
    else:
        st.info("Performance data not available")

st.markdown("---")

# Visualizations
st.markdown("### 📈 Visualizations")

viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    if bribe_col in pool_bribes.columns and 'bribe_efficiency' in pool_bribes.columns:
        fig_scatter = px.scatter(
            pool_bribes[pool_bribes[bribe_col] > 0],
            x=bribe_col,
            y='bribe_efficiency',
            hover_data=[pool_col],
            title="💰 Bribe Amount vs Efficiency",
            labels={bribe_col: 'Total Bribes (USD)', 'bribe_efficiency': 'Bribe Efficiency (BAL/USD)'},
            color='bribe_efficiency',
            color_continuous_scale='Viridis',
            size=bribe_col,
            size_max=20
        )
        fig_scatter.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_color='white',
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

with viz_col2:
    if votes_col and votes_col in pool_bribes.columns and bribe_col in pool_bribes.columns:
        fig_votes = px.scatter(
            pool_bribes[pool_bribes[bribe_col] > 0],
            x=bribe_col,
            y=votes_col,
            hover_data=[pool_col],
            title="📊 Bribes vs Votes Received",
            labels={bribe_col: 'Total Bribes (USD)', votes_col: 'Total Votes'},
            color=votes_col,
            color_continuous_scale='Blues',
            size=votes_col,
            size_max=20
        )
        fig_votes.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_color='white',
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig_votes, use_container_width=True)

# Top pools bar chart
st.markdown("#### 🏅 Top 10 Pools by Total Bribes")
if bribe_col in pool_bribes.columns:
    top_10 = pool_bribes.nlargest(10, bribe_col)
    fig_bar = px.bar(
        top_10,
        x=pool_col,
        y=bribe_col,
        title="Top 10 Pools by Bribe Amount",
        labels={bribe_col: 'Total Bribes (USD)', pool_col: 'Pool'},
        color=bribe_col,
        color_continuous_scale='Viridis'
    )
    fig_bar.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_color='white',
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Timeline if date column exists
date_col = None
for col in ['day', 'week_date', 'date', 'block_date', 'timestamp', 'week', 'period', 'time']:
    if col in df_bribes.columns:
        date_col = col
        break

if date_col:
    st.markdown("#### 📅 Bribe Timeline")
    if bribe_col in df_bribes_display.columns:
        timeline_data = df_bribes_display.groupby([date_col, pool_col])[bribe_col].sum().reset_index()
        if not timeline_data.empty and len(timeline_data[pool_col].unique()) <= 20:
            # Show individual pools if not too many
            fig_timeline = px.line(
                timeline_data,
                x=date_col,
                y=bribe_col,
                color=pool_col,
                title="💰 Bribe Amount Over Time by Pool",
                labels={bribe_col: 'Bribes (USD)', date_col: 'Date', pool_col: 'Pool'}
            )
        else:
            # Aggregate by date if too many pools
            timeline_agg = df_bribes_display.groupby(date_col)[bribe_col].sum().reset_index()
            fig_timeline = px.line(
                timeline_agg,
                x=date_col,
                y=bribe_col,
                title="💰 Total Bribes Over Time",
                labels={bribe_col: 'Total Bribes (USD)', date_col: 'Date'}
            )
        
        fig_timeline.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_color='white',
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            legend=dict(bgcolor='rgba(0,0,0,0.5)')
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

# Detailed Pool Analysis
if filter_by_pools and len(selected_pools) > 0:
    st.markdown("---")
    st.markdown("### 🔍 Detailed Pool Analysis")
    
    for pool in selected_pools:
        # Try to match pool from selected_pools (which are pool_symbol) with pool_col in bribes data
        # Match case-insensitive
        pool_bribe_data = pool_bribes[
            pool_bribes[pool_col].astype(str).str.upper().str.strip() == pool.upper().strip()
        ]
        pool_main_data = df_display[df_display['pool_symbol'] == pool] if 'pool_symbol' in df_display.columns else pd.DataFrame()
        
        if not pool_bribe_data.empty:
            with st.expander(f"📊 {pool}", expanded=False):
                col_p1, col_p2, col_p3, col_p4 = st.columns(4)
                
                pool_bribes_val = pool_bribe_data[bribe_col].iloc[0] if bribe_col in pool_bribe_data.columns else 0
                pool_votes_val = pool_bribe_data[votes_col].iloc[0] if votes_col and votes_col in pool_bribe_data.columns else 0
                pool_bal_val = pool_bribe_data[bal_col].iloc[0] if bal_col and bal_col in pool_bribe_data.columns else 0
                pool_eff = pool_bribe_data['bribe_efficiency'].iloc[0] if 'bribe_efficiency' in pool_bribe_data.columns else 0
                
                with col_p1:
                    st.metric("Total Bribes", f"${pool_bribes_val:,.0f}")
                with col_p2:
                    st.metric("Votes Received", f"{pool_votes_val:,.0f}")
                with col_p3:
                    st.metric("BAL Received", f"{pool_bal_val:,.0f}")
                with col_p4:
                    st.metric("Efficiency", f"{pool_eff:.3f}")
                
                if not pool_main_data.empty:
                    st.markdown("**Financial Metrics:**")
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        st.metric("Total Revenue", f"${pool_main_data['protocol_fee_amount_usd'].sum():,.0f}")
                    with col_f2:
                        st.metric("Total Incentives", f"${pool_main_data['direct_incentives'].sum():,.0f}")
                    with col_f3:
                        st.metric("DAO Profit", f"${pool_main_data['dao_profit_usd'].sum():,.0f}")
