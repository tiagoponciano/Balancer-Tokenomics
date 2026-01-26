import streamlit as st
import utils
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
import traceback
import os

st.set_page_config(page_title="Bribes Analysis", layout="wide", page_icon="💰")

# Check authentication
if not utils.check_authentication():
    st.stop()

utils.inject_css()

import streamlit.components.v1 as components

try:
    # Load data - ONLY bribes and veBAL votes
    df_bribes = utils.load_bribes_data()
    df_votes = utils.load_vebal_votes_data()  # Load veBAL votes data

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

# Initialize session state
if 'pool_filter_mode_bribes' not in st.session_state:
    st.session_state.pool_filter_mode_bribes = 'all'  # Default: show all pools
if 'show_performance_by_pool' not in st.session_state:
    st.session_state.show_performance_by_pool = False

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("Top 20", key="btn_top20_bribes"):
        st.session_state.pool_filter_mode_bribes = 'top20'
        st.session_state.show_performance_by_pool = False
        st.rerun()
with col_btn2:
    if st.button("Worst 20", key="btn_worst20_bribes"):
        st.session_state.pool_filter_mode_bribes = 'worst20'
        st.session_state.show_performance_by_pool = False
        st.rerun()

# Show "Select All" button only when a filter is active (top20 or worst20)
if st.session_state.pool_filter_mode_bribes in ['top20', 'worst20']:
    if st.sidebar.button("Select All", key="btn_select_all_bribes"):
        st.session_state.pool_filter_mode_bribes = 'all'
        st.session_state.show_performance_by_pool = False
        st.rerun()

components.html("""
<script>
console.log('[Button IDs] Script loaded via components.html (bribes_analysis.py)!');

function applyButtonIds() {
    const contexts = [
        { doc: document, name: 'document' },
        { doc: window.parent?.document, name: 'parent' },
        { doc: window.top?.document, name: 'top' }
    ];
    
    let totalButtons = 0;
    let perfButtonFound = false;
    
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
                
                // Apply IDs with correct prefixes
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
                } else if (text.includes('Show Performance') || text.includes('Performance by Pool') || textLower.includes('performance') || text.includes('🔍')) {
                    if (!button.id || button.id !== 'btn_performance_by_pool') {
                        button.id = 'btn_performance_by_pool';
                        button.classList.add('performance-button-fallback');
                        button.setAttribute('data-button-type', 'performance');
                        
                        // Apply all inline styles directly (maximum priority)
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
                    }
                }
            });
            
            totalButtons += buttons.length;
        } catch(e) {
            // Silent error handling
        }
    });
}

// Execute immediately and after delays
applyButtonIds();
setTimeout(applyButtonIds, 100);
setTimeout(applyButtonIds, 500);
setTimeout(applyButtonIds, 1000);
setTimeout(applyButtonIds, 2000);
setInterval(applyButtonIds, 3000);

// Observe DOM changes
if (window.MutationObserver) {
    const observer = new MutationObserver(() => {
        setTimeout(applyButtonIds, 100);
    });
    
    if (document.body) {
        observer.observe(document.body, { childList: true, subtree: true });
    }
    
    try {
        if (window.parent && window.parent.document && window.parent.document.body) {
            observer.observe(window.parent.document.body, { childList: true, subtree: true });
        }
    } catch(e) {}
}
</script>
""", height=0)


# Determine filter pools based on mode - using only bribes data
if st.session_state.pool_filter_mode_bribes == 'top20':
    filter_label = "Top 20 Pools"
elif st.session_state.pool_filter_mode_bribes == 'worst20':
    filter_label = "Worst 20 Pools"
else:  # 'all' - default mode, show everything
    filter_label = "All Pools"

# Prepare data based on filter mode
# Find pool column in bribes data first (used for matching)
pool_match_col = None
for col in ['pool_title', 'pool_name', 'pool_symbol', 'pool', 'symbol', 'name']:
    if col in df_bribes.columns:
        pool_match_col = col
        break

# Find pool column for aggregation (used later in the code)
pool_col = None
for col in ['pool_title', 'pool_name', 'pool_symbol', 'pool', 'gauge', 'gauge_address', 'symbol', 'name', 'Pool', 'POOL']:
    if col in df_bribes.columns:
        pool_col = col
        break


# Helper function to load aggregated CSV files (tries multiple paths)
def load_aggregated_csv(filename):
    """Load aggregated CSV file trying multiple possible paths"""
    cwd = os.getcwd()
    
    # Try different possible file paths (in order of likelihood)
    # Priority: data/ in current directory (when running from root)
    file_paths = [
        os.path.join(cwd, 'data', filename),  # data/file.csv (when running from root)
        os.path.abspath(os.path.join(cwd, 'data', filename)),  # absolute path from root
        os.path.abspath(os.path.join(cwd, '..', 'data', filename)),  # ../data/file.csv (when running from script/)
        os.path.abspath(os.path.join(cwd, '..', '..', 'data', filename)),  # ../../data/file.csv
        f'data/{filename}',  # relative
        filename  # current dir
    ]
    
    for path in file_paths:
        try:
            abs_path = os.path.abspath(path) if not os.path.isabs(path) else path
            if os.path.exists(abs_path) and os.path.getsize(abs_path) > 0:
                return pd.read_csv(abs_path)
        except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, Exception) as e:
            continue
    
    return None

