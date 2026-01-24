import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# Prevent this file from being rendered as a Streamlit page
# This is a utility module, not a page - it should only be imported
# Check if this is being run as a page (has page config or is being accessed directly)
try:
    # If this file is accessed as a page, show a message and stop
    if hasattr(st, '_is_running_with_streamlit') and st._is_running_with_streamlit:
        # Check if we're in the main execution context (not imported)
        import inspect
        frame = inspect.currentframe()
        # If called directly (not imported), show message
        if frame and frame.f_back and 'streamlit' in str(frame.f_back.f_code.co_filename):
            st.info("ℹ️ **utils.py** é um módulo de funções utilitárias, não uma página.\n\nUse as páginas do menu lateral: Home, Bribes Analysis, Pool Classification, etc.")
            st.stop()
except:
    pass

def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .stApp {
            background: linear-gradient(135deg, #0F1419 0%, #1A1F26 100%);
            font-family: 'Inter', sans-serif;
        }
        
        .block-container {
            padding-top: 3rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            letter-spacing: -0.02em;
            color: #FFFFFF;
        }
        
        .page-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #67A2E1 0%, #B1ACF1 50%, #E9A97B 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            letter-spacing: -0.03em;
        }
        
        .page-subtitle {
            font-size: 1rem;
            color: #8B95A6;
            font-weight: 400;
            margin-bottom: 2rem;
        }
        
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1A1F26 0%, #151A20 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        
        div[data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
        }
        
        div[data-testid="metric-container"] label {
            color: #8B95A6 !important;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            font-size: 1.75rem;
            font-weight: 700;
        }
        
        div[data-testid="metric-container"] div[data-testid="stMetricDelta"] {
            font-weight: 500;
        }
        
        .stSlider > div > div > div[role="slider"] {
            background-color: #67A2E1 !important;
        }
        
        .stSlider > div > div > div > div {
            background-color: #B1ACF1 !important;
        }
        
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.1) 50%, transparent 100%);
            margin: 2rem 0;
        }
        
        section[data-testid="stSidebar"] hr {
            margin: 0.4rem 0 !important;
        }
        
        .stInfo {
            background: rgba(103, 162, 225, 0.1);
            border: 1px solid rgba(103, 162, 225, 0.2);
            border-radius: 8px;
        }
        
        .stCaption {
            color: #6B7280;
            font-size: 0.8125rem;
        }
        
        .stButton > button {
            width: 100%;
            background-color: rgba(103, 162, 225, 0.1);
            border: 1px solid rgba(103, 162, 225, 0.3);
            color: #67A2E1;
            font-weight: 500;
            border-radius: 8px;
            padding: 0.5rem 1rem;
        }
        
        .stButton > button:hover {
            background-color: rgba(103, 162, 225, 0.2);
            border-color: rgba(103, 162, 225, 0.5);
        }
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        # Get current working directory (where streamlit is run from)
        cwd = os.getcwd()
        
        # Try to get script directory
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
        except:
            script_dir = cwd
            project_root = os.path.dirname(cwd) if os.path.basename(cwd) == 'script' else cwd
        
        # Build possible data directories
        possible_data_dirs = [
            os.path.join(project_root, 'data'),
            os.path.join(cwd, 'data'),
            os.path.join(cwd, '..', 'data'),
            os.path.join(script_dir, 'data'),
            'data'
        ]
        
        # Try different possible file names and paths
        # Priority: ../data/ (most likely when running from script/)
        file_paths = [
            os.path.abspath(os.path.join(cwd, '..', 'data', 'balancer_v2_financial_master_final.csv')),  # ../data/ - MOST LIKELY
        ]
        # Then try other data directories
        for data_dir in possible_data_dirs:
            abs_data_dir = os.path.abspath(data_dir)
            file_paths.extend([
                os.path.join(abs_data_dir, 'balancer_v2_financial_master_final.csv'),
                os.path.join(abs_data_dir, 'balancer_v2_best_pools.csv'),
            ])
        # Also try relative to current directory
        file_paths.extend([
            os.path.join(cwd, 'balancer_v2_financial_master_final.csv'),
            'data/balancer_v2_financial_master_final.csv',
            'balancer_v2_financial_master_final.csv'
        ])
        
        df = None
        found_path = None
        for path in file_paths:
            try:
                # Normalize path
                if not os.path.isabs(path):
                    abs_path = os.path.abspath(path)
                else:
                    abs_path = path
                
                # Check if file exists and has content
                if os.path.exists(abs_path) and os.path.getsize(abs_path) > 100:  # At least 100 bytes
                    df = pd.read_csv(abs_path)
                    if df is not None and not df.empty:
                        found_path = abs_path
                        break
            except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, Exception) as e:
                continue
        
        if df is None or df.empty:
            error_msg = st.error("❌ CSV file not found or is empty.")
            with st.expander("🔍 Debug Info - Click to see details"):
                st.write(f"**Current working directory:** `{cwd}`")
                st.write(f"**Script directory:** `{script_dir}`")
                st.write(f"**Project root:** `{project_root}`")
                st.write("**Tried paths:**")
                for i, path in enumerate(file_paths[:15], 1):
                    abs_path = os.path.abspath(path)
                    exists = "✅" if os.path.exists(abs_path) else "❌"
                    st.write(f"{i}. {exists} `{abs_path}`")
                # List files in data directory if it exists
                for data_dir in possible_data_dirs:
                    abs_data_dir = os.path.abspath(data_dir)
                    if os.path.exists(abs_data_dir):
                        st.write(f"\n**Files in `{abs_data_dir}`:**")
                        try:
                            files = [f for f in os.listdir(abs_data_dir) if f.endswith('.csv')]
                            for f in files[:10]:
                                st.write(f"  - {f}")
                        except:
                            pass
            return pd.DataFrame()
        
        if 'block_date' in df.columns:
            df['block_date'] = pd.to_datetime(df['block_date'], errors='coerce')
        
        numeric_cols = [
            'protocol_fee_amount_usd',
            'total_protocol_fee_usd',
            'direct_incentives',
            'dao_profit_usd',
            'bal_emited_votes',
            'votes_received',
            'emissions_roi',
            'is_core_pool'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        if 'is_core_pool' in df.columns:
            df['is_core_pool'] = df['is_core_pool'].astype(int)
        
        if 'pool_category' not in df.columns:
            df = classify_pools(df)
        
        return df
    
    except FileNotFoundError:
        st.error("❌ CSV file not found. Please verify that 'balancer_v2_financial_master_final.csv' is in the correct directory.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return pd.DataFrame()

def classify_pools(df):
    pool_agg = df.groupby('pool_symbol').agg({
        'dao_profit_usd': 'sum',
        'protocol_fee_amount_usd': 'sum',
        'direct_incentives': 'sum',
        'emissions_roi': 'mean',
        'is_core_pool': 'max'
    }).reset_index()
    
    pool_agg.columns = ['pool_symbol', 'total_dao_profit', 'total_revenue', 'total_incentives', 'avg_roi', 'is_core_pool']
    
    pool_agg['incentive_dependency'] = np.where(
        pool_agg['total_revenue'] > 0,
        pool_agg['total_incentives'] / pool_agg['total_revenue'],
        1.0
    )
    
    def classify_pool(row):
        if row['total_incentives'] == 0:
            if row['total_revenue'] > 10000:
                return 'Legitimate'
            return 'Undefined'
        
        if row['total_revenue'] == 0:
            return 'Mercenary'
        
        if row['avg_roi'] < 0.5:
            return 'Mercenary'
        
        if row['total_dao_profit'] < -1000:
            return 'Mercenary'
        
        if row['incentive_dependency'] > 0.8:
            return 'Mercenary'
        
        if row['total_revenue'] < 10000:
            return 'Mercenary'
        
        if row['total_dao_profit'] > 0 and row['avg_roi'] > 1.0:
            return 'Legitimate'
        
        if row['is_core_pool'] == 1 and row['avg_roi'] > 0.7:
            return 'Legitimate'
        
        return 'Undefined'
    
    pool_agg['pool_category'] = pool_agg.apply(classify_pool, axis=1)
    
    df = df.merge(
        pool_agg[['pool_symbol', 'pool_category']],
        on='pool_symbol',
        how='left'
    )
    
    df['pool_category'] = df['pool_category'].fillna('Undefined')
    
    return df

@st.cache_data
def load_bribes_data():
    """Load bribes and gauges enriched data"""
    try:
        # Get current working directory (where streamlit is run from)
        cwd = os.getcwd()
        
        # Try different possible file names and paths (in order of likelihood)
        file_paths = [
            os.path.abspath(os.path.join(cwd, '..', 'data', 'Balancer_Bribes_Gauges_enriched.csv')),  # ../data/file.csv
            os.path.abspath(os.path.join(cwd, '..', 'data', 'balancer_bribes_gauges_enriched.csv')),
            os.path.abspath(os.path.join(cwd, '..', 'data', 'Balancer_Bribes_Gauges.csv')),
            os.path.abspath(os.path.join(cwd, 'data', 'Balancer_Bribes_Gauges_enriched.csv')),  # data/file.csv
            os.path.abspath(os.path.join(cwd, 'data', 'balancer_bribes_gauges_enriched.csv')),
            'data/Balancer_Bribes_Gauges_enriched.csv',  # relative
            'data/balancer_bribes_gauges_enriched.csv',
            'Balancer_Bribes_Gauges_enriched.csv'  # current dir
        ]
        
        df_bribes = None
        for path in file_paths:
            try:
                abs_path = os.path.abspath(path) if not os.path.isabs(path) else path
                if os.path.exists(abs_path) and os.path.getsize(abs_path) > 0:
                    df_bribes = pd.read_csv(abs_path)
                    if not df_bribes.empty:
                        break
            except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, Exception):
                continue
        
        if df_bribes is None or df_bribes.empty:
            return pd.DataFrame()
        
        # Convert date columns if they exist
        date_cols = ['date', 'block_date', 'timestamp', 'week', 'period']
        for col in date_cols:
            if col in df_bribes.columns:
                df_bribes[col] = pd.to_datetime(df_bribes[col], errors='coerce')
        
        # Convert numeric columns
        numeric_cols = [
            'bribe_amount_usd', 'bribe_amount', 'total_bribes_usd',
            'votes_received', 'bal_received', 'bal_emitted',
            'bribe_efficiency', 'bribe_per_vote', 'votes_per_bribe',
            'gauge_weight', 'gauge_share', 'bribe_count'
        ]
        
        for col in numeric_cols:
            if col in df_bribes.columns:
                df_bribes[col] = pd.to_numeric(df_bribes[col], errors='coerce').fillna(0)
        
        return df_bribes
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading bribes data: {str(e)}")
        return pd.DataFrame()

def get_top_pools(df, n=20):
    pool_agg = df.groupby('pool_symbol')['dao_profit_usd'].sum().sort_values(ascending=False).head(n)
    return pool_agg.index.tolist()

def get_worst_pools(df, n=20):
    pool_agg = df.groupby('pool_symbol')['dao_profit_usd'].sum().sort_values(ascending=True).head(n)
    return pool_agg.index.tolist()

def run_simulation_sidebar(df):
    st.sidebar.markdown("### ⚖️ Simulation Controls")
    
    st.sidebar.markdown("**1. Protocol Fee Percentage**")
    protocol_fee_pct = st.sidebar.slider(
        "Protocol Fee (%)",
        min_value=0,
        max_value=100,
        value=50,
        step=5,
        help="Percentage of total fees that goes to the protocol before distribution"
    )
    st.sidebar.markdown("**2. Revenue Share**")
    st.sidebar.caption("Division of remaining revenue after protocol fee")
    
    with st.sidebar.expander("📊 Non-Core Pools", expanded=True):
        nc_dao_pct = st.slider(
            "DAO Share (%)",
            min_value=0,
            max_value=100,
            value=50,
            step=1,
            key='nc_dao'
        )
        nc_holders_pct = 100 - nc_dao_pct
        st.caption(f"veBAL/BAL Holders: {nc_holders_pct}%")
    
    with st.sidebar.expander("⭐ Core Pools", expanded=True):
        c_dao_pct = st.slider(
            "DAO Share (%)",
            min_value=0,
            max_value=100,
            value=18,
            step=1,
            key='c_dao'
        )
        remaining_core = 100 - c_dao_pct
        c_holders_pct = st.slider(
            "veBAL/BAL Holders (%)",
            min_value=0,
            max_value=remaining_core,
            value=min(22, remaining_core),
            step=1,
            key='c_holders'
        )
        c_incentives_pct = 100 - c_dao_pct - c_holders_pct
        st.caption(f"Incentives (Tribes): {c_incentives_pct}%")
    
    st.sidebar.markdown("**3. Emissions**")
    emissions_per_week = st.sidebar.slider(
        "BAL Emitted per Week",
        min_value=0,
        max_value=200_000,
        value=86_000,
        step=1_000,
        help="Amount of BAL emitted per week, distributed proportionally to votes"
    )
    
    df_sim = df.copy()
    
    mask_core = df_sim['is_core_pool'] == 1
    mask_noncore = df_sim['is_core_pool'] == 0
    
    df_sim['sim_protocol_fee'] = df_sim['total_protocol_fee_usd'] * (protocol_fee_pct / 100)
    df_sim['remaining_revenue'] = df_sim['total_protocol_fee_usd'] - df_sim['sim_protocol_fee']
    
    df_sim['sim_dao_revenue'] = 0.0
    df_sim['sim_holders_revenue'] = 0.0
    df_sim['sim_incentives_revenue'] = 0.0
    
    df_sim.loc[mask_noncore, 'sim_dao_revenue'] = (
        df_sim.loc[mask_noncore, 'remaining_revenue'] * (nc_dao_pct / 100)
    )
    df_sim.loc[mask_noncore, 'sim_holders_revenue'] = (
        df_sim.loc[mask_noncore, 'remaining_revenue'] * (nc_holders_pct / 100)
    )
    
    df_sim.loc[mask_core, 'sim_dao_revenue'] = (
        df_sim.loc[mask_core, 'remaining_revenue'] * (c_dao_pct / 100)
    )
    df_sim.loc[mask_core, 'sim_holders_revenue'] = (
        df_sim.loc[mask_core, 'remaining_revenue'] * (c_holders_pct / 100)
    )
    df_sim.loc[mask_core, 'sim_incentives_revenue'] = (
        df_sim.loc[mask_core, 'remaining_revenue'] * (c_incentives_pct / 100)
    )
    
    df_sim['week'] = df_sim['block_date'].dt.to_period('W').dt.start_time
    weekly_votes = df_sim.groupby('week')['votes_received'].sum()
    
    df_sim['weekly_total_votes'] = df_sim['week'].map(weekly_votes)
    df_sim['vote_share'] = np.where(
        df_sim['weekly_total_votes'] > 0,
        df_sim['votes_received'] / df_sim['weekly_total_votes'],
        0
    )
    
    df_sim['sim_bal_emitted'] = df_sim['vote_share'] * emissions_per_week
    
    df_sim.attrs['protocol_fee_pct'] = protocol_fee_pct
    df_sim.attrs['emissions_per_week'] = emissions_per_week
    df_sim.attrs['nc_dao_pct'] = nc_dao_pct
    df_sim.attrs['nc_holders_pct'] = nc_holders_pct
    df_sim.attrs['c_dao_pct'] = c_dao_pct
    df_sim.attrs['c_holders_pct'] = c_holders_pct
    df_sim.attrs['c_incentives_pct'] = c_incentives_pct
    
    return df_sim

def create_minimalist_chart(x, y, name, color, height=400):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines',
        name=name,
        line=dict(color=color, width=1.5),
        hovertemplate='%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=height,
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
        showlegend=False
    )
    
    return fig

def calculate_emission_reduction_impact(df, reduction_factor):
    df_scenario = df.copy()
    
    if 'sim_bal_emitted' in df_scenario.columns:
        df_scenario['reduced_bal_emitted'] = df_scenario['sim_bal_emitted'] * reduction_factor
    else:
        df_scenario['reduced_bal_emitted'] = df_scenario['bal_emited_votes'] * reduction_factor
    
    if 'direct_incentives' in df_scenario.columns:
        df_scenario['reduced_incentives'] = df_scenario['direct_incentives'] * reduction_factor
    else:
        df_scenario['reduced_incentives'] = 0
    
    if 'sim_dao_revenue' in df_scenario.columns:
        df_scenario['new_dao_profit'] = df_scenario['sim_dao_revenue'] - df_scenario['reduced_incentives']
    else:
        df_scenario['new_dao_profit'] = df_scenario['protocol_fee_amount_usd'] - df_scenario['reduced_incentives']
    
    return df_scenario
