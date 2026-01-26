import streamlit as st
import utils
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="veBAL Votes", layout="wide", page_icon="🗳️")

# Check authentication
if not utils.check_authentication():
    st.stop()

utils.inject_css()

# Load veBAL votes data
df_votes = utils.load_vebal_votes_data()

if df_votes.empty:
    st.warning("⚠️ veBAL votes data file not found. Please ensure 'veBAL_votes.csv' is in the `data/` folder.")
    st.stop()

# Clean symbol column (remove HTML tags)
def clean_symbol(symbol):
    """Extract text from HTML links"""
    if pd.isna(symbol):
        return ""
    # Remove HTML tags and extract text
    text = re.sub(r'<[^>]+>', '', str(symbol))
    # Remove the ↗ emoji if present
    text = text.replace('↗', '').strip()
    return text

def extract_gauge_address(gauge_str):
    """Extract gauge address from the gauge column"""
    if pd.isna(gauge_str):
        return ""
    gauge_str = str(gauge_str)
    # Remove 0x prefix if present and return
    if gauge_str.startswith('0x'):
        return gauge_str
    return gauge_str

df_votes['symbol_clean'] = df_votes['symbol'].apply(clean_symbol)
df_votes['gauge_address'] = df_votes['gauge'].apply(extract_gauge_address)

# Page Header with logout button
col_title, col_logout = st.columns([1, 0.1])
with col_title:
    st.markdown('<div class="page-title">🗳️ veBAL Votes Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Current voting distribution across Balancer gauges</div>', unsafe_allow_html=True)
with col_logout:
    utils.show_logout_button()

st.markdown("---")

# Main Metrics
st.markdown("### 📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

total_votes = df_votes['votes'].sum()
total_gauges = len(df_votes)
top_gauge_votes = df_votes['votes'].max()
top_gauge_pct = df_votes['pct_votes'].max() * 100

with col1:
    st.metric("Total Votes", f"{total_votes:,.0f}", help="Total votes across all gauges")

with col2:
    st.metric("Total Gauges", f"{total_gauges:,}", help="Number of gauges receiving votes")

with col3:
    st.metric("Top Gauge Votes", f"{top_gauge_votes:,.0f}", help="Highest vote count for a single gauge")

with col4:
    st.metric("Top Gauge Share", f"{top_gauge_pct:.2f}%", help="Percentage of total votes for top gauge")

st.markdown("---")

# Rankings and Visualizations
st.markdown("### 🏆 Gauge Rankings")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Top Gauges", "📈 Distribution", "🥧 Vote Share", "📋 Full Table"])

with tab1:
    st.markdown("#### Top 20 Gauges by Votes")
    
    # Slider to select number of top gauges
    n_gauges = st.slider("Number of top gauges to display", 10, 50, 20, 5)
    top_n = df_votes.nlargest(n_gauges, 'votes')
    
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        # Horizontal bar chart for better readability
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            y=top_n['symbol_clean'].iloc[::-1],  # Reverse for top-to-bottom
            x=top_n['votes'].iloc[::-1],
            orientation='h',
            marker=dict(
                color=top_n['votes'].iloc[::-1],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(
                    title=dict(text="Votes", font=dict(color='white')),
                    tickfont=dict(color='white')
                )
            ),
            text=[f"{v:,.0f}" for v in top_n['votes'].iloc[::-1]],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Votes: %{x:,.0f}<br>Share: %{customdata:.2f}%<extra></extra>',
            customdata=top_n['pct_votes'].iloc[::-1] * 100
        ))
        fig_bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title=dict(font=dict(color='white', size=16)),
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.1)',
                title=dict(text="Votes", font=dict(color='#8B95A6'))
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.1)',
                title="",
                tickfont=dict(size=10)
            ),
            height=600,
            margin=dict(l=200, r=50, t=20, b=50),
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col_chart2:
        st.markdown("**Top 5 Gauges**")
        top_5 = df_votes.nlargest(5, 'votes')
        for idx, row in top_5.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #67A2E1;">
                    <div style="font-weight: 600; color: #67A2E1; font-size: 0.9rem;">#{int(row['ranking'])} {row['symbol_clean'][:30]}</div>
                    <div style="font-size: 1.2rem; font-weight: 700; color: white; margin-top: 0.3rem;">{row['votes']:,.0f}</div>
                    <div style="font-size: 0.8rem; color: #8B95A6; margin-top: 0.2rem;">{row['pct_votes']*100:.2f}% share</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Table
    st.markdown("#### Detailed Rankings")
    top_n_display = top_n[['ranking', 'symbol_clean', 'votes', 'pct_votes']].copy()
    top_n_display['votes'] = top_n_display['votes'].apply(lambda x: f"{x:,.0f}")
    top_n_display['pct_votes'] = top_n_display['pct_votes'].apply(lambda x: f"{x*100:.2f}%")
    top_n_display.columns = ['Rank', 'Gauge', 'Votes', 'Share %']
    st.dataframe(top_n_display, use_container_width=True, hide_index=True)

