import streamlit as st
import utils
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
import traceback

st.set_page_config(page_title="Bribes Analysis", layout="wide", page_icon="💰")

# Check authentication
if not utils.check_authentication():
    st.stop()

utils.inject_css()

# Script para aplicar IDs específicos aos botões usando components.v1.html (mais confiável)
import streamlit.components.v1 as components

components.html("""
<script>
console.log('[Button IDs] Script carregado via components.html!');

function applyButtonIds() {
    console.log('[Button IDs] Executando applyButtonIds...');
    
    // Tenta múltiplos contextos do DOM
    const contexts = [
        { doc: document, name: 'document' },
        { doc: window.parent?.document, name: 'parent' },
        { doc: window.top?.document, name: 'top' }
    ];
    
    let totalButtons = 0;
    let perfButtonFound = false;
    
    contexts.forEach(({ doc, name }) => {
        if (!doc) {
            console.log(`[Button IDs] Contexto ${name}: não disponível`);
            return;
        }
        
        try {
            // Procura por todos os botões do Streamlit
            const buttons = doc.querySelectorAll('button[data-testid*="stBaseButton"], button');
            console.log(`[Button IDs] Contexto ${name}: Encontrados ${buttons.length} botões`);
            
            buttons.forEach((button, index) => {
                // Pega o texto completo do botão (incluindo emojis e espaços)
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
                } catch(e) {
                    console.error(`[Button IDs] Erro ao pegar texto:`, e);
                }
                
                const textLower = text.toLowerCase();
                
                // Log todos os botões para debug
                if (text) {
                    console.log(`[Button IDs] Botão ${index} (${name}): "${text}"`);
                }
                
                // Aplica IDs específicos baseado no texto do botão
                if (text === 'Top 20' || textLower === 'top 20') {
                    button.id = 'btn_top20_bribes';
                    console.log(`[Button IDs] ✅ ID aplicado: btn_top20_bribes`);
                } else if (text === 'Worst 20' || textLower === 'worst 20') {
                    button.id = 'btn_worst20_bribes';
                    console.log(`[Button IDs] ✅ ID aplicado: btn_worst20_bribes`);
                } else if (text === 'Select All' || textLower === 'select all') {
                    button.id = 'btn_select_all_bribes';
                    console.log(`[Button IDs] ✅ ID aplicado: btn_select_all_bribes`);
                } else if (text.includes('Show Performance') || text.includes('Performance by Pool') || textLower.includes('performance') || text.includes('🔍')) {
                    button.id = 'btn_performance_by_pool';
                    button.classList.add('performance-button-fallback');
                    button.setAttribute('data-button-type', 'performance');
                    console.log(`[Button IDs] ✅ ID aplicado: btn_performance_by_pool`);
                    console.log(`[Button IDs] Texto detectado: "${text}"`);
                    
                    // Aplica TODOS os estilos inline diretamente (máxima prioridade)
                    const styles = {
                        'width': '250px',
                        'min-width': '250px',
                        'max-width': '250px',
                        'height': '56px',
                        'padding': '0.625rem 1.5rem',
                        'font-weight': '600',
                        'background': 'linear-gradient(135deg, rgba(103, 162, 225, 0.18) 0%, rgba(103, 162, 225, 0.08) 100%)',
                        'border': '1.5px solid rgba(103, 162, 225, 0.45)',
                        'color': '#8BB5F0',
                        'border-radius': '12px',
                        'transition': 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        'box-shadow': '0 3px 12px rgba(103, 162, 225, 0.15)',
                        'position': 'relative',
                        'overflow': 'hidden',
                        'letter-spacing': '0.02em'
                    };
                    
                    Object.keys(styles).forEach(prop => {
                        button.style.setProperty(prop, styles[prop], 'important');
                    });
                    
                    perfButtonFound = true;
                    console.log(`[Button IDs] ✅ Todos os estilos inline aplicados!`);
                }
            });
            
            totalButtons += buttons.length;
        } catch(e) {
            console.error(`[Button IDs] Erro no contexto ${name}:`, e);
        }
    });
    
    if (!perfButtonFound) {
        console.log('[Button IDs] ⚠️ Botão performance NÃO encontrado!');
    }
    
    console.log(`[Button IDs] Total de botões processados: ${totalButtons}`);
}

// Executa imediatamente
console.log('[Button IDs] Executando imediatamente...');
applyButtonIds();

// Executa após delays
setTimeout(() => {
    console.log('[Button IDs] Execução após 100ms');
    applyButtonIds();
}, 100);
setTimeout(() => {
    console.log('[Button IDs] Execução após 500ms');
    applyButtonIds();
}, 500);
setTimeout(() => {
    console.log('[Button IDs] Execução após 1000ms');
    applyButtonIds();
}, 1000);
setTimeout(() => {
    console.log('[Button IDs] Execução após 2000ms');
    applyButtonIds();
}, 2000);

// Executa repetidamente
const intervalId = setInterval(() => {
    console.log('[Button IDs] Intervalo de verificação (3s)');
    applyButtonIds();
}, 3000);

// Observa mudanças no DOM
if (window.MutationObserver) {
    const observer = new MutationObserver(() => {
        setTimeout(applyButtonIds, 100);
    });
    
    if (document.body) {
        observer.observe(document.body, { childList: true, subtree: true });
    }
    
    // Tenta observar no contexto pai também
    try {
        if (window.parent && window.parent.document && window.parent.document.body) {
            observer.observe(window.parent.document.body, { childList: true, subtree: true });
        }
    } catch(e) {
        console.log('[Button IDs] Não foi possível observar contexto pai:', e);
    }
}
</script>
""", height=0)

