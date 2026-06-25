#!/usr/bin/env python3
"""
============================================================
openFDA FAERS Adverse Event Analyzer
Signal Detection: PRR (Proportional Reporting Ratio)
                  ROR (Reporting Odds Ratio)
Data Source     : openFDA Drug Adverse Event API
Author          : Portfolio Project — Nitin Wankhade
============================================================

Usage:
    python faers_analyzer.py --drug ASPIRIN --top_n 30
    python faers_analyzer.py --drug METFORMIN --top_n 50 --api_key YOUR_KEY
    python faers_analyzer.py --drug WARFARIN --top_n 30 --output_dir ./results

Signal Criteria:
    PRR Signal      : PRR >= 2  AND  Chi² >= 4  AND  n >= 3
    ROR Signal      : ROR_CI_lower > 1           AND  n >= 3
    Strong Signal   : Both PRR and ROR criteria met with PRR >= 5
"""

import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import logging
import argparse
import os
import sys
from datetime import datetime

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
BASE_URL    = "https://api.fda.gov/drug/event.json"
SLEEP_SEC   = 0.3   # rate limit: ~200 req/min without key, stay safe
MAX_RETRIES = 3

# Signal color palette
SIGNAL_COLORS = {
    "Strong Signal"    : "#E24B4A",   # red
    "Signal"           : "#EF9F27",   # amber
    "Weak Signal"      : "#378ADD",   # blue
    "No Signal"        : "#888780",   # gray
    "Insufficient data": "#B4B2A9",   # light gray
}


