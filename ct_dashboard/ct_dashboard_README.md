# ClinicalTrials.gov Phase Analysis Dashboard

An interactive Streamlit dashboard for pharma R&D intelligence — queries ClinicalTrials.gov API v2 in real-time and delivers phase distribution, enrollment trends, sponsor analysis, and signal-level insights.

---

## Features

| Feature | Details |
|---|---|
| Real-time data | ClinicalTrials.gov API v2 — no static datasets |
| Search | Condition · Drug/Intervention · Lead Sponsor |
| Filters | Phase · Status · Study Type · Max Results |
| Phase Analysis | Donut + bar chart, Phase × Status heatmap |
| Enrollment Trends | Trial volume by year, avg enrollment over time, phase mix area chart |
| Sponsor Intelligence | Top 15 sponsors bar, sponsor type (Industry/NIH/Gov) donut, leaderboard table |
| Status & Mix | Status breakdown, study type pie, enrollment histogram |
| Data Table | Inline search + filter, download Excel / CSV |
| KPI Cards | Total · Recruiting · Completed · Median Enrollment · Top Phase |

---

## Installation & Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Dashboard opens at → `http://localhost:8501`

---

## Example Queries

| Condition | Drug | Sponsor |
|---|---|---|
| Lupus Nephritis | — | — |
| Type 2 Diabetes | Metformin | — |
| — | Pembrolizumab | — |
| Non-Small Cell Lung Cancer | — | Roche |
| Alzheimer Disease | — | NIH |

---

## Project Structure

```
ct_dashboard/
├── app.py            # Full Streamlit app (single file)
├── requirements.txt
└── README.md
```

---

## Skills Demonstrated (Resume Keywords)

- `ClinicalTrials.gov API v2` — live paginated data fetch
- `Clinical Trial Analytics` — phase distribution, enrollment, site trends
- `Streamlit` — multi-tab interactive dashboard
- `Plotly` — bar, pie, area, histogram, subplots
- `Python` — pandas, requests, openpyxl
- `Pharma R&D Intelligence` — sponsor classification, phase analysis
- `Data Export` — Excel (multi-sheet) + CSV download

---

*Built as a personal portfolio project using public ClinicalTrials.gov data.*