try:
    # Load data
    df = utils.load_data()
    df_bribes = utils.load_bribes_data()
    df_votes = utils.load_vebal_votes_data()  # Load veBAL votes data

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
    
    # Merge votes data with bribes data if available
    if not df_votes.empty and 'gauge_address' in df_bribes.columns:
        # Clean gauge addresses for matching
        import re
        def clean_gauge_address(addr):
            if pd.isna(addr):
                return ""
            addr_str = str(addr)
            # Remove 0x prefix if present, normalize
            if addr_str.startswith('0x'):
                return addr_str.lower().strip()
            return addr_str.lower().strip()
        
        # Extract gauge address from votes data
        def extract_gauge_from_votes(gauge_str):
            if pd.isna(gauge_str):
                return ""
            gauge_str = str(gauge_str)
            if gauge_str.startswith('0x'):
                return gauge_str.lower().strip()
            return gauge_str.lower().strip()
        
        # Clean symbol column in votes data if it doesn't exist
        def clean_symbol(symbol):
            """Extract text from HTML links"""
            if pd.isna(symbol):
                return ""
            # Remove HTML tags and extract text
            text = re.sub(r'<[^>]+>', '', str(symbol))
            # Remove the ↗ emoji if present
            text = text.replace('↗', '').strip()
            return text
        
        # Create symbol_clean if it doesn't exist
        if 'symbol_clean' not in df_votes.columns and 'symbol' in df_votes.columns:
            df_votes['symbol_clean'] = df_votes['symbol'].apply(clean_symbol)
        elif 'symbol_clean' not in df_votes.columns:
            df_votes['symbol_clean'] = ""
        
        df_bribes['gauge_address_clean'] = df_bribes['gauge_address'].apply(clean_gauge_address)
        df_votes['gauge_address_clean'] = df_votes['gauge'].apply(extract_gauge_from_votes)
        
        # Prepare columns for merge
        merge_cols = ['gauge_address_clean', 'votes', 'pct_votes', 'ranking', 'symbol_clean']
        available_cols = [col for col in merge_cols if col in df_votes.columns]
        
        # Merge votes data
        df_bribes = df_bribes.merge(
            df_votes[available_cols].rename(columns={
                'votes': 'vebal_votes',
                'pct_votes': 'vebal_pct_votes',
                'ranking': 'vebal_ranking',
                'symbol_clean': 'vebal_symbol'
            }),
            on='gauge_address_clean',
            how='left'
        )
        
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
    st.session_state.pool_filter_mode_bribes = 'all'  # Default: show all pools
if 'show_performance_by_pool' not in st.session_state:
    st.session_state.show_performance_by_pool = False

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("Top 20", key="btn_top20_bribes"):
        st.session_state.pool_filter_mode_bribes = 'top20'
        st.session_state.show_performance_by_pool = False
        st.session_state.selected_pools_bribes = []
        st.rerun()
with col_btn2:
    if st.button("Worst 20", key="btn_worst20_bribes"):
        st.session_state.pool_filter_mode_bribes = 'worst20'
        st.session_state.show_performance_by_pool = False
        st.session_state.selected_pools_bribes = []
        st.rerun()

# Show "Select All" button only when a filter is active (top20 or worst20)
if st.session_state.pool_filter_mode_bribes in ['top20', 'worst20']:
    if st.sidebar.button("Select All", key="btn_select_all_bribes"):
        st.session_state.pool_filter_mode_bribes = 'all'
        st.session_state.show_performance_by_pool = False
        st.session_state.selected_pools_bribes = []
        st.rerun()


# Determine filter pools based on mode
if st.session_state.pool_filter_mode_bribes == 'top20':
    filter_pools = sorted([str(p) for p in utils.get_top_pools(df, n=20)])
    filter_label = "Top 20 Pools"
    # Auto-select all pools in the category
    if not st.session_state.selected_pools_bribes or len(st.session_state.selected_pools_bribes) == 0:
        st.session_state.selected_pools_bribes = filter_pools.copy()
elif st.session_state.pool_filter_mode_bribes == 'worst20':
    filter_pools = sorted([str(p) for p in utils.get_worst_pools(df, n=20)])
    filter_label = "Worst 20 Pools"
    # Auto-select all pools in the category
    if not st.session_state.selected_pools_bribes or len(st.session_state.selected_pools_bribes) == 0:
        st.session_state.selected_pools_bribes = filter_pools.copy()
else:  # 'all' - default mode, show everything
    # Get all unique pools from main data
    all_pools = sorted([str(p) for p in df['pool_symbol'].unique() if pd.notna(p)])
    filter_pools = all_pools
    filter_label = "Select Pools (All Available)"
    # Auto-select all pools when in 'all' mode
    if not st.session_state.selected_pools_bribes or len(st.session_state.selected_pools_bribes) == 0:
        st.session_state.selected_pools_bribes = filter_pools.copy()

