# Balancer Tokenomics Analysis Dashboard

Professional Streamlit dashboard for comprehensive analysis of Balancer tokenomics, focusing on revenue distribution, pool classification, emission impact, bribes, and voting patterns.

## 🎯 Objective

Create a comprehensive Streamlit application to analyze historical Balancer tokenomics data, allowing users to:

- Analyze historical revenue distribution (DAO, veBAL/BAL Holders, Incentives)
- Classify pools as Legitimate vs Mercenary based on objective criteria
- Simulate emission reduction scenarios (50%, 70%) and analyze impact
- View weekly aggregation of emissions, votes, and distribution patterns
- Analyze bribes and their correlation with voting patterns
- Examine veBAL voting distribution across gauges

## 🚀 Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables (optional):**
Create a `.env` file with authentication credentials:
```
LOGIN_USERNAME=your_username
LOGIN_PASSWORD=your_password
```

3. **Generate aggregated data files (optional but recommended):**
```bash
# Generate Top 20 and Worst 20 pools aggregated data for bribes
python3 "data generator/create_top_worst_bribes_csv.py"

# Generate Top 20 and Worst 20 pools aggregated data for votes
python3 "data generator/create_top_worst_votes_csv.py"
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
- Historical revenue trends over time
- Simulation controls for protocol fee percentage and revenue share
- Filter pools by Top 20, Worst 20, or All

### Pool Classification
- Detailed breakdown of pool categories
- Historical distribution of BAL by category
- Monthly trends of incentives and DAO profit
- Individual pool analysis when filtering by Top 20 or Worst 20
- Filter pools by Top 20, Worst 20, or All

### Emission Impact Analysis
- Simulate 50% and 70% emission reduction scenarios
- Compare impact on Legitimate vs Mercenary pools
- Compare impact on Core vs Non-Core pools
- Visualize profit changes and incentive reductions
- Key insights for each scenario
- Filter pools by Top 20, Worst 20, or All

### Bribes Analysis
- Comprehensive analysis of bribes and voting patterns
- Top pools by bribe amount and votes received
- Correlation between bribes and veBAL votes
- Timeline visualization of bribe distribution
- Performance metrics by pool
- Filter pools by Top 20, Worst 20, or All (based on dao_profit_usd)

### veBAL Votes Analysis
- Current voting distribution across Balancer gauges
- Key metrics: total votes, gauge count, concentration analysis
- Top gauges by vote share
- Distribution charts and vote share pie charts
- HHI (Herfindahl-Hirschman Index) for market concentration
- Filter gauges by Top 20 or Worst 20 pools (based on dao_profit_usd)

### Weekly Analysis
- Weekly aggregation of emissions and votes
- Distribution patterns by category
- Percentage of weekly emissions per category
- Individual pool weekly analysis when filtering by Top 20 or Worst 20
- Filter pools by Top 20, Worst 20, or All

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
│   ├── balancer_v2_financial_master_final.csv  # Main financial data
│   ├── Balancer_Bribes_Gauges_enriched.csv     # Bribes and gauges data
│   ├── veBAL_votes.csv                         # veBAL voting data
│   ├── top20_pools_bribes_aggregated.csv       # Generated: Top 20 pools (bribes)
│   ├── worst20_pools_bribes_aggregated.csv     # Generated: Worst 20 pools (bribes)
│   ├── top20_pools_votes_aggregated.csv        # Generated: Top 20 pools (votes)
│   └── worst20_pools_votes_aggregated.csv      # Generated: Worst 20 pools (votes)
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 Pool Classification Criteria

Pools are automatically classified based on objective criteria:

**Mercenary Pools:**
- Low Emissions ROI (< 0.5)
- Negative DAO Profit (< -$1,000)
- High Incentive Dependency (> 80%)
- Low Revenue Generation (< $10,000)

**Legitimate Pools:**
- Positive DAO profit
- ROI > 1.0
- Meaningful revenue contribution
- Core Pools with strategic importance

**Undefined Pools:**
- Pools that don't clearly fit into Legitimate or Mercenary categories
- Pools with no incentives but low revenue

## 🎛️ Filtering System

All pages support consistent filtering options:

- **Top 20**: Shows only the top 20 pools ranked by `dao_profit_usd`
- **Worst 20**: Shows only the worst 20 pools ranked by `dao_profit_usd`
- **Select All**: Returns to showing all pools (only visible when a filter is active)

The filtering is consistent across all pages and based on the same metric (`dao_profit_usd`) from the main dataset.

## 📈 Key Metrics

- **Total Revenue**: Sum of all protocol fees collected
- **Total Incentives**: Sum of all BAL incentives distributed
- **DAO Profit**: Net profit (Revenue - Incentives)
- **Total BAL Emitted**: Total BAL tokens emitted historically
- **HHI Index**: Herfindahl-Hirschman Index for market concentration (0-10000 scale)

## 🔐 Authentication

The dashboard includes authentication to protect access. Default credentials can be set via environment variables:
- `LOGIN_USERNAME`: Username for login
- `LOGIN_PASSWORD`: Password for login

## 📊 Data Sources

- **Main Financial Data**: `balancer_v2_financial_master_final.csv`
  - Historical protocol fees, incentives, DAO profit, emissions
  - Pool classification and core pool indicators
  
- **Bribes Data**: `Balancer_Bribes_Gauges_enriched.csv`
  - Bribe amounts, gauge addresses, pool mappings
  - Voting patterns and correlations
  
- **Votes Data**: `veBAL_votes.csv`
  - Current veBAL voting distribution
  - Gauge addresses and vote percentages

## 🛠️ Data Generation Scripts

The project includes scripts to generate aggregated CSV files for efficient filtering:

1. **create_top_worst_bribes_csv.py**
   - Generates `top20_pools_bribes_aggregated.csv` and `worst20_pools_bribes_aggregated.csv`
   - Aggregates bribes data for Top/Worst 20 pools based on `dao_profit_usd`
   - Maps gauge addresses to pool symbols

2. **create_top_worst_votes_csv.py**
   - Generates `top20_pools_votes_aggregated.csv` and `worst20_pools_votes_aggregated.csv`
   - Aggregates votes data for Top/Worst 20 pools based on `dao_profit_usd`
   - Uses bribes data as bridge for gauge-to-pool mapping

## 🎨 Design

- Minimalist and professional dark theme
- Inter font family
- Gradient accents for titles and highlights
- Responsive layout with sidebar navigation
- Consistent button styling across all pages
- Interactive Plotly charts with dark theme

## 📝 Requirements

- Python 3.8+
- streamlit
- pandas
- plotly
- numpy
- python-dotenv (for environment variables)

## 🔮 Future Enhancements

- Automated data updates from on-chain sources
- Real-time bribe data integration (Votium, Hidden Hand)
- Voter profile analysis
- Self-voting pattern detection
- Advanced correlation analysis between bribes and votes
- Export functionality for reports

## 📄 License

This project is for internal use and analysis of Balancer tokenomics data.
