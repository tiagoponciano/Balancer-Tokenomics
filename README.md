# Balancer Tokenomics Analysis Dashboard

Professional Streamlit dashboard for historical analysis of Balancer tokenomics, focusing on revenue distribution, pool classification, and emission impact analysis.

## 🎯 Objective

Create a Streamlit app to analyze historical Balancer tokenomics data, allowing users to:

- Analyze historical revenue distribution (DAO, veBAL/BAL Holders, Incentives)
- Classify pools as Legitimate vs Mercenary based on objective criteria
- Simulate emission reduction scenarios (50%, 70%) and analyze impact
- View weekly aggregation of emissions, votes, and distribution patterns

## 🚀 Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the dashboard:**
```bash
cd script
streamlit run home.py
```

## 📊 Features

### Main Page (Home)
- Overview of total revenue, incentives, DAO profit, and BAL emitted
- Pool classification summary (Legitimate, Mercenary, Undefined)
- Historical revenue trends over time

### Pool Classification
- Detailed breakdown of pool categories
- Historical distribution of BAL by category
- Monthly trends of incentives and DAO profit
- Top performers by category

### Emission Impact Analysis
- Simulate 50% and 70% emission reduction scenarios
- Compare impact on Legitimate vs Mercenary pools
- Visualize profit changes and incentive reductions
- Key insights for each scenario

### Weekly Analysis
- Weekly aggregation of emissions and votes
- Distribution patterns by category
- Percentage of weekly emissions per category
- Placeholder for future bribe analysis

## 📁 Project Structure

```
script/
├── home.py                    # Main dashboard page
├── utils.py                    # Shared utilities and data loading
├── pages/
│   ├── pool_classification.py  # Pool classification analysis
│   ├── emission_impact.py      # Emission reduction impact analysis
│   └── weekly_analysis.py      # Weekly aggregation and voting patterns
└── balancer_v2_financial_master_final.csv  # Historical data
```

## 🔧 Pool Classification Criteria

Pools are automatically classified based on:

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

## 📈 Key Metrics

- **Total Revenue**: Sum of all protocol fees collected
- **Total Incentives**: Sum of all BAL incentives distributed
- **DAO Profit**: Net profit (Revenue - Incentives)
- **Total BAL Emitted**: Total BAL tokens emitted historically

## 🎨 Design

- Minimalist and professional dark theme
- Inter font family
- Gradient accents
- Responsive layout

## 📝 Requirements

- Python 3.8+
- streamlit
- pandas
- plotly
- numpy

## 🔮 Future Enhancements

- Bribe data integration (structure ready, data collection pending)
- Voter profile analysis
- Self-voting pattern detection
- Automated data updates
