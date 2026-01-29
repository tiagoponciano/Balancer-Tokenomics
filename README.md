# Balancer Tokenomics Analysis Dashboard

Professional Streamlit dashboard for comprehensive analysis of Balancer tokenomics, focusing on revenue distribution, pool classification, emission impact, bribes, and voting patterns.

## 🎯 Objective

Create a comprehensive Streamlit application to analyze historical Balancer tokenomics data, allowing users to:

- Analyze historical revenue distribution (DAO, veBAL/BAL Holders, Incentives)
- Classify pools as Legitimate vs Mercenary based on objective criteria
- Simulate custom emission reduction scenarios (0-100%) and analyze impact
- View weekly aggregation of emissions, votes, and distribution patterns
- Analyze bribes and their correlation with voting patterns
- Examine veBAL voting distribution across gauges

## 🚀 Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Place your data file:**
   - Place `Balancer-Tokenomics.csv` in the `data/` directory
   - This is a merged dataset containing financial data, bribes, votes, and emissions
   - The file should include columns: `block_date`, `pool_symbol`, `protocol_fee_amount_usd`, `bribe_amount_usd`, `votes_received`, `bal_emited_votes`, `direct_incentives`, `dao_profit_usd`, `pool_category`, `is_core_pool`

3. **Set up environment variables:**
Create a `.env` file with your credentials:
```
# Authentication (required)
LOGIN_USERNAME=your_username
LOGIN_PASSWORD=your_password

# Supabase Configuration (required for deployment)
SUPABASE_URL=https://your-project.supabase.co
# For public buckets:
SUPABASE_ANON_KEY=your-anon-key
# For private buckets (recommended):
# SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_BUCKET=data
```

4. **Run the dashboard:**
```bash
cd script
streamlit run home.py
```

## 📊 Features

### Main Page (Home)
- Overview of total revenue, incentives, DAO profit, and BAL emitted
- Pool classification summary (Legitimate, Mercenary, Undefined)
- **Monthly revenue distribution charts** (bar charts):
  - DAO Revenue over time
  - Holders Revenue (veBAL) over time
  - Incentives Revenue over time
- **Comparison chart**: Monthly comparison between DAO vs veBAL revenue
- Simulation controls for revenue distribution (Core vs Non-Core pools)
- Filter pools by Top 20, Worst 20, or All
- Date filter: Year and Quarter selection

### Pool Classification
- **Understanding Pool Classification** section with expandable explanations
- Detailed breakdown of pool categories (Legitimate, Mercenary, Undefined, Core)
- Historical distribution of **bribes** (not direct incentives) by category
- Monthly trends of bribes and DAO profit with **percentage toggle**
- Individual pool analysis when filtering by Top 20 or Worst 20
- Filter pools by Top 20, Worst 20, or All
- Date filter: Year and Quarter selection

### Emission Impact Analysis
- **Custom BAL Emission Reduction** input (0-100%) instead of fixed scenarios
- **Core Pools Only** toggle to restrict emissions to core pools
- Compare impact on Legitimate vs Mercenary pools
- Compare impact on Core vs Non-Core pools with **percentage toggle**
- **Percentage toggle** for Legitimate vs Mercenary emissions chart
- Visualize profit changes and incentive reductions
- Dynamic conclusion based on impact analysis
- Filter pools by Top 20, Worst 20, or All
- Date filter: Year and Quarter selection

### Bribes Analysis
- Comprehensive analysis of **bribes** (voting incentives) and voting patterns
- Total bribes calculation from `bribe_amount_usd` column
- Top pools by bribe amount and votes received
- **Monthly bribe timeline** visualization
- Performance metrics by pool (sorted by bribe amount)
- Monetary values displayed without cents
- Filter pools by Top 20, Worst 20, or All
- Date filter: Year and Quarter selection