with tab2:
    st.markdown("#### Vote Distribution Analysis")
    
    col_dist1, col_dist2 = st.columns(2)
    
    with col_dist1:
        # Histogram with log scale option
        use_log = st.checkbox("Use logarithmic scale", value=False)
        
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=df_votes['votes'],
            nbinsx=50,
            marker=dict(
                color='#67A2E1',
                line=dict(color='rgba(103, 162, 225, 0.3)', width=1)
            ),
            hovertemplate='Votes: %{x:,.0f}<br>Count: %{y}<extra></extra>'
        ))
        
        xaxis_type = 'log' if use_log else 'linear'
        fig_hist.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title=dict(text="Distribution of Votes Across Gauges", font=dict(color='white', size=16)),
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.1)',
                title=dict(text="Votes", font=dict(color='#8B95A6')),
                type=xaxis_type
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.1)',
                title=dict(text="Number of Gauges", font=dict(color='#8B95A6'))
            ),
            height=400
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col_dist2:
        # Box plot
        fig_box = go.Figure()
        fig_box.add_trace(go.Box(
            y=df_votes['votes'],
            name='Votes Distribution',
            marker_color='#B1ACF1',
            boxmean='sd'
        ))
        fig_box.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title=dict(text="Vote Distribution Box Plot", font=dict(color='white', size=16)),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.1)',
                title=dict(text="Votes", font=dict(color='#8B95A6')),
                type='log'
            ),
            xaxis=dict(showgrid=False),
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_box, use_container_width=True)
    
    # Statistics
    col_stat1, col_stat2, col_stat3, col_stat4, col_stat5 = st.columns(5)
    with col_stat1:
        st.metric("Mean Votes", f"{df_votes['votes'].mean():,.0f}")
    with col_stat2:
        st.metric("Median Votes", f"{df_votes['votes'].median():,.0f}")
    with col_stat3:
        st.metric("Std Deviation", f"{df_votes['votes'].std():,.0f}")
    with col_stat4:
        st.metric("Min Votes", f"{df_votes['votes'].min():,.2f}")
    with col_stat5:
        st.metric("Max Votes", f"{df_votes['votes'].max():,.0f}")
    
    # Percentiles
    st.markdown("#### Percentiles")
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    percentile_data = {f'P{p}': np.percentile(df_votes['votes'], p) for p in percentiles}
    col_p1, col_p2, col_p3, col_p4, col_p5, col_p6, col_p7 = st.columns(7)
    cols_p = [col_p1, col_p2, col_p3, col_p4, col_p5, col_p6, col_p7]
    for col, (label, value) in zip(cols_p, percentile_data.items()):
        with col:
            st.metric(label, f"{value:,.0f}")