# Helper function to match pools between main data and bribes data
def match_pools_in_bribes(bribes_df, main_pools, match_col):
    """Match pools from main data to bribes data using multiple strategies"""
    if match_col is None or match_col not in bribes_df.columns:
        return bribes_df.copy()  # Return all if no match column
    
    if bribes_df.empty:
        return bribes_df.copy()
    
    matched_indices = []
    main_pools_upper = [str(p).upper().strip() for p in main_pools]
    
    # First try exact match (fastest)
    exact_matches = bribes_df[
        bribes_df[match_col].astype(str).str.upper().str.strip().isin(main_pools_upper)
    ]
    if not exact_matches.empty:
        return exact_matches.copy()
    
    # If no exact match, try fuzzy matching
    for idx, row in bribes_df.iterrows():
        pool_name = str(row[match_col]).upper().strip() if pd.notna(row[match_col]) else ""
        if not pool_name:
            continue
            
        for main_pool_upper in main_pools_upper:
            # Strategy 1: Contains (either direction)
            if main_pool_upper in pool_name or pool_name in main_pool_upper:
                matched_indices.append(idx)
                break
            # Strategy 2: Remove spaces and compare
            elif main_pool_upper.replace(' ', '') in pool_name.replace(' ', '') or pool_name.replace(' ', '') in main_pool_upper.replace(' ', ''):
                matched_indices.append(idx)
                break
            # Strategy 3: Remove common suffixes/prefixes
            main_clean = main_pool_upper.replace('POOL', '').replace('LP', '').replace('-', '').strip()
            pool_clean = pool_name.replace('POOL', '').replace('LP', '').replace('-', '').strip()
            if main_clean and pool_clean and len(main_clean) > 2 and len(pool_clean) > 2:
                if main_clean in pool_clean or pool_clean in main_clean:
                    matched_indices.append(idx)
                    break
    
    if matched_indices:
        return bribes_df.loc[matched_indices].copy()
    else:
        # If no matches found, return all bribes data (better than showing empty)
        # This ensures data is still displayed even if matching fails
        return bribes_df.copy()

