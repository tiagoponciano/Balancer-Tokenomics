import streamlit as st
import utils
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Emission Impact Analysis", layout="wide", page_icon="📉")
utils.inject_css()

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
    if st.button("TOP 20", key="btn_top20_emission"):
        st.session_state.pool_filter_mode_emission = 'top20'
        st.session_state.selected_pools_emission = []

with col_btn2:
    if st.button("WORST 20", key="btn_worst20_emission"):
        st.session_state.pool_filter_mode_emission = 'worst20'
        st.session_state.selected_pools_emission = []

if st.session_state.pool_filter_mode_emission == 'worst20':
    filter_pools = sorted([str(p) for p in utils.get_worst_pools(df, n=20)])
    filter_label = "Select from WORST 20 Pools"
else:
    filter_pools = sorted([str(p) for p in utils.get_top_pools(df, n=20)])
    filter_label = "Select from TOP 20 Pools"

valid_sel = [p for p in st.session_state.selected_pools_emission if p in filter_pools]
default_selection = valid_sel if valid_sel else []

if st.sidebar.button("Selecionar tudo", key="btn_select_all_emission"):
    st.session_state.selected_pools_emission = filter_pools
    st.rerun()

selected_pools = st.sidebar.multiselect(
    filter_label,
    options=filter_pools,
    default=default_selection,
    help="Select specific pools to view individual analysis"
)

st.session_state.selected_pools_emission = selected_pools

filter_by_pools = len(selected_pools) > 0

if filter_by_pools:
    df_display = df_sim[df_sim['pool_symbol'].isin(selected_pools)].copy()
    st.info(f"📊 Showing analysis for {len(selected_pools)} selected pool(s)")
else:
    df_display = df_sim.copy()

st.markdown('<div class="page-title">Emission Reduction Impact Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Simulate emission reduction scenarios and analyze impact on legitimate vs mercenary pools</div>', unsafe_allow_html=True)

st.markdown("---")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📉 Emission Reduction Scenarios")

reduction_50 = st.sidebar.checkbox("50% Reduction (Keep 50% of emissions)", value=True)
reduction_70 = st.sidebar.checkbox("70% Reduction (Keep 30% of emissions)", value=True)

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

st.dataframe(baseline, use_container_width=True, hide_index=False)

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
    
    scenario_data.append({
        'name': scenario_name,
        'data': scenario_summary
    })
    
    st.markdown(f"#### {scenario_name}")
    st.dataframe(scenario_summary, use_container_width=True, hide_index=False)
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