with tab3:
    st.markdown("#### Vote Share Visualization")
    
    n_top_pie = st.slider("Number of top gauges for pie chart", 5, 20, 10, 1)
    
    col_pie1, col_pie2 = st.columns(2)
    
    with col_pie1:
        # Pie chart for top N
        top_n_pie = df_votes.nlargest(n_top_pie, 'votes')
        others_votes = df_votes['votes'].sum() - top_n_pie['votes'].sum()
        
        pie_data = top_n_pie.copy()
        if others_votes > 0:
            others_row = pd.DataFrame({
                'symbol_clean': ['Others'],
                'votes': [others_votes],
                'pct_votes': [others_votes / df_votes['votes'].sum()]
            })
            pie_data = pd.concat([pie_data, others_row], ignore_index=True)
        
        fig_pie = px.pie(
            pie_data,
            values='votes',
            names='symbol_clean',
            title=f"Vote Share - Top {n_top_pie} Gauges",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Votes: %{value:,.0f}<br>Share: %{percent}<extra></extra>'
        )
        fig_pie.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title=dict(font=dict(color='white', size=16)),
            legend=dict(
                bgcolor='rgba(0,0,0,0.5)',
                font=dict(size=10),
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.1
            )
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_pie2:
        # Treemap
        top_n_treemap = df_votes.nlargest(15, 'votes')
        fig_treemap = px.treemap(
            top_n_treemap,
            path=['symbol_clean'],
            values='votes',
            title=f"Vote Distribution - Top 15 Gauges",
            color='votes',
            color_continuous_scale='Viridis'
        )
        fig_treemap.update_traces(
            textinfo='label+value+percent parent',
            hovertemplate='<b>%{label}</b><br>Votes: %{value:,.0f}<br>Share: %{percentParent:.2f}%<extra></extra>'
        )
        fig_treemap.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title=dict(font=dict(color='white', size=16))
        )
        st.plotly_chart(fig_treemap, use_container_width=True)
    
    # Cumulative percentage
    st.markdown("#### Cumulative Vote Distribution")
    df_sorted = df_votes.sort_values('votes', ascending=False).copy()
    df_sorted['cumulative_pct'] = (df_sorted['votes'].cumsum() / df_sorted['votes'].sum() * 100)
    df_sorted['rank'] = range(1, len(df_sorted) + 1)
    
    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(
        x=df_sorted['rank'],
        y=df_sorted['cumulative_pct'],
        mode='lines',
        name='Cumulative %',
        line=dict(color='#67A2E1', width=2),
        fill='tozeroy',
        fillcolor='rgba(103, 162, 225, 0.1)',
        hovertemplate='Rank: %{x}<br>Cumulative: %{y:.2f}%<extra></extra>'
    ))
    
    # Add reference lines
    for pct in [25, 50, 75, 90]:
        rank_at_pct = df_sorted[df_sorted['cumulative_pct'] <= pct]['rank'].max()
        if not pd.isna(rank_at_pct):
            fig_cum.add_vline(
                x=rank_at_pct,
                line_dash="dash",
                line_color="rgba(255,255,255,0.3)",
                annotation_text=f"{pct}%",
                annotation_position="top"
            )
    
    fig_cum.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title=dict(text="Cumulative Vote Percentage by Rank", font=dict(color='white', size=16)),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            title=dict(text="Gauge Rank", font=dict(color='#8B95A6'))
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            title=dict(text="Cumulative % of Votes", font=dict(color='#8B95A6'))
        ),
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig_cum, use_container_width=True)

with tab4:
    st.markdown("#### Full Gauge Rankings")
    
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        # Search/filter
        search_term = st.text_input("🔍 Search gauge", placeholder="Type to filter...", key="search_gauge")
    
    with col_filter2:
        # Filter by minimum votes
        min_votes = st.number_input("Minimum votes", min_value=0.0, value=0.0, step=1000.0, key="min_votes")
    
    with col_filter3:
        # Filter by minimum share
        min_share = st.number_input("Minimum share (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="min_share")
    
    display_df = df_votes.copy()
    
    # Apply filters
    if search_term:
        display_df = display_df[
            display_df['symbol_clean'].str.contains(search_term, case=False, na=False)
        ]
    
    if min_votes > 0:
        display_df = display_df[display_df['votes'] >= min_votes]
    
    if min_share > 0:
        display_df = display_df[display_df['pct_votes'] * 100 >= min_share]
    
    # Sort options
    col_sort1, col_sort2 = st.columns(2)
    with col_sort1:
        sort_by = st.selectbox("Sort by", ['votes', 'ranking', 'pct_votes'], index=0, key="sort_by")
    with col_sort2:
        sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True, index=0, key="sort_order")
    
    display_df = display_df.sort_values(sort_by, ascending=(sort_order == "Ascending"))
    
    # Format display with better styling
    display_table = display_df[['ranking', 'symbol_clean', 'votes', 'pct_votes']].copy()
    display_table['votes'] = display_table['votes'].apply(lambda x: f"{x:,.0f}")
    display_table['pct_votes'] = display_table['pct_votes'].apply(lambda x: f"{x*100:.2f}%")
    display_table.columns = ['Rank', 'Gauge', 'Votes', 'Share %']
    
    # Add rank highlighting
    st.dataframe(
        display_table,
        use_container_width=True,
        hide_index=True,
        height=600
    )
    st.caption(f"Showing {len(display_table)} of {len(df_votes)} gauges")
    
    # Download button
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download filtered data as CSV",
        data=csv,
        file_name=f'vebal_votes_filtered_{len(display_df)}.csv',
        mime='text/csv'
    )

st.markdown("---")

# Insights
st.markdown("### 💡 Insights & Analysis")

col_insight1, col_insight2, col_insight3 = st.columns(3)

