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

# Script para aplicar IDs específicos aos botões
import streamlit.components.v1 as components

components.html("""
<script>
console.log('[Button IDs] Script carregado via components.html (vebal_votes.py)!');

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

# Load main data for pool filtering
df = utils.load_data()

# Sidebar filters
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Pool Selection")

# Initialize session state - default to 'all' (show everything)
if 'pool_filter_mode_votes' not in st.session_state:
    st.session_state.pool_filter_mode_votes = 'all'  # Default: show all pools

col_btn1, col_btn2 = st.sidebar.columns(2)

with col_btn1:
    if st.button("Top 20", key="btn_top20_votes"):
        st.session_state.pool_filter_mode_votes = 'top20'
        st.rerun()

with col_btn2:
    if st.button("Worst 20", key="btn_worst20_votes"):
        st.session_state.pool_filter_mode_votes = 'worst20'
        st.rerun()

# Show "Select All" button only when a filter is active (top20 or worst20)
if st.session_state.pool_filter_mode_votes in ['top20', 'worst20']:
    if st.sidebar.button("Select All", key="btn_select_all_votes"):
        st.session_state.pool_filter_mode_votes = 'all'
        st.rerun()

# Helper function to load aggregated CSV (same as bribes_analysis.py)
def load_aggregated_csv(filename):
    """Load aggregated CSV file trying multiple possible paths"""
    import os
    cwd = os.getcwd()
    
    file_paths = [
        os.path.join(cwd, 'data', filename),
        os.path.abspath(os.path.join(cwd, 'data', filename)),
        os.path.abspath(os.path.join(cwd, '..', 'data', filename)),
        os.path.abspath(os.path.join(cwd, '..', '..', 'data', filename)),
        f'data/{filename}',
        filename
    ]
    
    for path in file_paths:
        try:
            abs_path = os.path.abspath(path) if not os.path.isabs(path) else path
            if os.path.exists(abs_path) and os.path.getsize(abs_path) > 0:
                return pd.read_csv(abs_path)
        except Exception:
            continue
    return None

# Normalize gauge address for matching
def normalize_gauge_addr(addr):
    """Normalize gauge address for matching"""
    if pd.isna(addr):
        return ""
    addr_str = str(addr).lower().strip()
    if addr_str.startswith('0x'):
        return addr_str
    return addr_str

# Filter votes data based on mode - using votes aggregated CSVs (based on dao_profit_usd)
df_display = df_votes.copy()

# Normalize gauge addresses in df_display for matching
df_display['gauge_address_normalized'] = df_display['gauge_address'].apply(normalize_gauge_addr)

if st.session_state.pool_filter_mode_votes == 'top20':
    # Load aggregated top 20 CSV from bribes (has gauge_address -> pool_symbol mapping)
    csv_data = load_aggregated_csv('top20_pools_bribes_aggregated.csv')
    if csv_data is not None and not csv_data.empty and 'gauge_address' in csv_data.columns:
        # Get list of gauge addresses from CSV
        csv_data['gauge_address_normalized'] = csv_data['gauge_address'].apply(normalize_gauge_addr)
        top_gauges = set(csv_data['gauge_address_normalized'].dropna().unique())
        
        # Filter votes for gauges that match top pools
        df_filtered = df_display[df_display['gauge_address_normalized'].isin(top_gauges)].copy()
        matched_count = len(df_filtered)
        if matched_count > 0:
            df_display = df_filtered
            st.info(f"📊 Showing analysis for Top 20 Pools filter ({matched_count} matched gauges from top 20 pools)")
        else:
            st.warning(f"⚠️ No gauges matched for Top 20 Pools. Showing all gauges instead.")
            df_display = df_votes.copy()
            total_gauges = len(df_display)
            st.info(f"📊 Showing analysis for all gauges ({total_gauges} gauges)")
    else:
        st.warning("⚠️ Top 20 aggregated CSV not found. Showing all gauges.")
        total_gauges = len(df_display)
        st.info(f"📊 Showing analysis for all gauges ({total_gauges} gauges)")
elif st.session_state.pool_filter_mode_votes == 'worst20':
    # Load aggregated worst 20 CSV from bribes (has gauge_address -> pool_symbol mapping)
    csv_data = load_aggregated_csv('worst20_pools_bribes_aggregated.csv')
    if csv_data is not None and not csv_data.empty and 'gauge_address' in csv_data.columns:
        # Get list of gauge addresses from CSV
        csv_data['gauge_address_normalized'] = csv_data['gauge_address'].apply(normalize_gauge_addr)
        worst_gauges = set(csv_data['gauge_address_normalized'].dropna().unique())
        
        # Filter votes for gauges that match worst pools
        df_filtered = df_display[df_display['gauge_address_normalized'].isin(worst_gauges)].copy()
        matched_count = len(df_filtered)
        if matched_count > 0:
            df_display = df_filtered
            st.info(f"📊 Showing analysis for Worst 20 Pools filter ({matched_count} matched gauges from worst 20 pools)")
        else:
            st.warning(f"⚠️ No gauges matched for Worst 20 Pools. Showing all gauges instead.")
            df_display = df_votes.copy()
            total_gauges = len(df_display)
            st.info(f"📊 Showing analysis for all gauges ({total_gauges} gauges)")
    else:
        st.warning("⚠️ Worst 20 aggregated CSV not found. Showing all gauges.")
        total_gauges = len(df_display)
        st.info(f"📊 Showing analysis for all gauges ({total_gauges} gauges)")
else:
    # 'all' mode - show everything
    total_gauges = len(df_display)
    st.info(f"📊 Showing analysis for all gauges ({total_gauges} gauges)")

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

total_votes = df_display['votes'].sum()
total_gauges = len(df_display)
top_gauge_votes = df_display['votes'].max()
top_gauge_pct = df_display['pct_votes'].max() * 100

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
    top_n = df_display.nlargest(n_gauges, 'votes')
    
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
        top_5 = df_display.nlargest(5, 'votes')
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
            x=df_display['votes'],
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
            y=df_display['votes'],
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
        st.metric("Mean Votes", f"{df_display['votes'].mean():,.0f}")
    with col_stat2:
        st.metric("Median Votes", f"{df_display['votes'].median():,.0f}")
    with col_stat3:
        st.metric("Std Deviation", f"{df_display['votes'].std():,.0f}")
    with col_stat4:
        st.metric("Min Votes", f"{df_display['votes'].min():,.2f}")
    with col_stat5:
        st.metric("Max Votes", f"{df_display['votes'].max():,.0f}")
    
    # Percentiles
    st.markdown("#### Percentiles")
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    percentile_data = {f'P{p}': np.percentile(df_display['votes'], p) for p in percentiles}
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
        top_n_pie = df_display.nlargest(n_top_pie, 'votes')
        others_votes = df_display['votes'].sum() - top_n_pie['votes'].sum()
        
        pie_data = top_n_pie.copy()
        if others_votes > 0:
            others_row = pd.DataFrame({
                'symbol_clean': ['Others'],
                'votes': [others_votes],
                'pct_votes': [others_votes / df_display['votes'].sum()]
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
        top_n_treemap = df_display.nlargest(15, 'votes')
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
    df_sorted = df_display.sort_values('votes', ascending=False).copy()
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
    
    display_df = df_display.copy()
    
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
    st.caption(f"Showing {len(display_table)} of {len(df_display)} gauges")
    
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

col_insight1, col_insight2 = st.columns(2)

with col_insight1:
    st.markdown("#### 📊 Concentration Analysis")
    top_5_pct = (df_display.nlargest(5, 'votes')['votes'].sum() / total_votes * 100)
    top_10_pct = (df_display.nlargest(10, 'votes')['votes'].sum() / total_votes * 100)
    top_20_pct = (df_display.nlargest(20, 'votes')['votes'].sum() / total_votes * 100)
    
    st.metric("Top 5 Gauges Share", f"{top_5_pct:.1f}%")
    st.metric("Top 10 Gauges Share", f"{top_10_pct:.1f}%")
    st.metric("Top 20 Gauges Share", f"{top_20_pct:.1f}%")
    
    # Gini coefficient approximation
    df_sorted_votes = df_display.sort_values('votes', ascending=True)
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
    st.markdown("#### 🎯 Power Distribution")
    
    # Calculate how many gauges control X% of votes
    df_sorted_power = df_display.sort_values('votes', ascending=False)
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
    hhi = sum((df_display['pct_votes'] * 100) ** 2)
    st.metric("HHI Index", f"{hhi:.0f}", help="Higher HHI = more concentration (0-10000 scale)")
    
    if hhi > 2500:
        st.error("🔴 **High market concentration** (HHI > 2500)")
    elif hhi > 1500:
        st.warning("🟡 **Moderate concentration** (HHI 1500-2500)")
    else:
        st.success("🟢 **Low concentration** (HHI < 1500)")