# Use dynamic key based on filter mode to force update when mode changes
multiselect_key = f"multiselect_pools_bribes_{st.session_state.pool_filter_mode_bribes}"

# Ensure default_selection matches current filter mode
if st.session_state.pool_filter_mode_bribes in ['top20', 'worst20']:
    # In filter mode, use filter_pools as default
    default_selection = filter_pools.copy()
    # Sync session state with filter_pools
    valid_selection = [p for p in st.session_state.selected_pools_bribes if p in filter_pools]
    if len(valid_selection) != len(filter_pools):
        st.session_state.selected_pools_bribes = filter_pools.copy()
        default_selection = filter_pools.copy()
    else:
        default_selection = valid_selection if valid_selection else filter_pools.copy()
else:
    # In 'all' mode, use all pools
    default_selection = filter_pools.copy()
    st.session_state.selected_pools_bribes = filter_pools.copy()

selected_pools = st.sidebar.multiselect(
    filter_label,
    options=filter_pools,
    default=default_selection if default_selection else [],
    help="Select specific pools to view individual analysis",
    key=multiselect_key
)

# Sync session state with current selection
if not selected_pools or len(selected_pools) == 0:
    # If nothing selected, select all pools in current filter context
    st.session_state.selected_pools_bribes = filter_pools.copy()
    selected_pools = filter_pools.copy()
else:
    st.session_state.selected_pools_bribes = list(selected_pools)

# Determine if we should filter by pools
if st.session_state.pool_filter_mode_bribes in ['top20', 'worst20']:
    filter_by_pools = True  # Always filter when in top20/worst20 mode
else:  # 'all' mode
    filter_by_pools = True  # Always filter (by all pools or selected ones)

# Prepare data
if st.session_state.pool_filter_mode_bribes in ['top20', 'worst20']:
    # Show all pools in the selected category (top20 or worst20)
    category_pools = selected_pools if selected_pools else filter_pools
    mode_label = "Top 20" if st.session_state.pool_filter_mode_bribes == 'top20' else "Worst 20"
    
    # CRITICAL: Filter df_display to ONLY show top20/worst20 pools
    df_display = df_sim[df_sim['pool_symbol'].isin(category_pools)].copy()
    
    # Verify the filter worked
    if len(df_display['pool_symbol'].unique()) != len(category_pools):
        # Some pools might not be in df_sim, that's okay
        actual_pools = set(df_display['pool_symbol'].unique())
        expected_pools = set(category_pools)
        missing_pools = expected_pools - actual_pools
        if missing_pools:
            st.sidebar.warning(f"⚠️ {len(missing_pools)} pools from {mode_label} not found in main data")
    
    # Try to match pools in bribes data - use multiple matching strategies
    pool_match_col = None
    for col in ['pool_title', 'pool_name', 'pool_symbol', 'pool']:
        if col in df_bribes.columns:
            pool_match_col = col
            break
    
    if pool_match_col:
        # Try exact match first - use selected_pools if available, otherwise category_pools
        pools_to_match = selected_pools if selected_pools else category_pools
        df_bribes_display = df_bribes[
            df_bribes[pool_match_col].astype(str).str.upper().str.strip().isin([p.upper().strip() for p in pools_to_match])
        ].copy()
        
        # If no matches found, try partial matching (contains)
        if df_bribes_display.empty:
            # Try fuzzy matching - check if pool name contains any of the category pool names
            matched_indices = []
            pools_to_match = selected_pools if selected_pools else category_pools
            for idx, row in df_bribes.iterrows():
                pool_name = str(row[pool_match_col]).upper().strip()
                for cat_pool in pools_to_match:
                    cat_pool_upper = cat_pool.upper().strip()
                    # Check if pool name contains category pool or vice versa
                    if cat_pool_upper in pool_name or pool_name in cat_pool_upper:
                        matched_indices.append(idx)
                        break
            if matched_indices:
                df_bribes_display = df_bribes.loc[matched_indices].copy()
        
        # IMPORTANT: If still empty, show empty dataframe, NOT all bribes data
        # This ensures we only show data for the selected top20/worst20 pools
        if df_bribes_display.empty:
            df_bribes_display = pd.DataFrame()
    else:
        # No pool column found, show empty dataframe to maintain filter
        df_bribes_display = pd.DataFrame()
    
    matched_count = len(df_bribes_display[pool_match_col].unique()) if pool_match_col and not df_bribes_display.empty else 0
    
    # Debug info (can be removed later)
    if st.sidebar.checkbox("🔍 Debug Matching", value=False, key="debug_matching_bribes"):
        st.sidebar.write(f"**Category Pools:** {len(category_pools)}")
        st.sidebar.write(f"**df_display unique pools:** {len(df_display['pool_symbol'].unique())}")
        st.sidebar.write(f"**Matched in Bribes:** {matched_count}")
        if category_pools:
            st.sidebar.write(f"**Sample Category Pool:** {category_pools[0]}")
        if pool_match_col and not df_bribes_display.empty:
            sample_bribe_pool = df_bribes_display[pool_match_col].iloc[0] if len(df_bribes_display) > 0 else "N/A"
            st.sidebar.write(f"**Sample Bribe Pool:** {sample_bribe_pool}")
        st.sidebar.write(f"**Bribes Data Rows:** {len(df_bribes_display)}")
        st.sidebar.write(f"**df_display Rows:** {len(df_display)}")
    
    # Only show info if there are matches, otherwise show nothing (cleaner UI)
    pools_displayed = len(selected_pools) if selected_pools else len(category_pools)
    if matched_count > 0:
        st.info(f"📊 Showing analysis for {mode_label} Pools ({pools_displayed} pools, {matched_count} matched in bribes data)")
