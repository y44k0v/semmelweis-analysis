# analysis/services.py

import io
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import date
from scipy import stats

from .models import YearlyRecord, MonthlyRecord

PIVOT = pd.Timestamp("1847-06-01")


# ─────────────────────────────────────────────
# CSV IMPORT
# ─────────────────────────────────────────────

def import_yearly_csv(file_obj):
    df = pd.read_csv(file_obj)
    YearlyRecord.objects.all().delete()
    YearlyRecord.objects.bulk_create([
        YearlyRecord(
            year=int(row["year"]),
            births=int(row["births"]),
            deaths=int(row["deaths"]),
            clinic=str(row["clinic"]).strip(),
        )
        for _, row in df.iterrows()
    ])


def import_monthly_csv(file_obj):
    df = pd.read_csv(file_obj, parse_dates=["date"])
    MonthlyRecord.objects.all().delete()
    MonthlyRecord.objects.bulk_create([
        MonthlyRecord(
            date=row["date"].date(),
            births=int(row["births"]),
            deaths=int(row["deaths"]),
        )
        for _, row in df.iterrows()
    ])


# ─────────────────────────────────────────────
# DATAFRAMES
# ─────────────────────────────────────────────

def yearly_to_dataframe():
    qs = YearlyRecord.objects.values("year", "births", "deaths", "clinic")
    df = pd.DataFrame(list(qs))
    if not df.empty:
        df["proportion_deaths"] = (df["deaths"] / df["births"]).round(6)
    return df


def monthly_to_dataframe():
    qs = MonthlyRecord.objects.values("date", "births", "deaths")
    df = pd.DataFrame(list(qs))
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["proportion_deaths"] = (df["deaths"] / df["births"]).round(6)
        df = df.sort_values("date").reset_index(drop=True)
    return df


# ─────────────────────────────────────────────
# CHART.JS JSON DATA
# ─────────────────────────────────────────────

def yearly_chart_data():
    """JSON blob consumed by renderClinicChart() in charts.js"""
    df = yearly_to_dataframe()
    if df.empty:
        return json.dumps({"empty": True})
    c1 = df[df["clinic"] == "clinic 1"].sort_values("year")
    c2 = df[df["clinic"] == "clinic 2"].sort_values("year")
    return json.dumps({
        "labels":  c1["year"].tolist(),
        "clinic1": c1["proportion_deaths"].tolist(),
        "clinic2": c2["proportion_deaths"].tolist(),
    })


def monthly_chart_data():
    """JSON blob consumed by renderMonthlyChart() in charts.js"""
    df = monthly_to_dataframe()
    if df.empty:
        return json.dumps({"empty": True})
    before = df[df["date"] < PIVOT]
    after  = df[df["date"] >= PIVOT]
    return json.dumps({
        "labelsBefore": [str(d.date()) for d in before["date"]],
        "before":       before["proportion_deaths"].tolist(),
        "labelsAfter":  [str(d.date()) for d in after["date"]],
        "after":        after["proportion_deaths"].tolist(),
    })


def bootstrap_chart_data_json(boot_diffs, ci_lower, ci_upper):
    counts, edges = np.histogram(boot_diffs, bins=40)
    return json.dumps({
        "labels":   [round((edges[i] + edges[i + 1]) / 2, 5) for i in range(len(counts))],
        "counts":   counts.tolist(),
        "ci_lower": round(ci_lower, 5),
        "ci_upper": round(ci_upper, 5),
    })


# ─────────────────────────────────────────────
# FULL ANALYSIS (feeds analysis_results.html)
# ─────────────────────────────────────────────