if st.session_state.pool_filter_mode_bribes == 'top20':
    # Top 20 mode - show only pools that have bribes data
    mode_label = "Top 20"
    
    # Load the aggregated CSV file with pools that have bribes
    try:
        df_top20_bribes = load_aggregated_csv('top20_pools_bribes_aggregated.csv')
        if df_top20_bribes is None or df_top20_bribes.empty:
            raise FileNotFoundError("CSV file not found")
        
        if 'pool_symbol' in df_top20_bribes.columns:
            # Get pools from CSV - try pool_symbol, pool_title, and pool_name
            pools_with_bribes_symbols = df_top20_bribes['pool_symbol'].unique().tolist()
            pools_with_bribes_symbols = [str(p) for p in pools_with_bribes_symbols if pd.notna(p)]
            
            # Also get pool_title and pool_name if available for better matching
            pools_with_bribes_titles = []
            pools_with_bribes_names = []
            if 'pool_title' in df_top20_bribes.columns:
                pools_with_bribes_titles = df_top20_bribes['pool_title'].dropna().unique().tolist()
                pools_with_bribes_titles = [str(p) for p in pools_with_bribes_titles if pd.notna(p)]
            if 'pool_name' in df_top20_bribes.columns:
                pools_with_bribes_names = df_top20_bribes['pool_name'].dropna().unique().tolist()
                pools_with_bribes_names = [str(p) for p in pools_with_bribes_names if pd.notna(p)]
            
            # Combine all possible pool identifiers
            all_pool_identifiers = set(pools_with_bribes_symbols + pools_with_bribes_titles + pools_with_bribes_names)
            all_pool_identifiers_upper = [p.upper().strip() for p in all_pool_identifiers]
            
            # Filter bribes data - try multiple matching strategies
            matching_mask = pd.Series([False] * len(df_bribes), index=df_bribes.index)
            
            # Try matching by pool_title
            if 'pool_title' in df_bribes.columns:
                matching_mask |= df_bribes['pool_title'].astype(str).str.upper().str.strip().isin(all_pool_identifiers_upper)
            
            # Try matching by pool_name
            if 'pool_name' in df_bribes.columns:
                matching_mask |= df_bribes['pool_name'].astype(str).str.upper().str.strip().isin(all_pool_identifiers_upper)
            
            # Try matching by pool_symbol if it exists
            if 'pool_symbol' in df_bribes.columns:
                matching_mask |= df_bribes['pool_symbol'].astype(str).str.upper().str.strip().isin(all_pool_identifiers_upper)
            
            # Try matching by pool_match_col as fallback
            if pool_match_col and pool_match_col in df_bribes.columns:
                matching_mask |= df_bribes[pool_match_col].astype(str).str.upper().str.strip().isin(all_pool_identifiers_upper)
            
            if matching_mask.any():
                df_bribes_display = df_bribes[matching_mask].copy()
            else:
                # If no matches, show all data as fallback
                df_bribes_display = df_bribes.copy()
            
            matched_count = len(pools_with_bribes_symbols)
            
            # Show warning about limited data
            st.warning(f"⚠️ **Only {matched_count} pools from Top 20 has Bribes Data.** Showing only these pools.")
            st.info(f"📊 Analysis for {mode_label} Pools with bribes data ({matched_count} of 20 pools)")
        else:
            # Fallback: show all bribes data
            df_bribes_display = df_bribes.copy()
            matched_count = len(df_bribes_display[pool_match_col].unique()) if pool_match_col and not df_bribes_display.empty else 0
            st.info(f"📊 Showing analysis for {mode_label} Pools ({matched_count} pools in bribes data)")
    except FileNotFoundError:
        st.error("❌ File `data/top20_pools_bribes_aggregated.csv` not found. Please run the script `create_top_worst_bribes_csv.py` first.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.stop()

elif st.session_state.pool_filter_mode_bribes == 'worst20':
    # Worst 20 mode - show only pools that have bribes data
    mode_label = "Worst 20"
    
    # Load the aggregated CSV file with pools that have bribes
    try:
        df_worst20_bribes = load_aggregated_csv('worst20_pools_bribes_aggregated.csv')
        if df_worst20_bribes is None or df_worst20_bribes.empty:
            raise FileNotFoundError("CSV file not found")
        
        if 'pool_symbol' in df_worst20_bribes.columns:
            # Get pools from CSV - try pool_symbol, pool_title, and pool_name
            pools_with_bribes_symbols = df_worst20_bribes['pool_symbol'].unique().tolist()
            pools_with_bribes_symbols = [str(p) for p in pools_with_bribes_symbols if pd.notna(p)]
            
            # Also get pool_title and pool_name if available for better matching
            pools_with_bribes_titles = []
            pools_with_bribes_names = []
            if 'pool_title' in df_worst20_bribes.columns:
                pools_with_bribes_titles = df_worst20_bribes['pool_title'].dropna().unique().tolist()
                pools_with_bribes_titles = [str(p) for p in pools_with_bribes_titles if pd.notna(p)]
            if 'pool_name' in df_worst20_bribes.columns:
                pools_with_bribes_names = df_worst20_bribes['pool_name'].dropna().unique().tolist()
                pools_with_bribes_names = [str(p) for p in pools_with_bribes_names if pd.notna(p)]
            
            # Combine all possible pool identifiers
            all_pool_identifiers = set(pools_with_bribes_symbols + pools_with_bribes_titles + pools_with_bribes_names)
            all_pool_identifiers_upper = [p.upper().strip() for p in all_pool_identifiers]
            
            # Filter bribes data - try multiple matching strategies
            matching_mask = pd.Series([False] * len(df_bribes), index=df_bribes.index)
            
            # Try matching by pool_title
            if 'pool_title' in df_bribes.columns:
                matching_mask |= df_bribes['pool_title'].astype(str).str.upper().str.strip().isin(all_pool_identifiers_upper)
            
            # Try matching by pool_name
            if 'pool_name' in df_bribes.columns:
                matching_mask |= df_bribes['pool_name'].astype(str).str.upper().str.strip().isin(all_pool_identifiers_upper)
            
            # Try matching by pool_symbol if it exists
            if 'pool_symbol' in df_bribes.columns:
                matching_mask |= df_bribes['pool_symbol'].astype(str).str.upper().str.strip().isin(all_pool_identifiers_upper)
            
            # Try matching by pool_match_col as fallback
            if pool_match_col and pool_match_col in df_bribes.columns:
                matching_mask |= df_bribes[pool_match_col].astype(str).str.upper().str.strip().isin(all_pool_identifiers_upper)
            
            if matching_mask.any():
                df_bribes_display = df_bribes[matching_mask].copy()
            else:
                # If no matches, show all data as fallback
                df_bribes_display = df_bribes.copy()
            
            matched_count = len(pools_with_bribes_symbols)
            
            # Show warning about limited data
            st.warning(f"⚠️ **Only {matched_count} pools from Worst 20 has Bribes Data.** Showing only these pools.")
            st.info(f"📊 Analysis for {mode_label} Pools with bribes data ({matched_count} of 20 pools)")
        else:
            # Fallback: show all bribes data
            df_bribes_display = df_bribes.copy()
            matched_count = len(df_bribes_display[pool_match_col].unique()) if pool_match_col and not df_bribes_display.empty else 0
            st.info(f"📊 Showing analysis for {mode_label} Pools ({matched_count} pools in bribes data)")
    except FileNotFoundError:
        st.error("❌ File `data/worst20_pools_bribes_aggregated.csv` not found. Please run the script `create_top_worst_bribes_csv.py` first.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.stop()

else:
    # 'all' mode - show all pools by default
    # Show all pools in bribes data
    df_bribes_display = df_bribes.copy()
    
    total_bribes_pools = len(df_bribes_display[pool_match_col].unique()) if pool_match_col and not df_bribes_display.empty else 0
    st.info(f"📊 Showing analysis for all pools ({total_bribes_pools} pools in bribes data)")

# Page Header with logout button
col_title, col_logout = st.columns([1, 0.1])
with col_title:
    st.markdown('<div class="page-title">💰 Bribes Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Comprehensive analysis of bribes, voting patterns, and their impact on BAL token distribution</div>', unsafe_allow_html=True)
with col_logout:
    utils.show_logout_button()

st.markdown("---")

# Verify pool_col was found
if pool_col is None:
    st.error("❌ Could not identify pool column in bribes data.")
    st.info(f"Available columns: {', '.join(df_bribes.columns.tolist())}")
    st.dataframe(df_bribes.head(5))
    st.stop()


try:
    # Identify bribe-related columns - always use df_bribes (original) for column identification
    # df_bribes_display is used for filtering/display, but column names come from original
    df_to_check = df_bribes
    
    bribe_col = None
    votes_col = None
    bal_col = None

    # Try to find bribe amount column (case-insensitive search)
    df_cols_lower = {col.lower(): col for col in df_to_check.columns}
    for col_lower in ['amount_usdc', 'bribe_amount_usd', 'total_bribes_usd', 'bribe_amount', 'bribes_usd', 'amount_usd', 'bribe', 'bribes', 'amount']:
        if col_lower in df_cols_lower:
            bribe_col = df_cols_lower[col_lower]
            break

    # Try to find votes column (may not exist in this dataset)
    # First check if we have veBAL votes from merge
    if 'vebal_votes' in df_to_check.columns:
        votes_col = 'vebal_votes'
    else:
        for col_lower in ['votes_received', 'votes', 'total_votes', 'vote_count', 'vote']:
            if col_lower in df_cols_lower:
                votes_col = df_cols_lower[col_lower]
                break

    # BAL column not available in bribes dataset
    # This data would come from the main financial dataset, but we're using only bribes data here
    bal_col = None
    
    # Also check for total_bribes_periodo which might be useful
    total_bribes_col = None
    if 'total_bribes_periodo' in df_to_check.columns:
        total_bribes_col = 'total_bribes_periodo'

    if bribe_col is None:
        st.error("❌ Could not find bribe amount column in the data.")
        st.info(f"Available columns: {', '.join(df_to_check.columns.tolist())}")
        st.dataframe(df_to_check.head(5))
        st.stop()
except Exception as e:
    st.error(f"❌ Error identifying columns: {str(e)}")
    st.code(traceback.format_exc())
    st.stop()

try:
    # Verify df_bribes_display has data
    if df_bribes_display.empty:
        st.warning("⚠️ No bribes data available for the selected filter.")
        pool_bribes = pd.DataFrame()
    else:
        # Aggregate bribes data by pool
        agg_dict = {bribe_col: 'sum'}
        # Votes should be 'max' not 'sum' because each gauge has unique vote count
        # If we sum, we're counting votes multiple times for the same gauge
        if votes_col:
            # Only sum if it's not veBAL votes (which are unique per gauge)
            if votes_col == 'vebal_votes':
                agg_dict[votes_col] = 'max'  # Unique per gauge, use max
            else:
                agg_dict[votes_col] = 'sum'  # Other vote types might be cumulative
        if bal_col:
            agg_dict[bal_col] = 'sum'
        # Include total_bribes_periodo if available
        if 'total_bribes_periodo' in df_bribes_display.columns:
            agg_dict['total_bribes_periodo'] = 'max'  # Use max since it's per period
        # Include veBAL votes if available
        if 'vebal_votes' in df_bribes_display.columns:
            agg_dict['vebal_votes'] = 'max'  # Unique per gauge, use max (not sum!)
        if 'vebal_pct_votes' in df_bribes_display.columns:
            agg_dict['vebal_pct_votes'] = 'mean'  # Average percentage
        if 'vebal_ranking' in df_bribes_display.columns:
            agg_dict['vebal_ranking'] = 'min'  # Best (lowest) ranking

        # Calculate metrics - aggregate by pool
        if pool_col and pool_col in df_bribes_display.columns:
            pool_bribes = df_bribes_display.groupby(pool_col).agg(agg_dict).reset_index()
        else:
            # Fallback: use pool_match_col if pool_col not available
            if pool_match_col and pool_match_col in df_bribes_display.columns:
                pool_bribes = df_bribes_display.groupby(pool_match_col).agg(agg_dict).reset_index()
                pool_col = pool_match_col  # Update pool_col for later use
            else:
                st.error("❌ Could not find pool column for aggregation.")
                st.info(f"Available columns: {', '.join(df_bribes_display.columns.tolist())}")
                pool_bribes = pd.DataFrame()
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

else:
    # Create empty columns for consistency when DataFrame is empty
    if pool_bribes.empty:
        # Create empty DataFrame with proper structure and numeric columns
        empty_cols = [pool_col, bribe_col]
        if votes_col:
            empty_cols.append('bribe_per_vote')
        pool_bribes = pd.DataFrame(columns=empty_cols)
        # Ensure numeric columns have proper dtype
        for col in ['bribe_per_vote']:
            if col in pool_bribes.columns:
                pool_bribes[col] = pool_bribes[col].astype(float)

# No merge with main data - using only bribes and veBAL votes data

# Main Metrics
st.markdown("### 📊 Key Metrics")

col1, col2, col3 = st.columns(3)

# Calculate total bribes based on filter mode
if st.session_state.pool_filter_mode_bribes == 'top20':
    # Sum amount_usdc from top20_pools_bribes_aggregated.csv
    try:
        df_top20_bribes = load_aggregated_csv('top20_pools_bribes_aggregated.csv')
        if df_top20_bribes is not None and not df_top20_bribes.empty and 'amount_usdc' in df_top20_bribes.columns:
            total_bribes = df_top20_bribes['amount_usdc'].sum()
        else:
            total_bribes = pool_bribes[bribe_col].sum() if bribe_col in pool_bribes.columns and not pool_bribes.empty else 0
    except:
        total_bribes = pool_bribes[bribe_col].sum() if bribe_col in pool_bribes.columns and not pool_bribes.empty else 0
elif st.session_state.pool_filter_mode_bribes == 'worst20':
    # Sum amount_usdc from worst20_pools_bribes_aggregated.csv
    try:
        df_worst20_bribes = load_aggregated_csv('worst20_pools_bribes_aggregated.csv')
        if df_worst20_bribes is not None and not df_worst20_bribes.empty and 'amount_usdc' in df_worst20_bribes.columns:
            total_bribes = df_worst20_bribes['amount_usdc'].sum()
        else:
            total_bribes = pool_bribes[bribe_col].sum() if bribe_col in pool_bribes.columns and not pool_bribes.empty else 0
    except:
        total_bribes = pool_bribes[bribe_col].sum() if bribe_col in pool_bribes.columns and not pool_bribes.empty else 0
else:
    # All pools - sum from pool_bribes
    total_bribes = pool_bribes[bribe_col].sum() if bribe_col in pool_bribes.columns and not pool_bribes.empty else 0

# Both Total Votes and veBAL Votes use the same source: sum of votes from veBAL_votes.csv
total_votes = df_votes['votes'].sum() if not df_votes.empty and 'votes' in df_votes.columns else 0
# For veBAL votes, sum directly from veBAL_votes.csv (same as Total Votes)
total_vebal_votes = df_votes['votes'].sum() if not df_votes.empty and 'votes' in df_votes.columns else 0

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

st.markdown("---")

# Rankings
st.markdown("### 🏆 Pool Rankings")

# Get all pools from CSV files if in Top 20 or Worst 20 mode
all_pools_for_ranking = None
if st.session_state.pool_filter_mode_bribes == 'top20':
    df_ranking = load_aggregated_csv('top20_pools_bribes_aggregated.csv')
    if df_ranking is not None and not df_ranking.empty and 'pool_symbol' in df_ranking.columns:
        all_pools_for_ranking = df_ranking[['pool_symbol', 'pool_title', 'pool_name', 'amount_usdc']].copy()
        all_pools_for_ranking = all_pools_for_ranking.rename(columns={'pool_symbol': 'pool', 'amount_usdc': 'bribe_amount'})
elif st.session_state.pool_filter_mode_bribes == 'worst20':
    df_ranking = load_aggregated_csv('worst20_pools_bribes_aggregated.csv')
    if df_ranking is not None and not df_ranking.empty and 'pool_symbol' in df_ranking.columns:
        all_pools_for_ranking = df_ranking[['pool_symbol', 'pool_title', 'pool_name', 'amount_usdc']].copy()
        all_pools_for_ranking = all_pools_for_ranking.rename(columns={'pool_symbol': 'pool', 'amount_usdc': 'bribe_amount'})

tab1, tab2, tab3 = st.tabs(["💰 Top Bribes", "📈 Most Votes", "🗳️ veBAL Votes"])

with tab1:
    if all_pools_for_ranking is not None and not all_pools_for_ranking.empty:
        # Show all pools from CSV, even if they don't have data in pool_bribes
        ranking_df = all_pools_for_ranking.copy()
        
        # Use amount_usdc from CSV as base, merge with pool_bribes if available for updated values
        if not pool_bribes.empty and bribe_col in pool_bribes.columns and pool_col in pool_bribes.columns:
            # Create a mapping from pool_bribes
            pool_bribes_dict = {}
            for idx, row in pool_bribes.iterrows():
                pool_key = str(row[pool_col]).upper().strip()
                pool_bribes_dict[pool_key] = row[bribe_col]
            
            # Try to match and update bribe amounts
            def get_bribe_amount(row):
                pool_val = str(row['pool']).upper().strip()
                title_val = str(row.get('pool_title', '')).upper().strip()
                name_val = str(row.get('pool_name', '')).upper().strip()
                
                # Try multiple matching strategies
                if pool_val in pool_bribes_dict:
                    return pool_bribes_dict[pool_val]
                elif title_val in pool_bribes_dict:
                    return pool_bribes_dict[title_val]
                elif name_val in pool_bribes_dict:
                    return pool_bribes_dict[name_val]
                else:
                    return row.get('bribe_amount', 0)
            
            ranking_df['Total Bribes (USD)'] = ranking_df.apply(get_bribe_amount, axis=1)
        else:
            ranking_df['Total Bribes (USD)'] = ranking_df.get('bribe_amount', 0)
        
        # Sort by bribe amount descending
        ranking_df = ranking_df.sort_values('Total Bribes (USD)', ascending=False)
        
        # Display all pools
        display_df = ranking_df[['pool', 'Total Bribes (USD)']].copy()
        display_df.columns = ['Pool', 'Total Bribes (USD)']
        display_df['Total Bribes (USD)'] = display_df['Total Bribes (USD)'].apply(
            lambda x: f"${float(x):,.2f}" if pd.notna(x) and float(x) > 0 else "$0.00"
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    elif bribe_col in pool_bribes.columns and not pool_bribes.empty:
        # Fallback: show from pool_bribes
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
    if all_pools_for_ranking is not None and not all_pools_for_ranking.empty:
        # Show all pools from CSV, merge with votes data from df_bribes_display
        ranking_df = all_pools_for_ranking[['pool', 'pool_title', 'pool_name']].copy()
        
        # Get votes from df_bribes_display if available
        votes_dict = {}
        if not df_bribes_display.empty:
            if votes_col and votes_col in df_bribes_display.columns:
                for pool_identifier in ['pool_title', 'pool_name', 'pool_symbol']:
                    if pool_identifier in df_bribes_display.columns:
                        pool_grouped = df_bribes_display.groupby(pool_identifier).agg({
                            votes_col: 'max'  # Use max since votes are unique per gauge
                        }).reset_index()
                        
                        for idx, row in pool_grouped.iterrows():
                            pool_key = str(row[pool_identifier]).upper().strip()
                            votes_val = pd.to_numeric(row.get(votes_col, 0), errors='coerce')
                            if pool_key not in votes_dict:  # Don't overwrite if already set
                                votes_dict[pool_key] = votes_val if pd.notna(votes_val) else 0
        
        # Match votes
        def get_votes(row):
            pool_val = str(row['pool']).upper().strip()
            title_val = str(row.get('pool_title', '')).upper().strip()
            name_val = str(row.get('pool_name', '')).upper().strip()
            
            if pool_val in votes_dict:
                return votes_dict[pool_val]
            elif title_val in votes_dict:
                return votes_dict[title_val]
            elif name_val in votes_dict:
                return votes_dict[name_val]
            else:
                return 0
        
        ranking_df['Total Votes'] = ranking_df.apply(get_votes, axis=1)
        
        # Sort by votes descending
        ranking_df = ranking_df.sort_values('Total Votes', ascending=False)
        
        # Display
        display_df = ranking_df[['pool', 'Total Votes']].copy()
        display_df.columns = ['Pool', 'Total Votes']
        display_df['Total Votes'] = display_df['Total Votes'].apply(
            lambda x: f"{float(x):,.0f}" if pd.notna(x) and float(x) > 0 else "0"
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    elif votes_col and votes_col in pool_bribes.columns and not pool_bribes.empty:
        # Fallback: show from pool_bribes
        top_votes = pool_bribes.nlargest(20, votes_col)[[pool_col, votes_col]].copy()
        top_votes.columns = ['Pool', 'Total Votes']
        top_votes['Total Votes'] = top_votes['Total Votes'].apply(lambda x: f"{x:,.0f}")
        st.dataframe(top_votes, use_container_width=True, hide_index=True)
    else:
        st.info("Votes data not available")

with tab3:
    if all_pools_for_ranking is not None and not all_pools_for_ranking.empty:
        # Show all pools from CSV, merge with veBAL votes data from df_bribes_display
        ranking_df = all_pools_for_ranking[['pool', 'pool_title', 'pool_name']].copy()
        
        # Get veBAL votes from df_bribes_display if available
        vebal_votes_dict = {}
        vebal_pct_dict = {}
        vebal_rank_dict = {}
        
        if not df_bribes_display.empty and 'vebal_votes' in df_bribes_display.columns:
            for pool_identifier in ['pool_title', 'pool_name', 'pool_symbol']:
                if pool_identifier in df_bribes_display.columns:
                    pool_grouped = df_bribes_display.groupby(pool_identifier).agg({
                        'vebal_votes': 'max',  # Use max since votes are unique per gauge
                        'vebal_pct_votes': 'mean',
                        'vebal_ranking': 'min'
                    }).reset_index()
                    
                    for idx, row in pool_grouped.iterrows():
                        pool_key = str(row[pool_identifier]).upper().strip()
                        if pool_key not in vebal_votes_dict:  # Don't overwrite if already set
                            vebal_votes_dict[pool_key] = pd.to_numeric(row.get('vebal_votes', 0), errors='coerce') if pd.notna(row.get('vebal_votes')) else 0
                            vebal_pct_dict[pool_key] = pd.to_numeric(row.get('vebal_pct_votes', 0), errors='coerce') if pd.notna(row.get('vebal_pct_votes')) else 0
                            vebal_rank_dict[pool_key] = pd.to_numeric(row.get('vebal_ranking', None), errors='coerce') if pd.notna(row.get('vebal_ranking')) else None
        
        # Match veBAL data
        def get_vebal_votes(row):
            pool_val = str(row['pool']).upper().strip()
            title_val = str(row.get('pool_title', '')).upper().strip()
            name_val = str(row.get('pool_name', '')).upper().strip()
            
            if pool_val in vebal_votes_dict:
                return vebal_votes_dict[pool_val]
            elif title_val in vebal_votes_dict:
                return vebal_votes_dict[title_val]
            elif name_val in vebal_votes_dict:
                return vebal_votes_dict[name_val]
            else:
                return 0
        
        def get_vebal_pct(row):
            pool_val = str(row['pool']).upper().strip()
            title_val = str(row.get('pool_title', '')).upper().strip()
            name_val = str(row.get('pool_name', '')).upper().strip()
            
            if pool_val in vebal_pct_dict:
                return vebal_pct_dict[pool_val]
            elif title_val in vebal_pct_dict:
                return vebal_pct_dict[title_val]
            elif name_val in vebal_pct_dict:
                return vebal_pct_dict[name_val]
            else:
                return 0
        
        def get_vebal_rank(row):
            pool_val = str(row['pool']).upper().strip()
            title_val = str(row.get('pool_title', '')).upper().strip()
            name_val = str(row.get('pool_name', '')).upper().strip()
            
            if pool_val in vebal_rank_dict:
                return vebal_rank_dict[pool_val]
            elif title_val in vebal_rank_dict:
                return vebal_rank_dict[title_val]
            elif name_val in vebal_rank_dict:
                return vebal_rank_dict[name_val]
            else:
                return None
        
        ranking_df['veBAL Votes'] = ranking_df.apply(get_vebal_votes, axis=1)
        ranking_df['Vote Share %'] = ranking_df.apply(get_vebal_pct, axis=1)
        ranking_df['Ranking'] = ranking_df.apply(get_vebal_rank, axis=1)
        
        # Sort by veBAL votes descending
        ranking_df = ranking_df.sort_values('veBAL Votes', ascending=False)
        
        # Display
        display_df = ranking_df[['pool', 'veBAL Votes', 'Vote Share %', 'Ranking']].copy()
        display_df.columns = ['Pool', 'veBAL Votes', 'Vote Share %', 'Ranking']
        display_df['veBAL Votes'] = display_df['veBAL Votes'].apply(
            lambda x: f"{float(x):,.0f}" if pd.notna(x) and float(x) > 0 else "0"
        )
        display_df['Vote Share %'] = display_df['Vote Share %'].apply(
            lambda x: f"{float(x)*100:.2f}%" if pd.notna(x) and float(x) > 0 else "0.00%"
        )
        display_df['Ranking'] = display_df['Ranking'].apply(
            lambda x: f"#{int(x)}" if pd.notna(x) else "N/A"
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Add visualization if there's data
        vebal_with_data = ranking_df[ranking_df['veBAL Votes'] > 0]
        if not vebal_with_data.empty:
            st.markdown("#### 📊 Top Pools by veBAL Votes")
            top_10_vebal = vebal_with_data.nlargest(10, 'veBAL Votes')
            fig_vebal = px.bar(
                top_10_vebal,
                x='pool',
                y='veBAL Votes',
                title="Top Pools by veBAL Votes",
                labels={'veBAL Votes': 'veBAL Votes', 'pool': 'Pool'},
                color='veBAL Votes',
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
    elif 'vebal_votes' in pool_bribes.columns:
        # Fallback: show from pool_bribes
        vebal_data = pool_bribes[pool_bribes['vebal_votes'].notna() & (pool_bribes['vebal_votes'] > 0)].copy()
        if not vebal_data.empty:
            top_vebal = vebal_data.nlargest(20, 'vebal_votes')[[pool_col, 'vebal_votes', 'vebal_pct_votes', 'vebal_ranking']].copy()
            top_vebal.columns = ['Pool', 'veBAL Votes', 'Vote Share %', 'Ranking']
            top_vebal['veBAL Votes'] = top_vebal['veBAL Votes'].apply(lambda x: f"{x:,.0f}")
            top_vebal['Vote Share %'] = top_vebal['Vote Share %'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A")
            top_vebal['Ranking'] = top_vebal['Ranking'].apply(lambda x: f"#{int(x)}" if pd.notna(x) else "N/A")
            st.dataframe(top_vebal, use_container_width=True, hide_index=True)
            
            # Add visualization
            st.markdown("#### 📊 Top Pools by veBAL Votes")
            top_10_vebal = vebal_data.nlargest(10, 'vebal_votes')
            fig_vebal = px.bar(
                top_10_vebal,
                x=pool_col,
                y='vebal_votes',
                title="Top Pools by veBAL Votes",
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

# Performance by Pool button (shown in all modes)
st.markdown("### 📊 Performance by Pool")

col_btn_perf, col_info = st.columns([1, 4])
with col_btn_perf:
    if st.button("🔍 Show Performance by Pool", key="btn_performance_by_pool"):
        st.session_state.show_performance_by_pool = not st.session_state.show_performance_by_pool
        st.rerun()

if st.session_state.show_performance_by_pool:
    if st.session_state.pool_filter_mode_bribes == 'top20':
        mode_label = "Top"
        # Get pools from top20 CSV
        try:
            df_top20_bribes = load_aggregated_csv('top20_pools_bribes_aggregated.csv')
            if df_top20_bribes is not None and not df_top20_bribes.empty and 'pool_symbol' in df_top20_bribes.columns:
                category_pools = df_top20_bribes['pool_symbol'].unique().tolist()
                category_pools = [str(p) for p in category_pools if pd.notna(p)]
            else:
                category_pools = []
        except:
            category_pools = []
    elif st.session_state.pool_filter_mode_bribes == 'worst20':
        mode_label = "Worst"
        # Get pools from worst20 CSV
        try:
            df_worst20_bribes = load_aggregated_csv('worst20_pools_bribes_aggregated.csv')
            if df_worst20_bribes is not None and not df_worst20_bribes.empty and 'pool_symbol' in df_worst20_bribes.columns:
                category_pools = df_worst20_bribes['pool_symbol'].unique().tolist()
                category_pools = [str(p) for p in category_pools if pd.notna(p)]
            else:
                category_pools = []
        except:
            category_pools = []
    else:
        mode_label = "All"
        # Get all pools from bribes data
        if pool_match_col and not df_bribes_display.empty:
            category_pools = df_bribes_display[pool_match_col].unique().tolist()
            category_pools = [str(p) for p in category_pools if pd.notna(p)]
        else:
            category_pools = []
    
    st.markdown(f"#### {mode_label} Pools - Individual Performance")
    
    # Get aggregated CSV data for Top/Worst 20
    csv_data = None
    if st.session_state.pool_filter_mode_bribes == 'top20':
        csv_data = load_aggregated_csv('top20_pools_bribes_aggregated.csv')
    elif st.session_state.pool_filter_mode_bribes == 'worst20':
        csv_data = load_aggregated_csv('worst20_pools_bribes_aggregated.csv')
    
    for pool in category_pools:
        # Try to match pool from category_pools with df_bribes_display
        pool_bribe_data = pd.DataFrame()
        
        # First, try to get data from df_bribes_display using multiple matching strategies
        if not df_bribes_display.empty:
            # Try matching by pool_symbol, pool_title, pool_name
            for match_col in ['pool_symbol', 'pool_title', 'pool_name']:
                if match_col in df_bribes_display.columns:
                    matches = df_bribes_display[
                        df_bribes_display[match_col].astype(str).str.upper().str.strip() == pool.upper().strip()
                    ]
                    if not matches.empty:
                        pool_bribe_data = matches
                        break
        
        # If no match in df_bribes_display, try to get from CSV aggregated data
        if pool_bribe_data.empty and csv_data is not None and not csv_data.empty:
            csv_match = csv_data[
                csv_data['pool_symbol'].astype(str).str.upper().str.strip() == pool.upper().strip()
            ]
            if not csv_match.empty:
                # Create a minimal pool_bribe_data from CSV
                pool_bribe_data = csv_match.iloc[[0]].copy()
                # Map CSV columns to expected columns
                if 'amount_usdc' in pool_bribe_data.columns:
                    pool_bribe_data[bribe_col] = pool_bribe_data['amount_usdc']
        
        # If still empty, try pool_bribes as fallback
        if pool_bribe_data.empty and not pool_bribes.empty and pool_col in pool_bribes.columns:
            pool_bribe_data = pool_bribes[
                pool_bribes[pool_col].astype(str).str.upper().str.strip() == pool.upper().strip()
            ]
        
        # Show pool data even if empty (to show all pools from category)
        with st.expander(f"📊 {pool}", expanded=False):
            if not pool_bribe_data.empty:
                col_p1, col_p2, col_p3 = st.columns(3)
                
                # Get values from pool_bribe_data
                pool_bribes_val = 0
                if bribe_col in pool_bribe_data.columns:
                    pool_bribes_val = pd.to_numeric(pool_bribe_data[bribe_col].iloc[0], errors='coerce') if pd.notna(pool_bribe_data[bribe_col].iloc[0]) else 0
                elif 'amount_usdc' in pool_bribe_data.columns:
                    pool_bribes_val = pd.to_numeric(pool_bribe_data['amount_usdc'].iloc[0], errors='coerce') if pd.notna(pool_bribe_data['amount_usdc'].iloc[0]) else 0
                
                pool_votes_val = pd.to_numeric(pool_bribe_data[votes_col].iloc[0], errors='coerce') if votes_col and votes_col in pool_bribe_data.columns and pd.notna(pool_bribe_data[votes_col].iloc[0]) else 0
                pool_vebal_votes = pd.to_numeric(pool_bribe_data['vebal_votes'].iloc[0], errors='coerce') if 'vebal_votes' in pool_bribe_data.columns and pd.notna(pool_bribe_data['vebal_votes'].iloc[0]) else 0
                pool_vebal_pct = pd.to_numeric(pool_bribe_data['vebal_pct_votes'].iloc[0], errors='coerce') if 'vebal_pct_votes' in pool_bribe_data.columns and pd.notna(pool_bribe_data['vebal_pct_votes'].iloc[0]) else 0
                pool_vebal_rank = pd.to_numeric(pool_bribe_data['vebal_ranking'].iloc[0], errors='coerce') if 'vebal_ranking' in pool_bribe_data.columns and pd.notna(pool_bribe_data['vebal_ranking'].iloc[0]) else None
                
                with col_p1:
                    st.metric("Total Bribes", f"${pool_bribes_val:,.0f}")
                with col_p2:
                    st.metric("Votes Received", f"{pool_votes_val:,.0f}")
                with col_p3:
                    if pool_vebal_votes > 0:
                        rank_text = f"#{int(pool_vebal_rank)}" if pool_vebal_rank else "N/A"
                        st.metric("veBAL Votes", f"{pool_vebal_votes:,.0f}", delta=f"{pool_vebal_pct*100:.2f}% share", help=f"Ranking: {rank_text}")
                    else:
                        st.metric("veBAL Votes", "N/A", help="No veBAL votes data available")
            else:
                # Show data from CSV if available, even if not in df_bribes_display
                if csv_data is not None and not csv_data.empty:
                    csv_match = csv_data[
                        csv_data['pool_symbol'].astype(str).str.upper().str.strip() == pool.upper().strip()
                    ]
                    if not csv_match.empty:
                        csv_row = csv_match.iloc[0]
                        col_p1, col_p2, col_p3 = st.columns(3)
                        
                        pool_bribes_val = csv_row.get('amount_usdc', 0) if pd.notna(csv_row.get('amount_usdc')) else 0
                        
                        with col_p1:
                            st.metric("Total Bribes", f"${pool_bribes_val:,.0f}")
                        with col_p2:
                            st.metric("Votes Received", "N/A", help="No votes data available")
                        with col_p3:
                            st.metric("veBAL Votes", "N/A", help="No veBAL votes data available")
                    else:
                        st.info("No data available for this pool")
                else:
                    st.info("No data available for this pool")

st.markdown("---")

# Visualizations
st.markdown("### 📈 Visualizations")

viz_col1, viz_col2, viz_col3 = st.columns(3)

with viz_col1:
    if bribe_col in pool_bribes.columns and not pool_bribes.empty:
        scatter_data = pool_bribes[pool_bribes[bribe_col] > 0].copy()
        if not scatter_data.empty:
            fig_scatter = px.scatter(
                scatter_data,
                x=pool_col,
                y=bribe_col,
                hover_data=[pool_col],
                title="💰 Bribe Amount by Pool",
                labels={bribe_col: 'Total Bribes (USD)', pool_col: 'Pool'},
                color=bribe_col,
                color_continuous_scale='Viridis',
                size=bribe_col,
                size_max=20
            )
            fig_scatter.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title=dict(font=dict(color='white', size=16)),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickangle=-45),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No data available for scatter plot")
    else:
        st.info("Bribe data not available")

with viz_col2:
    # Use veBAL votes instead of votes_col for the scatter plot
    if 'vebal_votes' in pool_bribes.columns and bribe_col in pool_bribes.columns and not pool_bribes.empty:
        votes_data = pool_bribes[
            (pool_bribes[bribe_col] > 0) & 
            (pool_bribes['vebal_votes'].notna()) & 
            (pool_bribes['vebal_votes'] > 0)
        ].copy()
        if not votes_data.empty:
            # Ensure numeric values
            votes_data['vebal_votes'] = pd.to_numeric(votes_data['vebal_votes'], errors='coerce')
            votes_data = votes_data[votes_data['vebal_votes'].notna() & (votes_data['vebal_votes'] > 0)]
            if not votes_data.empty:
                fig_votes = px.scatter(
                    votes_data,
                    x=bribe_col,
                    y='vebal_votes',
                    hover_data=[pool_col],
                    title="📊 Bribes vs veBAL Votes",
                    labels={bribe_col: 'Total Bribes (USD)', 'vebal_votes': 'veBAL Votes'},
                    color='vebal_votes',
                    color_continuous_scale='Blues',
                    size='vebal_votes',
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

# Top pools bar chart
st.markdown("---")
st.markdown("#### 🏅 Top Pools by Total Bribes")
if bribe_col in pool_bribes.columns and not pool_bribes.empty:
    top_10 = pool_bribes.nlargest(10, bribe_col)
    fig_bar = px.bar(
        top_10,
        x=pool_col,
        y=bribe_col,
        title="Top Pools by Bribe Amount",
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

# Detailed Pool Analysis (only for 'all' mode - shows all pools)
if st.session_state.pool_filter_mode_bribes == 'all':
    st.markdown("---")
    st.markdown("### 🔍 Detailed Pool Analysis")
    
    # Get all pools from bribes data
    if pool_match_col and not df_bribes_display.empty:
        all_pools = df_bribes_display[pool_match_col].unique().tolist()
        all_pools = [str(p) for p in all_pools if pd.notna(p)]
    else:
        all_pools = []
    
    # Show analysis for all pools
    for pool in all_pools:
        # Try to match pool from selected_pools (which are pool_symbol) with pool_col in bribes data
        # Match case-insensitive
        if not pool_bribes.empty and pool_col in pool_bribes.columns:
            pool_bribe_data = pool_bribes[
                pool_bribes[pool_col].astype(str).str.upper().str.strip() == pool.upper().strip()
            ]
        else:
            pool_bribe_data = pd.DataFrame()
        if not pool_bribe_data.empty:
            with st.expander(f"📊 {pool}", expanded=False):
                col_p1, col_p2, col_p3 = st.columns(3)
                
                pool_bribes_val = pool_bribe_data[bribe_col].iloc[0] if bribe_col in pool_bribe_data.columns else 0
                pool_votes_val = pool_bribe_data[votes_col].iloc[0] if votes_col and votes_col in pool_bribe_data.columns else 0
                pool_vebal_votes = pool_bribe_data['vebal_votes'].iloc[0] if 'vebal_votes' in pool_bribe_data.columns and pd.notna(pool_bribe_data['vebal_votes'].iloc[0]) else 0
                pool_vebal_pct = pool_bribe_data['vebal_pct_votes'].iloc[0] if 'vebal_pct_votes' in pool_bribe_data.columns and pd.notna(pool_bribe_data['vebal_pct_votes'].iloc[0]) else 0
                pool_vebal_rank = pool_bribe_data['vebal_ranking'].iloc[0] if 'vebal_ranking' in pool_bribe_data.columns and pd.notna(pool_bribe_data['vebal_ranking'].iloc[0]) else None
                
                col_p1, col_p2, col_p3 = st.columns(3)
                
                with col_p1:
                    st.metric("Total Bribes", f"${pool_bribes_val:,.0f}")
                with col_p2:
                    st.metric("Votes Received", f"{pool_votes_val:,.0f}")
                with col_p3:
                    if pool_vebal_votes > 0:
                        rank_text = f"#{int(pool_vebal_rank)}" if pool_vebal_rank else "N/A"
                        st.metric("veBAL Votes", f"{pool_vebal_votes:,.0f}", delta=f"{pool_vebal_pct*100:.2f}% share", help=f"Ranking: {rank_text}")
                    else:
                        st.metric("veBAL Votes", "N/A", help="No veBAL votes data available")
                