else:
    # 'all' mode - show all pools or selected pools
    if selected_pools and len(selected_pools) > 0:
        df_display = df_sim[df_sim['pool_symbol'].isin(selected_pools)].copy()
        # Try to match pools in bribes data
        pool_match_col = None
        for col in ['pool_title', 'pool_name', 'pool_symbol', 'pool']:
            if col in df_bribes.columns:
                pool_match_col = col
                break
        
        if pool_match_col:
            df_bribes_display = df_bribes[
                df_bribes[pool_match_col].astype(str).str.upper().str.strip().isin([p.upper().strip() for p in selected_pools])
            ].copy()
        else:
            df_bribes_display = df_bribes.copy()
        st.info(f"📊 Showing analysis for {len(selected_pools)} selected pool(s)")
    else:
        # Show all pools
        df_display = df_sim.copy()
        df_bribes_display = df_bribes.copy()
        total_pools = len(df_display['pool_symbol'].unique()) if 'pool_symbol' in df_display.columns else 0
        st.info(f"📊 Showing analysis for all pools ({total_pools} pools)")

# Page Header with logout button
col_title, col_logout = st.columns([1, 0.1])
with col_title:
    st.markdown('<div class="page-title">💰 Bribes Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Comprehensive analysis of bribes, voting patterns, and their impact on BAL distribution</div>', unsafe_allow_html=True)
with col_logout:
    utils.show_logout_button()

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
    # First check if we have veBAL votes from merge
    if 'vebal_votes' in df_bribes.columns:
        votes_col = 'vebal_votes'
    else:
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
        agg_dict['total_bribes_periodo'] = 'max'  # Use max since it's per period
    # Include veBAL votes if available
    if 'vebal_votes' in df_bribes_display.columns:
        agg_dict['vebal_votes'] = 'sum'
    if 'vebal_pct_votes' in df_bribes_display.columns:
        agg_dict['vebal_pct_votes'] = 'mean'  # Average percentage
    if 'vebal_ranking' in df_bribes_display.columns:
        agg_dict['vebal_ranking'] = 'min'  # Best (lowest) ranking

    # Calculate metrics
    if df_bribes_display.empty:
        # Create empty dataframe with correct structure (no warning message - cleaner UI)
        pool_bribes = pd.DataFrame(columns=[pool_col] + list(agg_dict.keys()))
    else:
        pool_bribes = df_bribes_display.groupby(pool_col).agg(agg_dict).reset_index()
except Exception as e:
    st.error(f"❌ Error aggregating data: {str(e)}")
    st.code(traceback.format_exc())
    st.stop()

# Calculate derived metrics
if not pool_bribes.empty:
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
    
    # Ensure bribe_efficiency is numeric (convert from object if needed)
    if 'bribe_efficiency' in pool_bribes.columns:
        pool_bribes['bribe_efficiency'] = pd.to_numeric(pool_bribes['bribe_efficiency'], errors='coerce').fillna(0)
else:
    # Create empty columns for consistency when DataFrame is empty
    if pool_bribes.empty:
        # Create empty DataFrame with proper structure and numeric columns
        empty_cols = [pool_col, bribe_col, 'bribe_efficiency']
        if votes_col:
            empty_cols.append('bribe_per_vote')
        pool_bribes = pd.DataFrame(columns=empty_cols)
        # Ensure numeric columns have proper dtype
        for col in ['bribe_efficiency', 'bribe_per_vote']:
            if col in pool_bribes.columns:
                pool_bribes[col] = pool_bribes[col].astype(float)

# Merge with main data for additional context (if pool_symbol exists in main data)
if 'pool_symbol' in df_display.columns and not pool_bribes.empty:
    main_agg = df_display.groupby('pool_symbol').agg({
        'dao_profit_usd': 'sum',
        'protocol_fee_amount_usd': 'sum',
        'direct_incentives': 'sum'
    }).reset_index()
    
    # Try to match pools (case-insensitive match)
    # The bribes data uses pool_title/pool_name, main data uses pool_symbol
    # Try to match by converting both to uppercase and matching
    if pool_col in pool_bribes.columns:
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

col1, col2, col3, col4, col5 = st.columns(5)

total_bribes = pool_bribes[bribe_col].sum() if bribe_col in pool_bribes.columns and not pool_bribes.empty else 0
total_votes = pool_bribes[votes_col].sum() if votes_col and votes_col in pool_bribes.columns and not pool_bribes.empty else 0
total_bal = pool_bribes[bal_col].sum() if bal_col and bal_col in pool_bribes.columns and not pool_bribes.empty else 0
avg_efficiency = pd.to_numeric(pool_bribes['bribe_efficiency'], errors='coerce').mean() if 'bribe_efficiency' in pool_bribes.columns and not pool_bribes.empty else 0
total_vebal_votes = pool_bribes['vebal_votes'].sum() if 'vebal_votes' in pool_bribes.columns and not pool_bribes.empty else 0

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
        "veBAL Votes",
        f"{total_vebal_votes:,.0f}",
        help="Total veBAL votes from current voting period"
    )