with col_insight1:
    st.markdown("#### 📊 Concentration Analysis")
    top_5_pct = (df_votes.nlargest(5, 'votes')['votes'].sum() / total_votes * 100)
    top_10_pct = (df_votes.nlargest(10, 'votes')['votes'].sum() / total_votes * 100)
    top_20_pct = (df_votes.nlargest(20, 'votes')['votes'].sum() / total_votes * 100)
    
    st.metric("Top 5 Gauges Share", f"{top_5_pct:.1f}%")
    st.metric("Top 10 Gauges Share", f"{top_10_pct:.1f}%")
    st.metric("Top 20 Gauges Share", f"{top_20_pct:.1f}%")
    
    # Gini coefficient approximation
    df_sorted_votes = df_votes.sort_values('votes', ascending=True)
    n = len(df_sorted_votes)
    cumsum = df_sorted_votes['votes'].cumsum()
    gini = (2 * sum((i + 1) * v for i, v in enumerate(df_sorted_votes['votes']))) / (n * total_votes) - (n + 1) / n
    
    st.metric("Gini Coefficient", f"{gini:.3f}", help="0 = perfect equality, 1 = perfect inequality")
    
    if top_10_pct > 50:
        st.error("⚠️ **High concentration**: Top 10 gauges control majority of votes")
    elif top_10_pct > 30:
        st.warning("⚖️ **Moderate concentration** in top gauges")
    else:
        st.success("✅ Votes are relatively distributed")

with col_insight2:
    st.markdown("#### 📈 Vote Distribution")
    median_votes = df_votes['votes'].median()
    mean_votes = df_votes['votes'].mean()
    std_votes = df_votes['votes'].std()
    cv = (std_votes / mean_votes) * 100 if mean_votes > 0 else 0
    
    st.metric("Median Votes per Gauge", f"{median_votes:,.0f}")
    st.metric("Mean Votes per Gauge", f"{mean_votes:,.0f}")
    st.metric("Coefficient of Variation", f"{cv:.1f}%", help="Higher CV = more variability")
    
    if mean_votes > median_votes * 2:
        st.info("📊 **Right-skewed distribution**: Few gauges have very high votes")
    else:
        st.success("📊 Relatively balanced distribution")
    
    # Zero votes count
    zero_votes = len(df_votes[df_votes['votes'] == 0])
    if zero_votes > 0:
        st.warning(f"⚠️ {zero_votes} gauges have zero votes")

with col_insight3:
    st.markdown("#### 🎯 Power Distribution")
    
    # Calculate how many gauges control X% of votes
    df_sorted_power = df_votes.sort_values('votes', ascending=False)
    cumsum_power = df_sorted_power['votes'].cumsum()
    
    for target_pct in [50, 80, 90]:
        target_votes = total_votes * (target_pct / 100)
        n_gauges = len(cumsum_power[cumsum_power <= target_votes])
        if n_gauges == 0:
            n_gauges = 1
        st.metric(
            f"Gauges controlling {target_pct}%",
            f"{n_gauges}",
            help=f"Number of top gauges needed to control {target_pct}% of votes"
        )
    
    # Herfindahl-Hirschman Index (HHI)
    hhi = sum((df_votes['pct_votes'] * 100) ** 2)
    st.metric("HHI Index", f"{hhi:.0f}", help="Higher HHI = more concentration (0-10000 scale)")
    
    if hhi > 2500:
        st.error("🔴 **High market concentration** (HHI > 2500)")
    elif hhi > 1500:
        st.warning("🟡 **Moderate concentration** (HHI 1500-2500)")
    else:
        st.success("🟢 **Low concentration** (HHI < 1500)")

# Votes vs Pool Performance Analysis
st.markdown("---")
st.markdown("### 🏆 Votes vs Pool Performance")

