import streamlit as st
import utils
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Emission Impact Analysis", layout="wide", page_icon="📉")

# Check authentication
if not utils.check_authentication():
    st.stop()

utils.inject_css()

# Script para aplicar IDs específicos aos botões
import streamlit.components.v1 as components

components.html("""
<script>
console.log('[Button IDs] Script carregado via components.html (emission_impact.py)!');

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

if 'selected_pools_emission' not in st.session_state:
    st.session_state.selected_pools_emission = []
if 'pool_filter_mode_emission' not in st.session_state:
    st.session_state.pool_filter_mode_emission = 'top20'

col_btn1, col_btn2 = st.sidebar.columns(2)

with col_btn1:
    if st.button("Top 20", key="btn_top20_emission"):
        old_mode = st.session_state.pool_filter_mode_emission
        st.session_state.pool_filter_mode_emission = 'top20'
        # Clear selections when mode changes
        if old_mode != 'top20':
            st.session_state.selected_pools_emission = []
        st.rerun()

with col_btn2:
    if st.button("Worst 20", key="btn_worst20_emission"):
        old_mode = st.session_state.pool_filter_mode_emission
        st.session_state.pool_filter_mode_emission = 'worst20'
        # Clear selections when mode changes
        if old_mode != 'worst20':
            st.session_state.selected_pools_emission = []
        st.rerun()

if st.session_state.pool_filter_mode_emission == 'worst20':
    filter_pools = sorted([str(p) for p in utils.get_worst_pools(df, n=20)])
    filter_label = "Select from Worst 20 Pools"
else:
    filter_pools = sorted([str(p) for p in utils.get_top_pools(df, n=20)])
    filter_label = "Select from Top 20 Pools"

# Clear invalid selections when filter mode changes
valid_sel = [p for p in st.session_state.selected_pools_emission if p in filter_pools]
if len(valid_sel) != len(st.session_state.selected_pools_emission):
    st.session_state.selected_pools_emission = valid_sel

# Initialize default selection from session state if valid
default_selection = []
if st.session_state.selected_pools_emission:
    # Only use session state if all selections are valid for current filter
    if all(p in filter_pools for p in st.session_state.selected_pools_emission):
        default_selection = st.session_state.selected_pools_emission

if st.sidebar.button("Select All", key="btn_select_all_emission"):
    st.session_state.selected_pools_emission = filter_pools.copy()
    default_selection = filter_pools.copy()
    st.rerun()

# Use dynamic key based on filter mode to force update when mode changes
multiselect_key = f"multiselect_pools_emission_{st.session_state.pool_filter_mode_emission}"

selected_pools = st.sidebar.multiselect(
    filter_label,
    options=filter_pools,
    default=default_selection,
    help="Select specific pools to view individual analysis",
    key=multiselect_key
)

# Always sync session state with current selection
st.session_state.selected_pools_emission = list(selected_pools) if selected_pools else []

filter_by_pools = len(selected_pools) > 0

if filter_by_pools:
    df_display = df_sim[df_sim['pool_symbol'].isin(selected_pools)].copy()
    st.info(f"📊 Showing analysis for {len(selected_pools)} selected pool(s)")
else:
    df_display = df_sim.copy()

# Page Header with logout button
col_title, col_logout = st.columns([1, 0.1])
with col_title:
    st.markdown('<div class="page-title">Emission Reduction Impact Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Simulate emission reduction scenarios and analyze impact on legitimate vs mercenary pools</div>', unsafe_allow_html=True)
with col_logout:
    utils.show_logout_button()

st.markdown("---")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📉 Emission Reduction Scenarios")

reduction_50 = st.sidebar.checkbox("50% Reduction (Keep 50% of emissions)", value=True)
reduction_70 = st.sidebar.checkbox("70% Reduction (Keep 30% of emissions)", value=True)

# ============================================================================
# EMISSIONS ANALYSIS: LEGITIMATE VS MERCENARY
# ============================================================================
st.markdown("### 📊 Emissions Analysis: Legitimate vs Mercenary Pools")

# Determine which BAL column to use
bal_col = 'sim_bal_emitted' if 'sim_bal_emitted' in df_display.columns else 'bal_emited_votes'

# Aggregate emissions by pool category
emissions_by_category = df_display.groupby('pool_category').agg({
    bal_col: 'sum',
    'pool_symbol': 'nunique'
}).round(2)
emissions_by_category.columns = ['Total BAL Emitted', 'Pool Count']

# Calculate percentages
total_emissions = emissions_by_category['Total BAL Emitted'].sum()
if total_emissions > 0:
    emissions_by_category['Percentage'] = (emissions_by_category['Total BAL Emitted'] / total_emissions * 100).round(2)
else:
    emissions_by_category['Percentage'] = 0

# Display aggregated values
col1, col2, col3, col4 = st.columns(4)

legitimate_emissions = emissions_by_category.loc['Legitimate', 'Total BAL Emitted'] if 'Legitimate' in emissions_by_category.index else 0
legitimate_pct = emissions_by_category.loc['Legitimate', 'Percentage'] if 'Legitimate' in emissions_by_category.index else 0
mercenary_emissions = emissions_by_category.loc['Mercenary', 'Total BAL Emitted'] if 'Mercenary' in emissions_by_category.index else 0
mercenary_pct = emissions_by_category.loc['Mercenary', 'Percentage'] if 'Mercenary' in emissions_by_category.index else 0

with col1:
    st.metric(
        "Legitimate Emissions",
        f"{legitimate_emissions:,.0f} BAL",
        f"{legitimate_pct:.1f}%",
        help="Total BAL emitted to legitimate pools"
    )

with col2:
    st.metric(
        "Mercenary Emissions",
        f"{mercenary_emissions:,.0f} BAL",
        f"{mercenary_pct:.1f}%",
        help="Total BAL emitted to mercenary pools"
    )

with col3:
    undefined_emissions = emissions_by_category.loc['Undefined', 'Total BAL Emitted'] if 'Undefined' in emissions_by_category.index else 0
    undefined_pct = emissions_by_category.loc['Undefined', 'Percentage'] if 'Undefined' in emissions_by_category.index else 0
    st.metric(
        "Undefined Emissions",
        f"{undefined_emissions:,.0f} BAL",
        f"{undefined_pct:.1f}%",
        help="Total BAL emitted to undefined pools"
    )

with col4:
    st.metric(
        "Total Emissions",
        f"{total_emissions:,.0f} BAL",
        help="Total BAL emitted across all pools"
    )

# Display detailed table
st.markdown("#### 📋 Detailed Breakdown")
emissions_display = emissions_by_category.copy()
emissions_display['Total BAL Emitted'] = emissions_display['Total BAL Emitted'].apply(lambda x: f"{x:,.0f}")
emissions_display['Percentage'] = emissions_display['Percentage'].apply(lambda x: f"{x:.2f}%")
st.dataframe(emissions_display, use_container_width=True, hide_index=False)

# Temporal chart for emissions by category
st.markdown("#### 📈 Emissions Over Time: Legitimate vs Mercenary")

# Prepare temporal data
df_display['month'] = df_display['block_date'].dt.to_period('M').dt.start_time
emissions_temporal = df_display.groupby(['month', 'pool_category']).agg({
    bal_col: 'sum'
}).reset_index()

# Pivot for chart
pivot_emissions = emissions_temporal.pivot(index='month', columns='pool_category', values=bal_col).fillna(0)

# Create area chart
fig_legit_mercenary = go.Figure()

colors = {
    'Legitimate': '#2ecc71',
    'Mercenary': '#e74c3c',
    'Undefined': '#95a5a6'
}

for category in pivot_emissions.columns:
    fig_legit_mercenary.add_trace(go.Scatter(
        x=pivot_emissions.index,
        y=pivot_emissions[category],
        mode='lines',
        name=category,
        fill='tonexty' if category != pivot_emissions.columns[0] else 'tozeroy',
        stackgroup='one',
        line=dict(color=colors.get(category, '#3498db'), width=1.5),
        hovertemplate=f'<b>{category}</b><br>%{{x|%b %Y}}<br>%{{y:,.0f}} BAL<extra></extra>'
    ))

fig_legit_mercenary.update_layout(
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    height=450,
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
        title=dict(text="BAL Emitted", font=dict(size=12, color='#8B95A6')),
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

st.plotly_chart(fig_legit_mercenary, use_container_width=True, key="emissions_legit_mercenary")

st.markdown("---")

# ============================================================================
# EMISSIONS ANALYSIS: CORE VS NON-CORE POOLS
# ============================================================================
st.markdown("### 📊 Emissions Analysis: Core Pools vs Non-Core Pools")

# Aggregate emissions by core pool status
emissions_by_core = df_display.groupby('is_core_pool').agg({
    bal_col: 'sum',
    'pool_symbol': 'nunique'
}).round(2)
# Map index values safely
mapping = {1: 'Core Pools', 0: 'Non-Core Pools'}
emissions_by_core.index = [mapping.get(x, f'Unknown ({x})') for x in emissions_by_core.index]
emissions_by_core.columns = ['Total BAL Emitted', 'Pool Count']

# Calculate percentages
total_emissions_core = emissions_by_core['Total BAL Emitted'].sum()
if total_emissions_core > 0:
    emissions_by_core['Percentage'] = (emissions_by_core['Total BAL Emitted'] / total_emissions_core * 100).round(2)
else:
    emissions_by_core['Percentage'] = 0

# Display aggregated values
col1, col2, col3 = st.columns(3)

core_emissions = emissions_by_core.loc['Core Pools', 'Total BAL Emitted'] if 'Core Pools' in emissions_by_core.index else 0
core_pct = emissions_by_core.loc['Core Pools', 'Percentage'] if 'Core Pools' in emissions_by_core.index else 0
noncore_emissions = emissions_by_core.loc['Non-Core Pools', 'Total BAL Emitted'] if 'Non-Core Pools' in emissions_by_core.index else 0
noncore_pct = emissions_by_core.loc['Non-Core Pools', 'Percentage'] if 'Non-Core Pools' in emissions_by_core.index else 0

with col1:
    st.metric(
        "Core Pools Emissions",
        f"{core_emissions:,.0f} BAL",
        f"{core_pct:.1f}%",
        help="Total BAL emitted to core pools"
    )

with col2:
    st.metric(
        "Non-Core Pools Emissions",
        f"{noncore_emissions:,.0f} BAL",
        f"{noncore_pct:.1f}%",
        help="Total BAL emitted to non-core pools"
    )

with col3:
    st.metric(
        "Total Emissions",
        f"{total_emissions_core:,.0f} BAL",
        help="Total BAL emitted across all pools"
    )

# Display detailed table
st.markdown("#### 📋 Detailed Breakdown")
emissions_core_display = emissions_by_core.copy()
emissions_core_display['Total BAL Emitted'] = emissions_core_display['Total BAL Emitted'].apply(lambda x: f"{x:,.0f}")
emissions_core_display['Percentage'] = emissions_core_display['Percentage'].apply(lambda x: f"{x:.2f}%")
st.dataframe(emissions_core_display, use_container_width=True, hide_index=False)

# Temporal chart for emissions by core status
st.markdown("#### 📈 Emissions Over Time: Core vs Non-Core Pools")

# Prepare temporal data
emissions_temporal_core = df_display.groupby(['month', 'is_core_pool']).agg({
    bal_col: 'sum'
}).reset_index()
mapping_core = {1: 'Core Pools', 0: 'Non-Core Pools'}
emissions_temporal_core['is_core_pool'] = emissions_temporal_core['is_core_pool'].apply(lambda x: mapping_core.get(x, f'Unknown ({x})'))

# Pivot for chart
pivot_emissions_core = emissions_temporal_core.pivot(index='month', columns='is_core_pool', values=bal_col).fillna(0)

# Create area chart
fig_core_noncore = go.Figure()

core_colors = {
    'Core Pools': '#67A2E1',
    'Non-Core Pools': '#E9A97B'
}

for pool_type in pivot_emissions_core.columns:
    fig_core_noncore.add_trace(go.Scatter(
        x=pivot_emissions_core.index,
        y=pivot_emissions_core[pool_type],
        mode='lines',
        name=pool_type,
        fill='tonexty' if pool_type != pivot_emissions_core.columns[0] else 'tozeroy',
        stackgroup='one',
        line=dict(color=core_colors.get(pool_type, '#3498db'), width=1.5),
        hovertemplate=f'<b>{pool_type}</b><br>%{{x|%b %Y}}<br>%{{y:,.0f}} BAL<extra></extra>'
    ))

fig_core_noncore.update_layout(
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    height=450,
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
        title=dict(text="BAL Emitted", font=dict(size=12, color='#8B95A6')),
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

st.plotly_chart(fig_core_noncore, use_container_width=True, key="emissions_core_noncore")

st.markdown("---")

# ============================================================================
# CURRENT STATE (BASELINE) - Existing section
# ============================================================================
st.markdown("### 📊 Current State (Baseline)")

if 'sim_bal_emitted' in df_display.columns:
    baseline = df_display.groupby('pool_category').agg({
        'sim_bal_emitted': 'sum',
        'direct_incentives': 'sum',
        'protocol_fee_amount_usd': 'sum',
        'dao_profit_usd': 'sum'
    }).round(2)
    baseline.columns = ['BAL Emitted', 'Total Incentives', 'Total Revenue', 'Total DAO Profit']
else:
    baseline = df_display.groupby('pool_category').agg({
        'bal_emited_votes': 'sum',
        'direct_incentives': 'sum',
        'protocol_fee_amount_usd': 'sum',
        'dao_profit_usd': 'sum'
    }).round(2)
    baseline.columns = ['BAL Emitted', 'Total Incentives', 'Total Revenue', 'Total DAO Profit']

# Format monetary columns
baseline_display = baseline.copy()
for col in ['Total Incentives', 'Total Revenue', 'Total DAO Profit']:
    if col in baseline_display.columns:
        baseline_display[col] = baseline_display[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")

st.dataframe(baseline_display, use_container_width=True, hide_index=False)

st.markdown("---")

scenarios = []
if reduction_50:
    scenarios.append(('50% Reduction', 0.5))
if reduction_70:
    scenarios.append(('70% Reduction', 0.3))

if not scenarios:
    st.info("Please select at least one reduction scenario in the sidebar.")
    st.stop()

st.markdown("### 📈 Impact Analysis by Scenario")

scenario_data = []

for scenario_name, reduction_factor in scenarios:
    df_scenario = utils.calculate_emission_reduction_impact(df_display, reduction_factor)
    
    agg_dict = {
        'reduced_incentives': 'sum',
        'protocol_fee_amount_usd': 'sum',
        'new_dao_profit': 'sum',
        'direct_incentives': 'sum'
    }
    
    if 'reduced_bal_emitted' in df_scenario.columns:
        agg_dict['reduced_bal_emitted'] = 'sum'
    if 'sim_bal_emitted' in df_scenario.columns:
        agg_dict['sim_bal_emitted'] = 'sum'
    elif 'bal_emited_votes' in df_scenario.columns:
        agg_dict['bal_emited_votes'] = 'sum'
    
    scenario_summary = df_scenario.groupby('pool_category').agg(agg_dict).round(2)
    
    if 'reduced_bal_emitted' in scenario_summary.columns:
        bal_col = 'reduced_bal_emitted'
        orig_bal_col = 'sim_bal_emitted' if 'sim_bal_emitted' in scenario_summary.columns else 'bal_emited_votes'
        scenario_summary['bal_reduction'] = scenario_summary[orig_bal_col] - scenario_summary[bal_col]
    else:
        scenario_summary['bal_reduction'] = 0
    
    scenario_summary['incentive_reduction'] = scenario_summary['direct_incentives'] - scenario_summary['reduced_incentives']
    scenario_summary['profit_change'] = scenario_summary['new_dao_profit'] - baseline['Total DAO Profit']
    scenario_summary['profit_change_pct'] = (scenario_summary['profit_change'] / baseline['Total DAO Profit'] * 100).round(2).fillna(0)
    
    if 'bal_reduction' in scenario_summary.columns and scenario_summary['bal_reduction'].sum() > 0:
        scenario_summary.columns = ['Reduced Incentives', 'Total Revenue', 'New DAO Profit', 'Original Incentives', 'Reduced BAL', 'Original BAL', 'BAL Reduction', 'Incentive Reduction', 'Profit Change', 'Profit Change %']
    else:
        scenario_summary.columns = ['Reduced Incentives', 'Total Revenue', 'New DAO Profit', 'Original Incentives', 'Incentive Reduction', 'Profit Change', 'Profit Change %']
    
    # Format monetary columns for display
    scenario_summary_display = scenario_summary.copy()
    monetary_cols = ['Reduced Incentives', 'Total Revenue', 'New DAO Profit', 'Original Incentives', 'Incentive Reduction', 'Profit Change']
    for col in monetary_cols:
        if col in scenario_summary_display.columns:
            scenario_summary_display[col] = scenario_summary_display[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
    
    # Format percentage column
    if 'Profit Change %' in scenario_summary_display.columns:
        scenario_summary_display['Profit Change %'] = scenario_summary_display['Profit Change %'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "0.00%")
    
    scenario_data.append({
        'name': scenario_name,
        'data': scenario_summary
    })
    
    st.markdown(f"#### {scenario_name}")
    st.dataframe(scenario_summary_display, use_container_width=True, hide_index=False)
    st.markdown("---")

st.markdown("### 📊 Comparison Charts")

comparison_data = []
for scenario in scenario_data:
    for category in scenario['data'].index:
        comparison_data.append({
            'Scenario': scenario['name'],
            'Category': category,
            'DAO Profit': scenario['data'].loc[category, 'New DAO Profit']
        })

for category in baseline.index:
    comparison_data.append({
        'Scenario': 'Baseline',
        'Category': category,
        'DAO Profit': baseline.loc[category, 'Total DAO Profit']
    })

df_comparison = pd.DataFrame(comparison_data)

if len(df_comparison) > 0:
    pivot_profit = df_comparison.pivot(index='Category', columns='Scenario', values='DAO Profit')
    
    fig1 = go.Figure()
    
    scenarios_list = ['Baseline'] + [s['name'] for s in scenario_data]
    
    for scenario in scenarios_list:
        if scenario in pivot_profit.columns:
            fig1.add_trace(go.Bar(
                name=scenario,
                x=list(pivot_profit.index),
                y=pivot_profit[scenario],
                marker_line_width=0
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
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.05,
            xanchor="left",
            x=0,
            font=dict(size=11, color='#8B95A6')
        )
    )
    
    st.plotly_chart(fig1, use_container_width=True, key="emission_comparison")

if filter_by_pools:
    st.markdown("---")
    st.markdown("### 📋 Selected Pools Impact")
    
    for idx, pool in enumerate(selected_pools):
        pool_data = df_display[df_display['pool_symbol'] == pool]
        if len(pool_data) > 0:
            with st.expander(f"{pool}"):
                baseline_pool = pool_data['dao_profit_usd'].sum()
                baseline_bal = pool_data['sim_bal_emitted'].sum() if 'sim_bal_emitted' in pool_data.columns else pool_data['bal_emited_votes'].sum()
                baseline_inc = pool_data['direct_incentives'].sum()
                
                col_base1, col_base2, col_base3 = st.columns(3)
                col_base1.metric("Baseline DAO Profit", f"${baseline_pool:,.0f}")
                col_base2.metric("Baseline BAL Emitted", f"{baseline_bal:,.0f}")
                col_base3.metric("Baseline Incentives", f"${baseline_inc:,.0f}")
                
                st.markdown("---")
                
                for scenario_name, reduction_factor in scenarios:
                    df_scenario = utils.calculate_emission_reduction_impact(pool_data, reduction_factor)
                    new_profit = df_scenario['new_dao_profit'].sum()
                    profit_change = new_profit - baseline_pool
                    
                    reduced_bal = df_scenario['reduced_bal_emitted'].sum() if 'reduced_bal_emitted' in df_scenario.columns else baseline_bal * reduction_factor
                    bal_reduction = baseline_bal - reduced_bal
                    
                    reduced_inc = df_scenario['reduced_incentives'].sum()
                    inc_reduction = baseline_inc - reduced_inc
                    
                    st.markdown(f"**{scenario_name}**")
                    col_s1, col_s2, col_s3 = st.columns(3)
                    with col_s1:
                        st.metric("New DAO Profit", f"${new_profit:,.0f}", f"${profit_change:,.0f}")
                    with col_s2:
                        st.metric("Reduced BAL", f"{reduced_bal:,.0f}", f"-{bal_reduction:,.0f}")
                    with col_s3:
                        st.metric("Reduced Incentives", f"${reduced_inc:,.0f}", f"-${inc_reduction:,.0f}")
                    
                    if idx < len(selected_pools) - 1 or scenario_name != scenarios[-1][0]:
                        st.markdown("---")