with col4:
    st.metric(
        "Total BAL Received",
        f"{total_bal:,.0f}",
        help="Total BAL tokens received from bribes"
    )

with col5:
    efficiency_display = f"{avg_efficiency:.2f}" if pd.notna(avg_efficiency) and not np.isnan(avg_efficiency) else "N/A"
    st.metric(
        "Avg Bribe Efficiency",
        efficiency_display,
        help="Average BAL received per USD of bribe"
    )

st.markdown("---")

# Rankings
st.markdown("### 🏆 Pool Rankings")

tab1, tab2, tab3, tab4 = st.tabs(["💰 Top Bribes", "⚡ Best Efficiency", "📈 Most Votes", "🗳️ veBAL Votes"])

with tab1:
    if bribe_col in pool_bribes.columns and not pool_bribes.empty:
        # Filter out pools with zero or negative bribes
        bribes_with_data = pool_bribes[pool_bribes[bribe_col] > 0]
        if not bribes_with_data.empty:
            top_bribes = bribes_with_data.nlargest(20, bribe_col)[[pool_col, bribe_col]].copy()
            top_bribes.columns = ['Pool', 'Total Bribes (USD)']
            top_bribes['Total Bribes (USD)'] = top_bribes['Total Bribes (USD)'].apply(lambda x: f"${x:,.0f}")
            st.dataframe(top_bribes, use_container_width=True, hide_index=True)
        else:
            st.info("No pools with bribes data found for the selected filter.")
    else:
        st.info("Bribe amount data not available")

with tab2:
    if 'bribe_efficiency' in pool_bribes.columns and not pool_bribes.empty:
        # Ensure bribe_efficiency is numeric before filtering
        pool_bribes['bribe_efficiency'] = pd.to_numeric(pool_bribes['bribe_efficiency'], errors='coerce').fillna(0)
        efficiency_data = pool_bribes[pool_bribes['bribe_efficiency'] > 0]
        if not efficiency_data.empty and len(efficiency_data) > 0:
            # Ensure the column is numeric before using nlargest
            efficiency_data['bribe_efficiency'] = pd.to_numeric(efficiency_data['bribe_efficiency'], errors='coerce').fillna(0)
            top_efficiency = efficiency_data.nlargest(20, 'bribe_efficiency')[[pool_col, 'bribe_efficiency']].copy()
            top_efficiency.columns = ['Pool', 'Bribe Efficiency']
            top_efficiency['Bribe Efficiency'] = top_efficiency['Bribe Efficiency'].apply(lambda x: f"{x:.3f}")
            st.dataframe(top_efficiency, use_container_width=True, hide_index=True)
        else:
            st.info("No pools with positive efficiency found for the selected filter.")
    else:
        st.info("Efficiency data not available")

with tab3:
    if votes_col and votes_col in pool_bribes.columns and not pool_bribes.empty:
        top_votes = pool_bribes.nlargest(20, votes_col)[[pool_col, votes_col]].copy()
        top_votes.columns = ['Pool', 'Total Votes']
        top_votes['Total Votes'] = top_votes['Total Votes'].apply(lambda x: f"{x:,.0f}")
        st.dataframe(top_votes, use_container_width=True, hide_index=True)
    else:
        st.info("Votes data not available")

with tab4:
    if 'vebal_votes' in pool_bribes.columns:
        # Filter out pools with no veBAL votes
        vebal_data = pool_bribes[pool_bribes['vebal_votes'].notna() & (pool_bribes['vebal_votes'] > 0)].copy()
        if not vebal_data.empty:
            top_vebal = vebal_data.nlargest(20, 'vebal_votes')[[pool_col, 'vebal_votes', 'vebal_pct_votes', 'vebal_ranking']].copy()
            top_vebal.columns = ['Pool', 'veBAL Votes', 'Vote Share %', 'Ranking']
            top_vebal['veBAL Votes'] = top_vebal['veBAL Votes'].apply(lambda x: f"{x:,.0f}")
            top_vebal['Vote Share %'] = top_vebal['Vote Share %'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A")
            top_vebal['Ranking'] = top_vebal['Ranking'].apply(lambda x: f"#{int(x)}" if pd.notna(x) else "N/A")
            st.dataframe(top_vebal, use_container_width=True, hide_index=True)
            
            # Add visualization
            st.markdown("#### 📊 Top 10 Pools by veBAL Votes")
            top_10_vebal = vebal_data.nlargest(10, 'vebal_votes')
            fig_vebal = px.bar(
                top_10_vebal,
                x=pool_col,
                y='vebal_votes',
                title="Top 10 Pools by veBAL Votes",
                labels={'vebal_votes': 'veBAL Votes', pool_col: 'Pool'},
                color='vebal_votes',
                color_continuous_scale='Blues'
            )
            fig_vebal.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title=dict(font=dict(color='white', size=16)),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickangle=-45),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                showlegend=False
            )
            st.plotly_chart(fig_vebal, use_container_width=True)
        else:
            st.info("No veBAL votes data available for the selected pools")
    else:
        st.info("veBAL votes data not available. Please ensure veBAL_votes.csv is in the data folder.")