def run_full_analysis():
    ctx = {}

    # ── Yearly clinic comparison ──────────────────────────
    ydf = yearly_to_dataframe()
    if not ydf.empty:
        c1 = ydf[ydf["clinic"] == "clinic 1"].set_index("year")["proportion_deaths"]
        c2 = ydf[ydf["clinic"] == "clinic 2"].set_index("year")["proportion_deaths"]
        years = sorted(set(c1.index) | set(c2.index))
        ctx["clinic_comparison"] = [
            {
                "year":    y,
                "clinic1": round(c1[y], 4) if y in c1.index else "—",
                "clinic2": round(c2[y], 4) if y in c2.index else "—",
            }
            for y in years
        ]
    else:
        ctx["clinic_comparison"] = []

    ctx["yearly_chart_data"] = yearly_chart_data()

    # ── Monthly handwashing effect ────────────────────────
    mdf = monthly_to_dataframe()
    ctx["monthly_chart_data"] = monthly_chart_data()

    if not mdf.empty:
        before_s = mdf[mdf["date"] < PIVOT]["proportion_deaths"]
        after_s  = mdf[mdf["date"] >= PIVOT]["proportion_deaths"]
        ctx["mean_before"] = round(float(before_s.mean()), 4)
        ctx["mean_after"]  = round(float(after_s.mean()),  4)
        ctx["mean_diff"]   = round(float(after_s.mean() - before_s.mean()), 4)
    else:
        ctx.update(mean_before=0, mean_after=0, mean_diff=0)
        before_s = after_s = pd.Series(dtype=float)

    # ── Bootstrap CI ─────────────────────────────────────
    if len(before_s) > 1 and len(after_s) > 1:
        rng = np.random.default_rng(42)
        boot_diffs = [
            rng.choice(after_s.values,  size=len(after_s),  replace=True).mean() -
            rng.choice(before_s.values, size=len(before_s), replace=True).mean()
            for _ in range(3000)
        ]
        ci_lower = float(np.quantile(boot_diffs, 0.025))
        ci_upper = float(np.quantile(boot_diffs, 0.975))
        ctx["bootstrap_chart_data"] = bootstrap_chart_data_json(
            boot_diffs, ci_lower, ci_upper
        )
    else:
        ci_lower = ci_upper = 0.0
        ctx["bootstrap_chart_data"] = json.dumps({"empty": True})

    ctx["ci_lower"]     = round(ci_lower, 4)
    ctx["ci_upper"]     = round(ci_upper, 4)
    ctx["ci_lower_pct"] = round(abs(ci_lower) * 100, 2)
    ctx["ci_upper_pct"] = round(abs(ci_upper) * 100, 2)

    # ── Welch t-test ──────────────────────────────────────
    if len(before_s) > 1 and len(after_s) > 1:
        t_stat, p_value = stats.ttest_ind(before_s, after_s, equal_var=False)
    else:
        t_stat = p_value = float("nan")

    ctx["t_stat"]      = round(float(t_stat), 4)
    ctx["p_value"]     = float(p_value)
    ctx["p_value_fmt"] = f"{p_value:.2e}" if not (p_value != p_value) else "N/A"
    ctx["significant"] = (p_value < 0.05) if not (p_value != p_value) else False

    return ctx


# ─────────────────────────────────────────────
# PNG EXPORTS
# ─────────────────────────────────────────────

def _fig_to_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def clinic_comparison_chart_png():
    df = yearly_to_dataframe()
    fig, ax = plt.subplots(figsize=(8, 4))
    if not df.empty:
        for label, grp in df.groupby("clinic"):
            grp = grp.sort_values("year")
            ax.plot(grp["year"], grp["proportion_deaths"], marker="o", label=label)
        ax.legend()
    ax.set_xlabel("Year")
    ax.set_ylabel("Proportion of deaths")
    ax.set_title("Death Proportion by Clinic (1841–1846)")
    return _fig_to_png(fig)


def monthly_proportion_chart_png():
    df = monthly_to_dataframe()
    fig, ax = plt.subplots(figsize=(10, 4))
    if not df.empty:
        before = df[df["date"] < PIVOT].sort_values("date")
        after  = df[df["date"] >= PIVOT].sort_values("date")
        ax.plot(before["date"], before["proportion_deaths"],
                color="tab:red",   label="Before handwashing")
        ax.plot(after["date"],  after["proportion_deaths"],
                color="tab:green", label="After handwashing")
        ax.axvline(PIVOT, color="gray", linestyle="--", linewidth=1)
        ax.legend()
    ax.set_ylabel("Proportion of deaths")
    ax.set_title("Monthly Proportion of Deaths — Clinic 1")
    return _fig_to_png(fig)


def bootstrap_histogram_png():
    mdf = monthly_to_dataframe()
    fig, ax = plt.subplots(figsize=(8, 4))
    if not mdf.empty:
        before_s = mdf[mdf["date"] < PIVOT]["proportion_deaths"]
        after_s  = mdf[mdf["date"] >= PIVOT]["proportion_deaths"]
        rng = np.random.default_rng(42)
        boot_diffs = [
            rng.choice(after_s.values,  size=len(after_s),  replace=True).mean() -
            rng.choice(before_s.values, size=len(before_s), replace=True).mean()
            for _ in range(3000)
        ]
        ci = np.quantile(boot_diffs, [0.025, 0.975])
        ax.hist(boot_diffs, bins=40, color="steelblue", alpha=0.7)
        ax.axvline(ci[0], color="red",   linestyle="--", label=f"2.5%  = {ci[0]:.4f}")
        ax.axvline(ci[1], color="green", linestyle="--", label=f"97.5% = {ci[1]:.4f}")
        ax.legend()
    ax.set_xlabel("Mean difference in proportion deaths")
    ax.set_ylabel("Frequency")
    ax.set_title("Bootstrap Distribution (3 000 resamples)")
    return _fig_to_png(fig)