# ══════════════════════════════════════════════════════════════════════════════
#  FAERS Analyzer Class
# ══════════════════════════════════════════════════════════════════════════════
class FAERSAnalyzer:
    """
    Queries openFDA FAERS and computes disproportionality metrics
    (PRR, ROR) to detect drug–adverse event safety signals.

    2×2 Contingency Table:
                    Drug (D+)    No Drug (D-)
    AE reported  |     a       |      c      |  a+c
    AE not rep.  |     b       |      d      |  b+d
                   ----------   -----------
                     a+b            c+d          N

    PRR = [a/(a+b)] / [c/(c+d)]
    ROR = (a×d) / (b×c)    with 95% CI via ln transform
    χ²  = N(ad − bc)² / [(a+b)(c+d)(a+c)(b+d)]
    """

    def __init__(self, drug_name: str, top_n: int = 30, api_key: str = ""):
        self.drug_name          = drug_name.strip().upper()
        self.top_n              = top_n
        self.api_key            = api_key
        self.results_df         = None
        self.total_db_reports   = 0
        self.total_drug_reports = 0

    # ── API helpers ────────────────────────────────────────────────────────────

    def _get(self, params: dict) -> dict | None:
        """GET request with retry + exponential backoff."""
        if self.api_key:
            params = {**params, "api_key": self.api_key}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                r = requests.get(BASE_URL, params=params, timeout=30)
                if r.status_code == 200:
                    return r.json()
                elif r.status_code == 404:
                    return None                      # zero results — not an error
                elif r.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"Rate limited — sleeping {wait}s (attempt {attempt})")
                    time.sleep(wait)
                else:
                    logger.error(f"HTTP {r.status_code}: {r.text[:200]}")
            except requests.RequestException as exc:
                logger.warning(f"Request error (attempt {attempt}): {exc}")
                time.sleep(attempt)
        return None

    def _total(self, params: dict) -> int:
        """Return meta.results.total from a query (1 record fetched)."""
        data = self._get({**params, "limit": 1})
        if data and "meta" in data:
            return data["meta"]["results"]["total"]
        return 0

    # ── Data fetching ──────────────────────────────────────────────────────────

    def fetch_db_total(self) -> int:
        """Total reports in entire FAERS database (N)."""
        logger.info("Fetching total FAERS database size...")
        n = self._total({})
        logger.info(f"  → Total FAERS reports : {n:,}")
        return n

    def fetch_drug_total(self) -> int:
        """Total reports mentioning target drug (a + b)."""
        logger.info(f"Fetching total reports for: {self.drug_name}")

        # Try exact medicinalproduct match first
        n = self._total({
            "search": f'patient.drug.medicinalproduct:"{self.drug_name}"'
        })

        # Fallback to generic name if nothing found
        if n == 0:
            logger.info("  Medicinal product not found — trying generic name field...")
            n = self._total({
                "search": f'patient.drug.openfda.generic_name:"{self.drug_name.lower()}"'
            })
            if n > 0:
                self._search_field = "generic"
            else:
                # Try brand name
                logger.info("  Trying brand name field...")
                n = self._total({
                    "search": f'patient.drug.openfda.brand_name:"{self.drug_name.lower()}"'
                })
                self._search_field = "brand" if n > 0 else "none"
        else:
            self._search_field = "medicinal"

        logger.info(f"  → Drug reports ({self._search_field}): {n:,}")
        return n

    def _build_drug_search(self) -> str:
        """Return the right search string based on what matched."""
        field_map = {
            "medicinal": f'patient.drug.medicinalproduct:"{self.drug_name}"',
            "generic"  : f'patient.drug.openfda.generic_name:"{self.drug_name.lower()}"',
            "brand"    : f'patient.drug.openfda.brand_name:"{self.drug_name.lower()}"',
        }
        return field_map.get(getattr(self, "_search_field", "medicinal"),
                             f'patient.drug.medicinalproduct:"{self.drug_name}"')

    def fetch_top_aes(self) -> list[dict]:
        """Fetch top-N AEs reported with the drug, sorted by count desc."""
        logger.info(f"Fetching top {self.top_n} AEs for {self.drug_name}...")
        data = self._get({
            "search" : self._build_drug_search(),
            "count"  : "patient.reaction.reactionmeddrapt.exact",
            "limit"  : self.top_n,
        })
        if data and "results" in data:
            logger.info(f"  → Found {len(data['results'])} AEs")
            return data["results"]
        logger.warning("  → No AEs found")
        return []

    def fetch_ae_total(self, ae_name: str) -> int:
        """Total reports with a given AE across ALL drugs (a + c)."""
        n = self._total({
            "search": f'patient.reaction.reactionmeddrapt.exact:"{ae_name}"'
        })
        return n

    # ── Statistical calculations ───────────────────────────────────────────────

    @staticmethod
    def prr(a, b, c, d) -> float:
        """Proportional Reporting Ratio."""
        denom_drug = a + b
        denom_rest = c + d
        if denom_drug == 0 or denom_rest == 0 or c == 0:
            return np.nan
        return (a / denom_drug) / (c / denom_rest)

    @staticmethod
    def ror(a, b, c, d) -> tuple[float, float, float]:
        """Reporting Odds Ratio + 95% CI (lower, upper)."""
        if b == 0 or c == 0:
            return np.nan, np.nan, np.nan
        val = (a * d) / (b * c)
        if any(x <= 0 for x in [a, b, c, d]):
            return val, np.nan, np.nan
        se = np.sqrt(1/a + 1/b + 1/c + 1/d)
        ln_val = np.log(val)
        return val, np.exp(ln_val - 1.96 * se), np.exp(ln_val + 1.96 * se)

    @staticmethod
    def chi_square(a, b, c, d) -> float:
        """Pearson Chi-square statistic."""
        n = a + b + c + d
        if n == 0:
            return np.nan
        numerator   = n * (a * d - b * c) ** 2
        denominator = (a + b) * (c + d) * (a + c) * (b + d)
        if denominator == 0:
            return np.nan
        return numerator / denominator

    @staticmethod
    def classify(a, prr_val, chi2, ror_lo) -> str:
        """Assign signal category per pharmacovigilance criteria."""
        if a < 3:
            return "Insufficient data"
        prr_sig = (not np.isnan(prr_val)) and prr_val >= 2 and (not np.isnan(chi2)) and chi2 >= 4
        ror_sig = (not np.isnan(ror_lo)) and ror_lo > 1
        if prr_sig and ror_sig:
            return "Strong Signal" if (prr_val >= 5 and ror_lo > 2) else "Signal"
        if prr_sig or ror_sig:
            return "Weak Signal"
        return "No Signal"

    # ── Main pipeline ──────────────────────────────────────────────────────────

    def run(self) -> pd.DataFrame:
        """Execute full analysis pipeline."""
        logger.info("=" * 60)
        logger.info(f"  FAERS Signal Detection  ▶  Drug: {self.drug_name}")
        logger.info("=" * 60)

        # Baseline counts
        N             = self.fetch_db_total()
        drug_total    = self.fetch_drug_total()

        if drug_total == 0:
            logger.error(f"No FAERS reports found for '{self.drug_name}'. "
                         "Try a different name (e.g. brand or generic).")
            return pd.DataFrame()

        self.total_db_reports   = N
        self.total_drug_reports = drug_total

        # Top AEs for this drug
        ae_list = self.fetch_top_aes()
        if not ae_list:
            return pd.DataFrame()

        # Per-AE signal calculation
        rows = []
        total = len(ae_list)
        logger.info(f"Computing PRR/ROR for {total} adverse events...")

        for i, item in enumerate(ae_list, 1):
            ae   = item["term"]
            a    = item["count"]          # drug + AE

            time.sleep(SLEEP_SEC)

            ae_total = self.fetch_ae_total(ae)

            b = drug_total - a            # drug, no AE
            c = ae_total   - a            # no drug, AE
            d = N - a - b  - c            # no drug, no AE

            if b < 0 or c < 0 or d < 0:
                logger.warning(f"  [{i}/{total}] {ae}: negative cell — skipping")
                continue

            prr_val              = self.prr(a, b, c, d)
            ror_val, ror_lo, ror_hi = self.ror(a, b, c, d)
            chi2                 = self.chi_square(a, b, c, d)
            signal               = self.classify(a, prr_val, chi2, ror_lo)

            rows.append({
                "adverse_event"     : ae,
                "drug_ae_count"     : a,
                "drug_total"        : drug_total,
                "ae_total_all_drugs": ae_total,
                "db_total"          : N,
                "a": a, "b": b, "c": c, "d": d,
                "PRR"               : round(prr_val, 3) if not np.isnan(prr_val) else np.nan,
                "ROR"               : round(ror_val, 3) if not np.isnan(ror_val) else np.nan,
                "ROR_CI_lower"      : round(ror_lo,  3) if not np.isnan(ror_lo)  else np.nan,
                "ROR_CI_upper"      : round(ror_hi,  3) if not np.isnan(ror_hi)  else np.nan,
                "chi_square"        : round(chi2,    3) if not np.isnan(chi2)    else np.nan,
                "signal"            : signal,
            })

            logger.info(
                f"  [{i:>2}/{total}] {ae:<45} "
                f"n={a:<6} PRR={prr_val:<7.2f} ROR={ror_val:<7.2f} → {signal}"
                if not np.isnan(prr_val) else
                f"  [{i:>2}/{total}] {ae:<45} n={a} → {signal}"
            )

        df = (
            pd.DataFrame(rows)
            .sort_values("drug_ae_count", ascending=False)
            .reset_index(drop=True)
        )
        self.results_df = df
        return df

    # ── Visualizations ─────────────────────────────────────────────────────────

    def plot_all(self, out_dir: str = "output"):
        """Generate and save all 4 Plotly charts as HTML."""
        os.makedirs(out_dir, exist_ok=True)
        df = self.results_df

        # ── 1. Top AEs horizontal bar ──────────────────────────────────────────
        top20 = df.head(20).copy()
        fig1  = px.bar(
            top20,
            x="drug_ae_count", y="adverse_event",
            orientation="h",
            color="signal", color_discrete_map=SIGNAL_COLORS,
            title=f"Top 20 Adverse Events — {self.drug_name} (FAERS)",
            labels={
                "drug_ae_count" : "Number of Reports",
                "adverse_event" : "Adverse Event",
                "signal"        : "Signal",
            },
            height=600,
        )
        fig1.update_layout(
            yaxis={"categoryorder": "total ascending"},
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Arial", size=12),
        )
        p1 = os.path.join(out_dir, f"{self.drug_name}_01_top_AEs.html")
        fig1.write_html(p1)
        logger.info(f"Saved: {p1}")

        # ── 2. PRR Forest Plot ─────────────────────────────────────────────────
        fdf  = df[df["PRR"].notna() & (df["drug_ae_count"] >= 3)].head(25)
        fig2 = go.Figure()
        for _, row in fdf.iterrows():
            col = SIGNAL_COLORS.get(row["signal"], "#888")
            fig2.add_trace(go.Scatter(
                x=[row["PRR"]], y=[row["adverse_event"]],
                mode="markers",
                marker=dict(size=max(8, min(20, row["drug_ae_count"] // 20 + 8)), color=col),
                showlegend=False,
                hovertemplate=(
                    f"<b>{row['adverse_event']}</b><br>"
                    f"PRR: {row['PRR']}<br>"
                    f"n: {row['drug_ae_count']}<br>"
                    f"Signal: {row['signal']}<extra></extra>"
                ),
            ))
        fig2.add_vline(x=2, line_dash="dash", line_color="red",
                       annotation_text="PRR = 2 (threshold)")
        fig2.add_vline(x=1, line_dash="dot", line_color="gray",
                       annotation_text="PRR = 1 (null)")
        fig2.update_layout(
            title=f"PRR Forest Plot — {self.drug_name}",
            xaxis_title="PRR Value",
            yaxis_title="Adverse Event",
            height=650, plot_bgcolor="white", paper_bgcolor="white",
        )
        p2 = os.path.join(out_dir, f"{self.drug_name}_02_PRR_forest.html")
        fig2.write_html(p2)
        logger.info(f"Saved: {p2}")

        # ── 3. ROR CI Plot (errorbars) ─────────────────────────────────────────
        rdf = df[
            df["ROR"].notna() &
            df["ROR_CI_lower"].notna() &
            (df["drug_ae_count"] >= 3)
        ].head(20).copy()

        fig3 = go.Figure()
        for _, row in rdf.iterrows():
            col       = SIGNAL_COLORS.get(row["signal"], "#888")
            error_lo  = max(0, row["ROR"] - row["ROR_CI_lower"])
            error_hi  = max(0, row["ROR_CI_upper"] - row["ROR"])
            fig3.add_trace(go.Scatter(
                x=[row["ROR"]], y=[row["adverse_event"]],
                mode="markers",
                error_x=dict(
                    type="data",
                    symmetric=False,
                    array=[error_hi],
                    arrayminus=[error_lo],
                    color=col,
                ),
                marker=dict(size=9, color=col),
                showlegend=False,
                hovertemplate=(
                    f"<b>{row['adverse_event']}</b><br>"
                    f"ROR: {row['ROR']} (95% CI: {row['ROR_CI_lower']}–{row['ROR_CI_upper']})<br>"
                    f"n: {row['drug_ae_count']}<extra></extra>"
                ),
            ))
        fig3.add_vline(x=1, line_dash="dash", line_color="red",
                       annotation_text="ROR = 1 (null)")
        fig3.update_layout(
            title=f"ROR with 95% CI — {self.drug_name}",
            xaxis_title="ROR (log scale)",
            yaxis_title="Adverse Event",
            xaxis_type="log",
            height=650, plot_bgcolor="white", paper_bgcolor="white",
        )
        p3 = os.path.join(out_dir, f"{self.drug_name}_03_ROR_CI.html")
        fig3.write_html(p3)
        logger.info(f"Saved: {p3}")

        # ── 4. Signal summary donut ────────────────────────────────────────────
        sig_counts = df["signal"].value_counts().reset_index()
        sig_counts.columns = ["signal", "count"]
        fig4 = px.pie(
            sig_counts, values="count", names="signal",
            color="signal", color_discrete_map=SIGNAL_COLORS,
            title=f"Signal Distribution — {self.drug_name}  (n={len(df)} AEs)",
            hole=0.45,
        )
        fig4.update_traces(textposition="outside", textinfo="percent+label")
        fig4.update_layout(paper_bgcolor="white")
        p4 = os.path.join(out_dir, f"{self.drug_name}_04_signal_summary.html")
        fig4.write_html(p4)
        logger.info(f"Saved: {p4}")

    # ── Excel export ───────────────────────────────────────────────────────────

    def to_excel(self, out_dir: str = "output") -> str:
        """Export to multi-sheet formatted Excel."""
        os.makedirs(out_dir, exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(out_dir, f"FAERS_{self.drug_name}_{ts}.xlsx")

        DISPLAY_COLS = [
            "adverse_event", "drug_ae_count", "ae_total_all_drugs",
            "PRR", "ROR", "ROR_CI_lower", "ROR_CI_upper",
            "chi_square", "signal",
        ]

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            # Sheet 1 — all results
            self.results_df[DISPLAY_COLS].to_excel(
                writer, sheet_name="All AEs", index=False
            )

            # Sheet 2 — signals only
            sig_df = self.results_df[
                self.results_df["signal"].isin(["Strong Signal", "Signal"])
            ]
            sig_df[DISPLAY_COLS].to_excel(
                writer, sheet_name="Signals Only", index=False
            )

            # Sheet 3 — contingency table (for audit)
            ct_cols = ["adverse_event", "a", "b", "c", "d",
                       "PRR", "ROR", "chi_square", "signal"]
            self.results_df[ct_cols].to_excel(
                writer, sheet_name="Contingency Table", index=False
            )

            # Sheet 4 — summary metadata
            summary = pd.DataFrame({
                "Parameter": [
                    "Drug",
                    "Total FAERS DB Reports",
                    "Drug Reports in FAERS",
                    "AEs Analyzed",
                    "Strong Signals",
                    "Signals",
                    "Weak Signals",
                    "No Signal",
                    "Analysis Date",
                ],
                "Value": [
                    self.drug_name,
                    f"{self.total_db_reports:,}",
                    f"{self.total_drug_reports:,}",
                    len(self.results_df),
                    len(self.results_df[self.results_df["signal"] == "Strong Signal"]),
                    len(self.results_df[self.results_df["signal"] == "Signal"]),
                    len(self.results_df[self.results_df["signal"] == "Weak Signal"]),
                    len(self.results_df[self.results_df["signal"] == "No Signal"]),
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                ],
            })
            summary.to_excel(writer, sheet_name="Summary", index=False)

            # Auto-fit column widths
            for sheet in writer.sheets.values():
                for col in sheet.columns:
                    width = max(
                        len(str(cell.value or "")) for cell in col
                    )
                    sheet.column_dimensions[col[0].column_letter].width = min(width + 4, 45)

        logger.info(f"Excel saved: {path}")
        return path

    # ── Console summary ────────────────────────────────────────────────────────

    def print_summary(self):
        df = self.results_df
        sep = "=" * 65
        print(f"\n{sep}")
        print(f"  FAERS ANALYSIS COMPLETE  ▶  {self.drug_name}")
        print(sep)
        print(f"  Total FAERS DB Reports  : {self.total_db_reports:>12,}")
        print(f"  Drug Reports in FAERS   : {self.total_drug_reports:>12,}")
        print(f"  Adverse Events Analyzed : {len(df):>12,}")
        print(f"\n  Signal Breakdown:")
        for sig, cnt in df["signal"].value_counts().items():
            bar = "█" * min(cnt, 30)
            print(f"    {sig:<20} {cnt:>4}  {bar}")
        print(f"\n  Top Confirmed Signals (PRR ≥ 2, χ² ≥ 4, n ≥ 3):")
        top_sig = df[df["signal"].isin(["Strong Signal", "Signal"])].head(10)
        if top_sig.empty:
            print("    No signals detected.")
        else:
            print(f"  {'Adverse Event':<40} {'n':>6} {'PRR':>7} {'ROR':>7} {'Signal'}")
            print("  " + "-" * 68)
            for _, r in top_sig.iterrows():
                print(
                    f"  {r['adverse_event']:<40} {r['drug_ae_count']:>6} "
                    f"{r['PRR']:>7.2f} {r['ROR']:>7.2f}  {r['signal']}"
                )
        print(sep + "\n")


# ══════════════════════════════════════════════════════════════════════════════
#  CLI Entry Point
# ══════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="FAERS Adverse Event Analyzer — PRR/ROR Signal Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python faers_analyzer.py --drug ASPIRIN
  python faers_analyzer.py --drug METFORMIN --top_n 50
  python faers_analyzer.py --drug WARFARIN  --top_n 30 --output_dir ./warfarin_results
  python faers_analyzer.py --drug OZEMPIC   --api_key YOUR_OPENFDA_KEY
        """
    )
    parser.add_argument("--drug",       required=True,  help="Drug name (medicinal/generic/brand)")
    parser.add_argument("--top_n",      type=int, default=30, help="Top N AEs to analyze (default: 30)")
    parser.add_argument("--api_key",    default="",     help="openFDA API key (optional, increases rate limit)")
    parser.add_argument("--output_dir", default="output", help="Output folder for Excel + HTML files")
    parser.add_argument("--no_plots",   action="store_true", help="Skip generating Plotly HTML files")
    args = parser.parse_args()

    analyzer = FAERSAnalyzer(
        drug_name=args.drug,
        top_n=args.top_n,
        api_key=args.api_key,
    )

    df = analyzer.run()

    if df.empty:
        logger.error("No results — exiting.")
        sys.exit(1)

    analyzer.print_summary()

    if not args.no_plots:
        analyzer.plot_all(out_dir=args.output_dir)

    analyzer.to_excel(out_dir=args.output_dir)

    logger.info("Done! Open the HTML files in your browser to explore the charts.")


if __name__ == "__main__":
    main()