st.markdown("---")

# Performance by Pool button (only shown when top20 or worst20 is selected)
if st.session_state.pool_filter_mode_bribes in ['top20', 'worst20']:
    st.markdown("### 📊 Performance by Pool")
    
    col_btn_perf, col_info = st.columns([1, 4])
    with col_btn_perf:
        if st.button("🔍 Show Performance by Pool", key="btn_performance_by_pool"):
            st.session_state.show_performance_by_pool = not st.session_state.show_performance_by_pool
            st.rerun()
    
    if st.session_state.show_performance_by_pool:
        mode_label = "Top 20" if st.session_state.pool_filter_mode_bribes == 'top20' else "Worst 20"
        category_pools = filter_pools
        
        st.markdown(f"#### {mode_label} Pools - Individual Performance")
        
        for pool in category_pools:
            # Try to match pool from category_pools with pool_col in bribes data
            if not pool_bribes.empty and pool_col in pool_bribes.columns:
                pool_bribe_data = pool_bribes[
                    pool_bribes[pool_col].astype(str).str.upper().str.strip() == pool.upper().strip()
                ]
            else:
                pool_bribe_data = pd.DataFrame()
            pool_main_data = df_display[df_display['pool_symbol'] == pool] if 'pool_symbol' in df_display.columns else pd.DataFrame()
            
            if not pool_bribe_data.empty or not pool_main_data.empty:
                with st.expander(f"📊 {pool}", expanded=False):
                    if not pool_bribe_data.empty:
                        col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
                        
                        pool_bribes_val = pool_bribe_data[bribe_col].iloc[0] if bribe_col in pool_bribe_data.columns else 0
                        pool_votes_val = pool_bribe_data[votes_col].iloc[0] if votes_col and votes_col in pool_bribe_data.columns else 0
                        pool_bal_val = pool_bribe_data[bal_col].iloc[0] if bal_col and bal_col in pool_bribe_data.columns else 0
                        pool_eff = pool_bribe_data['bribe_efficiency'].iloc[0] if 'bribe_efficiency' in pool_bribe_data.columns else 0
                        pool_vebal_votes = pool_bribe_data['vebal_votes'].iloc[0] if 'vebal_votes' in pool_bribe_data.columns and pd.notna(pool_bribe_data['vebal_votes'].iloc[0]) else 0
                        pool_vebal_pct = pool_bribe_data['vebal_pct_votes'].iloc[0] if 'vebal_pct_votes' in pool_bribe_data.columns and pd.notna(pool_bribe_data['vebal_pct_votes'].iloc[0]) else 0
                        pool_vebal_rank = pool_bribe_data['vebal_ranking'].iloc[0] if 'vebal_ranking' in pool_bribe_data.columns and pd.notna(pool_bribe_data['vebal_ranking'].iloc[0]) else None
                        
                        with col_p1:
                            st.metric("Total Bribes", f"${pool_bribes_val:,.0f}")
                        with col_p2:
                            st.metric("Votes Received", f"{pool_votes_val:,.0f}")
                        with col_p3:
                            st.metric("BAL Received", f"{pool_bal_val:,.0f}")
                        with col_p4:
                            st.metric("Efficiency", f"{pool_eff:.3f}")
                        with col_p5:
                            if pool_vebal_votes > 0:
                                rank_text = f"#{int(pool_vebal_rank)}" if pool_vebal_rank else "N/A"
                                st.metric("veBAL Votes", f"{pool_vebal_votes:,.0f}", delta=f"{pool_vebal_pct*100:.2f}% share", help=f"Ranking: {rank_text}")
                            else:
                                st.metric("veBAL Votes", "N/A", help="No veBAL votes data available")
                    
                    if not pool_main_data.empty:
                        st.markdown("**Financial Metrics:**")
                        col_f1, col_f2, col_f3 = st.columns(3)
                        with col_f1:
                            st.metric("Total Revenue", f"${pool_main_data['protocol_fee_amount_usd'].sum():,.0f}")
                        with col_f2:
                            st.metric("Total Incentives", f"${pool_main_data['direct_incentives'].sum():,.0f}")
                        with col_f3:
                            st.metric("DAO Profit", f"${pool_main_data['dao_profit_usd'].sum():,.0f}")
                    elif pool_bribe_data.empty:
                        st.info("No data available for this pool")

st.markdown("---")

# Visualizations
st.markdown("### 📈 Visualizations")

viz_col1, viz_col2, viz_col3 = st.columns(3)