try:
    # Load main data and bribes data to identify top/worst pools and get gauge mappings
    df_main = utils.load_data()
    df_bribes = utils.load_bribes_data()
    
    if not df_main.empty:
        # Get top and worst pools
        top_pools = utils.get_top_pools(df_main, n=20)
        worst_pools = utils.get_worst_pools(df_main, n=20)
        
        # Aggregate pool data by pool_symbol
        pool_performance = df_main.groupby('pool_symbol').agg({
            'dao_profit_usd': 'sum',
            'protocol_fee_amount_usd': 'sum',
            'direct_incentives': 'sum',
            'votes_received': 'sum'
        }).reset_index()
        
        # Try to match using bribes data which has gauge_address mapping
        votes_with_performance = df_votes.copy()
        votes_with_performance['matched_pool'] = None
        votes_with_performance['dao_profit_usd'] = np.nan
        votes_with_performance['protocol_fee_amount_usd'] = np.nan
        votes_with_performance['direct_incentives'] = np.nan
        
        # Method 1: Match via gauge_address using bribes data
        if not df_bribes.empty and 'gauge_address' in df_bribes.columns:
            # Normalize gauge addresses
            def clean_gauge_addr(addr):
                if pd.isna(addr):
                    return ""
                addr_str = str(addr).lower().strip()
                if addr_str.startswith('0x'):
                    return addr_str
                return addr_str
            
            df_bribes['gauge_address_clean'] = df_bribes['gauge_address'].apply(clean_gauge_addr)
            votes_with_performance['gauge_address_normalized'] = votes_with_performance['gauge_address'].apply(clean_gauge_addr)
            
            # Get unique pool-gauge mappings from bribes (use pool_title or pool_name)
            # Create a mapping: gauge -> pool_name, then pool_name -> pool_symbol
            gauge_to_pool_name = {}
            pool_name_to_symbol = {}
            
            for _, row in df_bribes.iterrows():
                gauge = clean_gauge_addr(row.get('gauge_address', ''))
                pool_title = str(row.get('pool_title', '')).strip()
                pool_name = str(row.get('pool_name', '')).strip()
                pool_identifier = pool_title if pool_title else pool_name
                
                if gauge and pool_identifier:
                    if gauge not in gauge_to_pool_name:
                        gauge_to_pool_name[gauge] = pool_identifier
            
            # Create mapping from pool names to pool_symbols (from pool_performance)
            def normalize_name(name):
                if pd.isna(name):
                    return ""
                # More aggressive normalization
                name_str = str(name).lower().strip()
                # Remove common prefixes/suffixes
                name_str = name_str.replace('(a)', '').replace('(b)', '').replace('(eth)', '')
                name_str = name_str.replace('eth:', '').replace('arb:', '').replace('base:', '').replace('pol:', '').replace('gno:', '')
                return name_str.strip()
            
            pool_performance['pool_symbol_normalized'] = pool_performance['pool_symbol'].apply(normalize_name)
            
            # Create reverse mapping: normalized pool_symbol -> original pool_symbol
            pool_symbol_map = {}
            for _, row in pool_performance.iterrows():
                pool_sym = row['pool_symbol']
                pool_sym_norm = normalize_name(pool_sym)
                if pool_sym_norm:
                    pool_symbol_map[pool_sym_norm] = pool_sym
            
            # Map gauges to pool names first
            votes_with_performance['matched_pool_name'] = votes_with_performance['gauge_address_normalized'].map(gauge_to_pool_name)
            
            # Normalize matched pool names
            votes_with_performance['matched_pool_name_normalized'] = votes_with_performance['matched_pool_name'].apply(normalize_name)
            
            # Try to match pool_name with pool_symbol using normalized names
            votes_with_performance['matched_pool'] = votes_with_performance['matched_pool_name_normalized'].map(pool_symbol_map)
            
            # If still no match, try using pool_name directly (might match exactly)
            unmatched_name = votes_with_performance['matched_pool'].isna() & votes_with_performance['matched_pool_name'].notna()
            if unmatched_name.sum() > 0:
                # Try exact match first
                exact_match = votes_with_performance.loc[unmatched_name].merge(
                    pool_performance[['pool_symbol']],
                    left_on='matched_pool_name',
                    right_on='pool_symbol',
                    how='left',
                    suffixes=('', '_exact')
                )
                votes_with_performance.loc[unmatched_name, 'matched_pool'] = exact_match['pool_symbol'].values
            
            # Now merge with pool_performance to get performance metrics
            perf_merge = votes_with_performance.merge(
                pool_performance,
                left_on='matched_pool',
                right_on='pool_symbol',
                how='left',
                suffixes=('', '_perf')
            )
            
            # Update performance columns
            for col in ['dao_profit_usd', 'protocol_fee_amount_usd', 'direct_incentives']:
                if col in perf_merge.columns:
                    votes_with_performance[col] = perf_merge[col].fillna(votes_with_performance[col])
        
        # Method 2: Fallback to name matching if gauge match didn't work well
        unmatched = votes_with_performance['matched_pool'].isna() | (votes_with_performance['matched_pool'] == '')
        if unmatched.sum() > 0:
            def normalize_name(name):
                if pd.isna(name):
                    return ""
                return str(name).lower().strip()
            
            # Ensure pool_performance has normalized column
            if 'pool_symbol_normalized' not in pool_performance.columns:
                pool_performance['pool_symbol_normalized'] = pool_performance['pool_symbol'].apply(normalize_name)
            
            votes_with_performance.loc[unmatched, 'symbol_normalized'] = votes_with_performance.loc[unmatched, 'symbol_clean'].apply(normalize_name)
            
            # Try name matching for unmatched rows
            name_match = votes_with_performance.loc[unmatched].merge(
                pool_performance,
                left_on='symbol_normalized',
                right_on='pool_symbol_normalized',
                how='left',
                suffixes=('', '_pool')
            )
            
            # Update matched_pool where it's missing
            if len(name_match) > 0:
                votes_with_performance.loc[unmatched, 'matched_pool'] = name_match['pool_symbol'].values
                
                # Update performance metrics for unmatched rows
                for col in ['dao_profit_usd', 'protocol_fee_amount_usd', 'direct_incentives']:
                    if col in name_match.columns:
                        votes_with_performance.loc[unmatched, col] = name_match[col].values
        
        # Classify pools
        votes_with_performance['pool_category'] = 'Other'
        votes_with_performance.loc[
            votes_with_performance['matched_pool'].isin(top_pools), 'pool_category'
        ] = 'Top 20 Pools'
        votes_with_performance.loc[
            votes_with_performance['matched_pool'].isin(worst_pools), 'pool_category'
        ] = 'Worst 20 Pools'
        
        # Filter to only matched pools
        matched_pools = votes_with_performance[votes_with_performance['matched_pool'].notna()].copy()
        
        # Debug info
        total_votes_matched = matched_pools['votes'].sum() if not matched_pools.empty else 0
        total_votes_all = votes_with_performance['votes'].sum()
        match_rate = (total_votes_matched / total_votes_all * 100) if total_votes_all > 0 else 0
        
        if not matched_pools.empty:
            st.info(f"ℹ️ Matched {len(matched_pools)} gauges ({match_rate:.1f}% of total votes) with pool performance data")
            col_perf1, col_perf2 = st.columns(2)
            
            with col_perf1:
                st.markdown("#### 📊 Votes Distribution: Top vs Worst Pools")
                
                # Aggregate by category
                category_votes = matched_pools.groupby('pool_category').agg({
                    'votes': 'sum',
                    'pct_votes': 'sum',
                    'matched_pool': 'nunique'
                }).reset_index()
                category_votes.columns = ['Category', 'Total Votes', 'Total Share', 'Pool Count']
                
                # Bar chart comparing votes
                fig_comparison = go.Figure()
                
                top_data = matched_pools[matched_pools['pool_category'] == 'Top 20 Pools']
                worst_data = matched_pools[matched_pools['pool_category'] == 'Worst 20 Pools']
                other_data = matched_pools[matched_pools['pool_category'] == 'Other']
                
                if not top_data.empty:
                    fig_comparison.add_trace(go.Bar(
                        name='Top 20 Pools',
                        x=['Top 20 Pools'],
                        y=[top_data['votes'].sum()],
                        marker_color='#67A2E1',
                        text=[f"{top_data['votes'].sum():,.0f}"],
                        textposition='outside'
                    ))
                
                if not worst_data.empty:
                    fig_comparison.add_trace(go.Bar(
                        name='Worst 20 Pools',
                        x=['Worst 20 Pools'],
                        y=[worst_data['votes'].sum()],
                        marker_color='#E9A97B',
                        text=[f"{worst_data['votes'].sum():,.0f}"],
                        textposition='outside'
                    ))
                
                if not other_data.empty:
                    fig_comparison.add_trace(go.Bar(
                        name='Other Pools',
                        x=['Other Pools'],
                        y=[other_data['votes'].sum()],
                        marker_color='#8B95A6',
                        text=[f"{other_data['votes'].sum():,.0f}"],
                        textposition='outside'
                    ))
                
                fig_comparison.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    title=dict(text="Total Votes by Pool Category", font=dict(color='white', size=16)),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title=""),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="Total Votes"),
                    height=400,
                    showlegend=True,
                    legend=dict(bgcolor='rgba(0,0,0,0.5)')
                )
                st.plotly_chart(fig_comparison, use_container_width=True)
                
                # Metrics
                col_met1, col_met2, col_met3 = st.columns(3)
                with col_met1:
                    top_votes_total = top_data['votes'].sum() if not top_data.empty else 0
                    st.metric("Top 20 Pools Votes", f"{top_votes_total:,.0f}")
                with col_met2:
                    worst_votes_total = worst_data['votes'].sum() if not worst_data.empty else 0
                    st.metric("Worst 20 Pools Votes", f"{worst_votes_total:,.0f}")
                with col_met3:
                    if top_votes_total > 0 and worst_votes_total > 0:
                        ratio = top_votes_total / worst_votes_total
                        st.metric("Top/Worst Ratio", f"{ratio:.2f}x")
                    else:
                        st.metric("Top/Worst Ratio", "N/A")
            
            with col_perf2:
                st.markdown("#### 📈 Average Votes per Pool")
                
                # Calculate averages
                avg_votes_data = []
                if not top_data.empty:
                    avg_votes_data.append({
                        'Category': 'Top 20 Pools',
                        'Avg Votes': top_data['votes'].mean(),
                        'Pool Count': len(top_data)
                    })
                if not worst_data.empty:
                    avg_votes_data.append({
                        'Category': 'Worst 20 Pools',
                        'Avg Votes': worst_data['votes'].mean(),
                        'Pool Count': len(worst_data)
                    })
                if not other_data.empty:
                    avg_votes_data.append({
                        'Category': 'Other Pools',
                        'Avg Votes': other_data['votes'].mean(),
                        'Pool Count': len(other_data)
                    })
                
                if avg_votes_data:
                    df_avg = pd.DataFrame(avg_votes_data)
                    
                    fig_avg = px.bar(
                        df_avg,
                        x='Category',
                        y='Avg Votes',
                        title="Average Votes per Pool by Category",
                        color='Category',
                        color_discrete_map={
                            'Top 20 Pools': '#67A2E1',
                            'Worst 20 Pools': '#E9A97B',
                            'Other Pools': '#8B95A6'
                        },
                        text='Avg Votes'
                    )
                    fig_avg.update_traces(
                        texttemplate='%{text:,.0f}',
                        textposition='outside'
                    )
                    fig_avg.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='white',
                        title=dict(font=dict(color='white', size=16)),
                        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title=""),
                        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="Average Votes"),
                        height=400,
                        showlegend=False
                    )
                    st.plotly_chart(fig_avg, use_container_width=True)
            
            # Scatter plot: DAO Profit vs Votes
            st.markdown("#### 💰 DAO Profit vs Votes Received")
            
            scatter_data = matched_pools[
                (matched_pools['dao_profit_usd'].notna()) & 
                (matched_pools['votes'] > 0)
            ].copy()
            
            if not scatter_data.empty:
                fig_scatter = px.scatter(
                    scatter_data,
                    x='dao_profit_usd',
                    y='votes',
                    color='pool_category',
                    size='votes',
                    hover_data=['symbol_clean', 'matched_pool', 'dao_profit_usd', 'votes'],
                    title="DAO Profit vs veBAL Votes",
                    labels={
                        'dao_profit_usd': 'DAO Profit (USD)',
                        'votes': 'veBAL Votes',
                        'pool_category': 'Pool Category'
                    },
                    color_discrete_map={
                        'Top 20 Pools': '#67A2E1',
                        'Worst 20 Pools': '#E9A97B',
                        'Other Pools': '#8B95A6'
                    },
                    size_max=20
                )
                fig_scatter.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    title=dict(font=dict(color='white', size=16)),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="DAO Profit (USD)"),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="veBAL Votes", type='log'),
                    legend=dict(bgcolor='rgba(0,0,0,0.5)'),
                    height=500
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Correlation analysis
                if len(scatter_data) > 1:
                    correlation = scatter_data['dao_profit_usd'].corr(scatter_data['votes'])
                    col_corr1, col_corr2, col_corr3 = st.columns(3)
                    with col_corr1:
                        st.metric("Correlation (Profit ↔ Votes)", f"{correlation:.3f}", 
                                 help="Correlation between DAO profit and votes received")
                    with col_corr2:
                        top_avg_profit = top_data['dao_profit_usd'].mean() if not top_data.empty and 'dao_profit_usd' in top_data.columns else 0
                        st.metric("Avg DAO Profit (Top 20)", f"${top_avg_profit:,.0f}")
                    with col_corr3:
                        worst_avg_profit = worst_data['dao_profit_usd'].mean() if not worst_data.empty and 'dao_profit_usd' in worst_data.columns else 0
                        st.metric("Avg DAO Profit (Worst 20)", f"${worst_avg_profit:,.0f}")
            
            # Top pools with votes table
            st.markdown("#### 📋 Top 20 Pools: Votes & Performance")
            if not top_data.empty:
                # Select available columns
                display_cols = ['symbol_clean', 'votes', 'pct_votes']
                if 'dao_profit_usd' in top_data.columns:
                    display_cols.append('dao_profit_usd')
                if 'protocol_fee_amount_usd' in top_data.columns:
                    display_cols.append('protocol_fee_amount_usd')
                if 'matched_pool' in top_data.columns:
                    display_cols.append('matched_pool')
                
                top_display = top_data.nlargest(20, 'votes')[display_cols].copy()
                
                # Rename columns
                col_mapping = {
                    'symbol_clean': 'Gauge',
                    'votes': 'Votes',
                    'pct_votes': 'Share %',
                    'dao_profit_usd': 'DAO Profit (USD)',
                    'protocol_fee_amount_usd': 'Revenue (USD)',
                    'matched_pool': 'Pool'
                }
                top_display.columns = [col_mapping.get(col, col) for col in top_display.columns]
                
                # Format numeric columns
                if 'Votes' in top_display.columns:
                    top_display['Votes'] = top_display['Votes'].apply(lambda x: f"{x:,.0f}")
                if 'Share %' in top_display.columns:
                    top_display['Share %'] = top_display['Share %'].apply(lambda x: f"{x*100:.2f}%")
                if 'DAO Profit (USD)' in top_display.columns:
                    top_display['DAO Profit (USD)'] = top_display['DAO Profit (USD)'].apply(
                        lambda x: f"${x:,.0f}" if pd.notna(x) and x != 0 else "N/A"
                    )
                if 'Revenue (USD)' in top_display.columns:
                    top_display['Revenue (USD)'] = top_display['Revenue (USD)'].apply(
                        lambda x: f"${x:,.0f}" if pd.notna(x) and x != 0 else "N/A"
                    )
                
                st.dataframe(top_display, use_container_width=True, hide_index=True)
            
            st.markdown("#### 📋 Worst 20 Pools: Votes & Performance")
            if not worst_data.empty:
                # Select available columns
                display_cols = ['symbol_clean', 'votes', 'pct_votes']
                if 'dao_profit_usd' in worst_data.columns:
                    display_cols.append('dao_profit_usd')
                if 'protocol_fee_amount_usd' in worst_data.columns:
                    display_cols.append('protocol_fee_amount_usd')
                if 'matched_pool' in worst_data.columns:
                    display_cols.append('matched_pool')
                
                worst_display = worst_data.nlargest(20, 'votes')[display_cols].copy()
                
                # Rename columns
                col_mapping = {
                    'symbol_clean': 'Gauge',
                    'votes': 'Votes',
                    'pct_votes': 'Share %',
                    'dao_profit_usd': 'DAO Profit (USD)',
                    'protocol_fee_amount_usd': 'Revenue (USD)',
                    'matched_pool': 'Pool'
                }
                worst_display.columns = [col_mapping.get(col, col) for col in worst_display.columns]
                
                # Format numeric columns
                if 'Votes' in worst_display.columns:
                    worst_display['Votes'] = worst_display['Votes'].apply(lambda x: f"{x:,.0f}")
                if 'Share %' in worst_display.columns:
                    worst_display['Share %'] = worst_display['Share %'].apply(lambda x: f"{x*100:.2f}%")
                if 'DAO Profit (USD)' in worst_display.columns:
                    worst_display['DAO Profit (USD)'] = worst_display['DAO Profit (USD)'].apply(
                        lambda x: f"${x:,.0f}" if pd.notna(x) and x != 0 else "N/A"
                    )
                if 'Revenue (USD)' in worst_display.columns:
                    worst_display['Revenue (USD)'] = worst_display['Revenue (USD)'].apply(
                        lambda x: f"${x:,.0f}" if pd.notna(x) and x != 0 else "N/A"
                    )
                
                st.dataframe(worst_display, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ Could not match pools with gauges. Pool names in main data may not match gauge names in votes data.")
    else:
        st.info("ℹ️ Main data not available. Cannot compare votes with pool performance.")
except Exception as e:
    st.warning(f"⚠️ Could not load pool performance data: {str(e)}")
    st.info("This analysis requires the main financial data file to be available.")

# Additional analysis section
st.markdown("---")
st.markdown("### 📊 Additional Statistics")

col_add1, col_add2, col_add3, col_add4 = st.columns(4)

with col_add1:
    # Gauges with significant share
    significant = len(df_votes[df_votes['pct_votes'] >= 0.01])  # >= 1%
    st.metric("Gauges with ≥1% share", f"{significant}")

with col_add2:
    # Average votes per gauge (excluding zeros)
    active_gauges = df_votes[df_votes['votes'] > 0]
    avg_active = active_gauges['votes'].mean() if len(active_gauges) > 0 else 0
    st.metric("Avg Votes (Active Gauges)", f"{avg_active:,.0f}")

with col_add3:
    # Vote efficiency (top gauge vs median)
    efficiency_ratio = top_gauge_votes / median_votes if median_votes > 0 else 0
    st.metric("Top/Median Ratio", f"{efficiency_ratio:.1f}x")

with col_add4:
    # Total unique gauges
    st.metric("Total Unique Gauges", f"{total_gauges}")