### veBAL Votes Analysis
- Current voting distribution across Balancer gauges
- Key metrics: total votes, gauge count, concentration analysis
- Top gauges by vote share with interactive bar charts
- Vote share pie charts and treemap visualizations
- Cumulative vote distribution analysis
- **Full table with animated filters**:
  - Search gauge functionality
  - Minimum votes and minimum share filters
  - Sort by votes, ranking, or percentage
- HHI (Herfindahl-Hirschman Index) for market concentration
- Filter gauges by Top 20 or Worst 20 pools
- Date filter: Year and Quarter selection

### Weekly Analysis
- Weekly aggregation of emissions and votes
- **BAL Emission Reduction Scenario** controls (same as Emission Impact page)
- Distribution patterns by category with **percentage toggles** for both charts:
  - Weekly BAL Emissions by Category
  - Weekly Incentives Distribution
- Percentage of weekly emissions per category
- Individual pool weekly analysis when filtering by Top 20 or Worst 20
- Filter pools by Top 20, Worst 20, or All
- Date filter: Year and Quarter selection

## 📁 Project Structure

```
Balancer-Tokenomics/
├── script/
│   ├── home.py                    # Main dashboard page
│   ├── utils.py                    # Shared utilities, data loading, authentication
│   └── pages/
│       ├── pool_classification.py  # Pool classification analysis
│       ├── emission_impact.py      # Emission reduction impact analysis
│       ├── bribes_analysis.py      # Bribes and voting pattern analysis
│       ├── vebal_votes.py          # veBAL votes distribution analysis
│       └── weekly_analysis.py      # Weekly aggregation and voting patterns
├── data generator/
│   ├── create_top_worst_bribes_csv.py  # Generate aggregated CSVs for bribes
│   ├── create_top_worst_votes_csv.py   # Generate aggregated CSVs for votes
│   └── list_top_worst_pools.py         # List Top/Worst pools utility
├── data/
│   └── Balancer-Tokenomics.csv                 # Merged dataset (financial, bribes, votes, emissions)
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 Pool Classification Criteria

Pools are automatically classified based on objective criteria. Detailed explanations are available in the Pool Classification and Emission Impact pages:

**Legitimate Pools:**
- Pools that generate positive DAO profit (revenue > bribes)
- Have good emissions ROI (revenue/bribes > 1.0)
- Generate meaningful revenue (>$10k) even without bribes
- Core pools with ROI > 0.7 are typically classified as legitimate

**Mercenary Pools:**
- Pools that generate negative DAO profit (revenue < bribes)
- Have poor emissions ROI (revenue/bribes < 0.5)
- Highly dependent on bribes (>80% of revenue comes from bribes)
- Generate little to no revenue without bribes

**Undefined Pools:**
- Pools that don't clearly fit into either category
- May have no bribes but also low revenue
- Require further analysis to classify

**Core Pools:**
- Pools designated as "core" by the protocol
- Typically receive priority in emissions distribution
- May have different revenue distribution rules

**Note:** The analysis focuses on **bribes** (voting incentives). Direct incentives are not considered in the classification.

## 🎛️ Filtering System

All pages support consistent filtering options:

- **Top 20**: Shows only the top 20 pools ranked by `dao_profit_usd`
- **Worst 20**: Shows only the worst 20 pools ranked by `dao_profit_usd`
- **Select All**: Returns to showing all pools (only visible when a filter is active)
- **Date Filter**: Year and Quarter selection (available on all pages)

The filtering is consistent across all pages and based on the same metric (`dao_profit_usd`) from the main dataset.

### Emission Reduction Scenarios

The **Emission Impact** and **Weekly Analysis** pages include additional controls:

- **BAL Emission Reduction (%)**: Custom input (0-100%) to simulate emission reductions
- **Allow emissions only for Core Pools**: Toggle to restrict emissions to core pools only

These controls allow you to analyze the impact of different emission reduction scenarios on legitimate vs mercenary pools.

## 📈 Key Metrics

- **Total Revenue**: Sum of all protocol fees collected
- **Total Bribes**: Sum of all voting incentives (bribes) distributed
- **Total Incentives**: Sum of all direct incentives (not used in classification)
- **DAO Profit**: Net profit (Revenue - Incentives)
- **Total BAL Emitted**: Total BAL tokens emitted historically
- **HHI Index**: Herfindahl-Hirschman Index for market concentration (0-10000 scale)
- **Gini Coefficient**: Measure of inequality in vote distribution (0 = perfect equality, 1 = perfect inequality)

## 🎨 Interactive Features

### Percentage Toggles
Multiple charts support toggling between absolute values and percentage views:
- **Emission Impact**: Legitimate vs Mercenary emissions, Core vs Non-Core emissions
- **Pool Classification**: Monthly bribes distribution
- **Weekly Analysis**: Weekly BAL emissions and incentives distribution

### Revenue Distribution Simulation
The home page includes simulation controls for revenue distribution:
- **Core Pools**: 70% → Voting Incentives (Bribes), 12.5% → veBAL Holders, 17.5% → DAO Treasury
- **Non-Core Pools**: 82.5% → veBAL Holders, 17.5% → DAO Treasury

These percentages can be adjusted via sidebar sliders to simulate different distribution scenarios.

## 🔐 Authentication

The dashboard includes authentication to protect access. Default credentials can be set via environment variables:
- `LOGIN_USERNAME`: Username for login
- `LOGIN_PASSWORD`: Password for login

## 📊 Data Sources

- **Main Financial Data**: `Balancer-Tokenomics.csv` (merged dataset)
  - Historical protocol fees, incentives, DAO profit, emissions
  - Pool classification and core pool indicators
  - Bribe amounts (`bribe_amount_usd` column)
  - Votes received (`votes_received` column)
  - BAL emissions (`bal_emited_votes` column)
  
The application uses a single merged CSV file (`Balancer-Tokenomics.csv`) that combines:
- Financial data (protocol fees, DAO profit)
- Bribes data (bribe amounts, gauge mappings)
- Votes data (veBAL voting distribution)
- Emissions data (BAL emissions per pool)

## 🛠️ Data Generation Scripts

The project includes utility scripts in the `data generator/` directory:

1. **create_top_worst_bribes_csv.py**
   - Generates aggregated CSV files for Top/Worst 20 pools (bribes)
   - Useful for generating filtered datasets

2. **create_top_worst_votes_csv.py**
   - Generates aggregated CSV files for Top/Worst 20 pools (votes)
   - Useful for generating filtered datasets

3. **merge_balancer_delivery.py**
   - Merges multiple data sources into the main `Balancer-Tokenomics.csv` file

**Note:** The main application uses the merged `Balancer-Tokenomics.csv` file directly, so these scripts are optional utilities.

## 🎨 Design

- Minimalist and professional dark theme
- Inter font family
- Gradient accents for titles and highlights
- Responsive layout with sidebar navigation
- Consistent button styling across all pages with smooth animations
- Interactive Plotly charts with dark theme
- Animated filters and inputs with hover effects
- Custom CSS animations for buttons and selectboxes
- Color-coded charts:
  - DAO Revenue: `#67A2E1` (blue)
  - Holders Revenue: `#E9A97B` (orange)
  - Incentives Revenue: `#B1ACF1` (purple)
  - Legitimate Pools: `#2ecc71` (green)
  - Mercenary Pools: `#e74c3c` (red)
  - Undefined Pools: `#95a5a6` (gray)

## 📝 Requirements

- Python 3.8+
- streamlit
- pandas
- plotly
- numpy
- python-dotenv (for environment variables)
- supabase (for Supabase Storage integration)

## 🔮 Future Enhancements

- Automated data updates from on-chain sources
- Real-time bribe data integration (Votium, Hidden Hand)
- Voter profile analysis
- Self-voting pattern detection
- Advanced correlation analysis between bribes and votes
- Export functionality for reports

## 📄 License

This project is for internal use and analysis of Balancer tokenomics data.