with viz_col1:
    if bribe_col in pool_bribes.columns and 'bribe_efficiency' in pool_bribes.columns and not pool_bribes.empty:
        scatter_data = pool_bribes[pool_bribes[bribe_col] > 0].copy()
        if not scatter_data.empty:
            # Ensure bribe_efficiency is numeric
            scatter_data['bribe_efficiency'] = pd.to_numeric(scatter_data['bribe_efficiency'], errors='coerce').fillna(0)
            fig_scatter = px.scatter(
                scatter_data,
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
                title=dict(font=dict(color='white', size=16)),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No data available for scatter plot")
    else:
        st.info("Bribe efficiency data not available")

with viz_col2:
    if votes_col and votes_col in pool_bribes.columns and bribe_col in pool_bribes.columns and not pool_bribes.empty:
        votes_data = pool_bribes[pool_bribes[bribe_col] > 0].copy()
        if not votes_data.empty:
            fig_votes = px.scatter(
                votes_data,
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
                title=dict(font=dict(color='white', size=16)),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig_votes, use_container_width=True)
        else:
            st.info("No data available for votes scatter plot")
    else:
        st.info("Votes data not available")

with viz_col3:
    if 'vebal_votes' in pool_bribes.columns and bribe_col in pool_bribes.columns and not pool_bribes.empty:
        vebal_scatter_data = pool_bribes[
            (pool_bribes[bribe_col] > 0) & 
            (pool_bribes['vebal_votes'].notna()) & 
            (pool_bribes['vebal_votes'] > 0)
        ]
        if not vebal_scatter_data.empty:
            fig_vebal_scatter = px.scatter(
                vebal_scatter_data,
                x=bribe_col,
                y='vebal_votes',
                hover_data=[pool_col, 'vebal_pct_votes'],
                title="🗳️ Bribes vs veBAL Votes",
                labels={
                    bribe_col: 'Total Bribes (USD)', 
                    'vebal_votes': 'veBAL Votes',
                    'vebal_pct_votes': 'Vote Share %'
                },
                color='vebal_votes',
                color_continuous_scale='Greens',
                size='vebal_votes',
                size_max=20
            )
            fig_vebal_scatter.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title=dict(font=dict(color='white', size=16)),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig_vebal_scatter, use_container_width=True)
        else:
            st.info("No data available for veBAL votes visualization")
    else:
        st.info("veBAL votes data not available")

# Analysis section for bribes vs veBAL votes
if 'vebal_votes' in pool_bribes.columns and bribe_col in pool_bribes.columns and not pool_bribes.empty:
    st.markdown("---")
    st.markdown("### 🗳️ Bribes vs veBAL Votes Analysis")
    
    vebal_analysis_data = pool_bribes[
        (pool_bribes[bribe_col] > 0) & 
        (pool_bribes['vebal_votes'].notna()) & 
        (pool_bribes['vebal_votes'] > 0)
    ].copy()
    
    if not vebal_analysis_data.empty:
        col_analysis1, col_analysis2 = st.columns(2)
        
        with col_analysis1:
            st.markdown("#### 📊 Correlation Analysis")
            # Calculate correlation
            correlation = vebal_analysis_data[bribe_col].corr(vebal_analysis_data['vebal_votes'])
            st.metric("Correlation (Bribes ↔ veBAL Votes)", f"{correlation:.3f}", 
                     help="Correlation coefficient between bribes and veBAL votes")
            
            # Calculate bribe per vote
            vebal_analysis_data['bribe_per_vebal_vote'] = np.where(
                vebal_analysis_data['vebal_votes'] > 0,
                vebal_analysis_data[bribe_col] / vebal_analysis_data['vebal_votes'],
                0
            )
            avg_bribe_per_vote = vebal_analysis_data['bribe_per_vebal_vote'].mean()
            st.metric("Avg Bribe per veBAL Vote", f"${avg_bribe_per_vote:.2f}")
            
            # Top pools by bribe efficiency (votes per dollar)
            vebal_analysis_data['votes_per_dollar'] = np.where(
                vebal_analysis_data[bribe_col] > 0,
                vebal_analysis_data['vebal_votes'] / vebal_analysis_data[bribe_col],
                0
            )
            st.markdown("**Top 5 Most Efficient (Votes per Dollar):**")
            top_efficient = vebal_analysis_data.nlargest(5, 'votes_per_dollar')[[pool_col, 'votes_per_dollar', bribe_col, 'vebal_votes']]
            for idx, row in top_efficient.iterrows():
                st.text(f"• {row[pool_col]}: {row['votes_per_dollar']:.2f} votes/$ (${row[bribe_col]:,.0f} bribes → {row['vebal_votes']:,.0f} votes)")
        
        with col_analysis2:
            st.markdown("#### 📈 Distribution")
            # Scatter with manual trend line using numpy
            fig_corr = go.Figure()
            
            # Add scatter points
            fig_corr.add_trace(go.Scatter(
                x=vebal_analysis_data[bribe_col],
                y=vebal_analysis_data['vebal_votes'],
                mode='markers',
                name='Pools',
                marker=dict(
                    color='#67A2E1',
                    size=8,
                    opacity=0.6
                ),
                hovertemplate='<b>%{text}</b><br>Bribes: $%{x:,.0f}<br>Votes: %{y:,.0f}<extra></extra>',
                text=vebal_analysis_data[pool_col]
            ))
            
            # Add trend line using numpy polyfit
            if len(vebal_analysis_data) > 1:
                x_data = vebal_analysis_data[bribe_col].values
                y_data = vebal_analysis_data['vebal_votes'].values
                
                # Remove zeros and NaN for trend line
                valid_mask = (x_data > 0) & (y_data > 0) & np.isfinite(x_data) & np.isfinite(y_data)
                if valid_mask.sum() > 1:
                    x_valid = x_data[valid_mask]
                    y_valid = y_data[valid_mask]
                    
                    # Fit polynomial (linear)
                    z = np.polyfit(x_valid, y_valid, 1)
                    p = np.poly1d(z)
                    
                    # Generate trend line points
                    x_trend = np.linspace(x_valid.min(), x_valid.max(), 100)
                    y_trend = p(x_trend)
                    
                    fig_corr.add_trace(go.Scatter(
                        x=x_trend,
                        y=y_trend,
                        mode='lines',
                        name='Trend Line',
                        line=dict(color='red', width=2, dash='dash'),
                        hovertemplate='Trend: %{y:,.0f} votes<extra></extra>'
                    ))
            
            fig_corr.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title=dict(text="Bribes vs veBAL Votes (with trend)", font=dict(color='white', size=16)),
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    title=dict(text="Total Bribes (USD)", font=dict(color='#8B95A6'))
                ),
                yaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    title=dict(text="veBAL Votes", font=dict(color='#8B95A6'))
                ),
                legend=dict(bgcolor='rgba(0,0,0,0.5)'),
                height=400
            )
            st.plotly_chart(fig_corr, use_container_width=True)

