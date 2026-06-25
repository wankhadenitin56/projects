# openFDA FAERS Adverse Event Analyzer
### Signal Detection: PRR | ROR | Chi-Square

A pharmacovigilance signal detection pipeline that queries the **FDA Adverse Event Reporting System (FAERS)** via the openFDA API and computes disproportionality metrics to identify drug safety signals.

---

## What It Does

For any drug name you provide, the tool:
1. Fetches the top-N most-reported adverse events from FAERS
2. Builds a **2×2 contingency table** for each AE
3. Computes **PRR**, **ROR** (with 95% CI), and **Chi-square**
4. Classifies each AE as: `Strong Signal | Signal | Weak Signal | No Signal`
5. Exports **4 interactive Plotly charts** + a **multi-sheet Excel report**

---

## Signal Detection Methods

### 2×2 Contingency Table
```
                  Drug (D+)     No Drug (D-)
  AE reported  |     a        |      c      |
  AE not rep.  |     b        |      d      |
```

### PRR — Proportional Reporting Ratio
```
PRR = [a / (a+b)] / [c / (c+d)]

Signal if: PRR ≥ 2  AND  Chi² ≥ 4  AND  n ≥ 3
```

### ROR — Reporting Odds Ratio
```
ROR = (a × d) / (b × c)

95% CI:  SE(ln ROR) = sqrt(1/a + 1/b + 1/c + 1/d)
         CI = exp(ln(ROR) ± 1.96 × SE)

Signal if: ROR_CI_lower > 1  AND  n ≥ 3
```

### Signal Classification
| Category | Criteria |
|---|---|
| Strong Signal | PRR ≥ 5, χ² ≥ 4, ROR_lower > 2, n ≥ 3 |
| Signal | PRR ≥ 2, χ² ≥ 4, ROR_lower > 1, n ≥ 3 |
| Weak Signal | Either PRR or ROR criteria met |
| No Signal | Neither criteria met |
| Insufficient data | n < 3 |

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Usage

```bash
# Basic usage
python faers_analyzer.py --drug ASPIRIN

# Analyze more AEs
python faers_analyzer.py --drug METFORMIN --top_n 50

# Custom output folder
python faers_analyzer.py --drug WARFARIN --top_n 30 --output_dir ./warfarin_results

# With openFDA API key (higher rate limit)
python faers_analyzer.py --drug OZEMPIC --api_key YOUR_KEY

# Skip plots (only Excel)
python faers_analyzer.py --drug IBUPROFEN --no_plots
```

> **Drug name tips:** Try brand name (ASPIRIN), generic (METFORMIN), or INN. The tool auto-tries `medicinalproduct → generic_name → brand_name` fields.

---

## Outputs

```
output/
├── DRUGNAME_01_top_AEs.html          # Horizontal bar chart — top 20 AEs
├── DRUGNAME_02_PRR_forest.html       # PRR forest plot
├── DRUGNAME_03_ROR_CI.html           # ROR with 95% CI error bars
├── DRUGNAME_04_signal_summary.html   # Signal distribution donut chart
└── FAERS_DRUGNAME_20240101_120000.xlsx
    ├── All AEs                        # Full results
    ├── Signals Only                   # Filtered to Signal + Strong Signal
    ├── Contingency Table              # Raw a, b, c, d values
    └── Summary                        # Metadata + signal counts
```

---

## Data Source

**openFDA Drug Adverse Event API**
- URL: https://api.fda.gov/drug/event.json
- API key (free): https://open.fda.gov/apis/authentication/
- Without key: 240 requests/min | With key: 1000 requests/min

> ⚠️ **Disclaimer:** FAERS data has limitations — underreporting, confounding, and duplicate reports. PRR/ROR signals indicate potential associations, not causality. Always validate with clinical judgment.

---

## Project Structure

```
faers_analyzer/
├── faers_analyzer.py    # Main pipeline
├── requirements.txt
└── README.md
```

---

## Skills Demonstrated (Resume Keywords)

- `openFDA API` — FAERS data extraction
- `Pharmacovigilance` — PRR/ROR signal detection methodology
- `Adverse Event Analysis` — AE frequency & disproportionality
- `Drug Safety Signal Detection` — quantitative criteria
- `Python` — pandas, numpy, plotly, requests
- `Data Visualization` — interactive Plotly HTML dashboards
- `Excel Reporting` — openpyxl multi-sheet output

---

*Built as a personal portfolio project using public openFDA data.*