# Top pools bar chart
st.markdown("---")
st.markdown("#### 🏅 Top 10 Pools by Total Bribes")
if bribe_col in pool_bribes.columns and not pool_bribes.empty:
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
        title=dict(font=dict(color='white', size=16)),
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
    if bribe_col in df_bribes_display.columns and not df_bribes_display.empty:
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
            title=dict(font=dict(color='white', size=16)),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            legend=dict(bgcolor='rgba(0,0,0,0.5)')
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

# Detailed Pool Analysis (only for manually selected pools in 'all' mode)
if filter_by_pools and len(selected_pools) > 0 and st.session_state.pool_filter_mode_bribes == 'all':
    st.markdown("---")
    st.markdown("### 🔍 Detailed Pool Analysis")
    
    for pool in selected_pools:
        # Try to match pool from selected_pools (which are pool_symbol) with pool_col in bribes data
        # Match case-insensitive
        if not pool_bribes.empty and pool_col in pool_bribes.columns:
            pool_bribe_data = pool_bribes[
                pool_bribes[pool_col].astype(str).str.upper().str.strip() == pool.upper().strip()
            ]
        else:
            pool_bribe_data = pd.DataFrame()
        pool_main_data = df_display[df_display['pool_symbol'] == pool] if 'pool_symbol' in df_display.columns else pd.DataFrame()
        
        if not pool_bribe_data.empty:
            with st.expander(f"📊 {pool}", expanded=False):
                col_p1, col_p2, col_p3, col_p4 = st.columns(4)
                
                pool_bribes_val = pool_bribe_data[bribe_col].iloc[0] if bribe_col in pool_bribe_data.columns else 0
                pool_votes_val = pool_bribe_data[votes_col].iloc[0] if votes_col and votes_col in pool_bribe_data.columns else 0
                pool_bal_val = pool_bribe_data[bal_col].iloc[0] if bal_col and bal_col in pool_bribe_data.columns else 0
                pool_eff = pool_bribe_data['bribe_efficiency'].iloc[0] if 'bribe_efficiency' in pool_bribe_data.columns else 0
                pool_vebal_votes = pool_bribe_data['vebal_votes'].iloc[0] if 'vebal_votes' in pool_bribe_data.columns and pd.notna(pool_bribe_data['vebal_votes'].iloc[0]) else 0
                pool_vebal_pct = pool_bribe_data['vebal_pct_votes'].iloc[0] if 'vebal_pct_votes' in pool_bribe_data.columns and pd.notna(pool_bribe_data['vebal_pct_votes'].iloc[0]) else 0
                pool_vebal_rank = pool_bribe_data['vebal_ranking'].iloc[0] if 'vebal_ranking' in pool_bribe_data.columns and pd.notna(pool_bribe_data['vebal_ranking'].iloc[0]) else None
                
                col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
                
                with col_p1:
                    st.metric("Total Bribes", f"${pool_bribes_val:,.0f}")
                with col_p2:
                    st.metric("Votes Received", f"{pool_votes_val:,.0f}")
                with col_p3:
                    st.metric("BAL Received", f"{pool_bal_val:,.0f}")
                with col_p4:
                    st.metric("Efficiency", f"{pool_eff:.3f}")
                with col_p5:
                    if pool_vebal_votes > 0:
                        rank_text = f"#{int(pool_vebal_rank)}" if pool_vebal_rank else "N/A"
                        st.metric("veBAL Votes", f"{pool_vebal_votes:,.0f}", delta=f"{pool_vebal_pct*100:.2f}% share", help=f"Ranking: {rank_text}")
                    else:
                        st.metric("veBAL Votes", "N/A", help="No veBAL votes data available")
                
                if not pool_main_data.empty:
                    st.markdown("**Financial Metrics:**")
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        st.metric("Total Revenue", f"${pool_main_data['protocol_fee_amount_usd'].sum():,.0f}")
                    with col_f2:
                        st.metric("Total Incentives", f"${pool_main_data['direct_incentives'].sum():,.0f}")
                    with col_f3:
                        st.metric("DAO Profit", f"${pool_main_data['dao_profit_usd'].sum():,.0f}")
