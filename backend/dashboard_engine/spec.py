"""
Dashboard spec builder for Day 4 MVP.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _looks_like_datetime(v: Any) -> bool:
    if isinstance(v, datetime):
        return True
    if isinstance(v, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"):
            try:
                datetime.strptime(v[:19], fmt)
                return True
            except Exception:
                continue
    return False


def build_dashboard_spec(question: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {"title": "No Data", "charts": [], "kpis": []}

    columns = list(results[0].keys())
    numeric_cols = [c for c in columns if any(_is_number(r.get(c)) for r in results)]
    time_cols = [c for c in columns if any(_looks_like_datetime(r.get(c)) for r in results)]
    string_cols = [c for c in columns if c not in numeric_cols and c not in time_cols]

    charts: list[dict[str, Any]] = []
    kpis: list[dict[str, Any]] = []

    # KPI cards for first two numeric columns
    for c in numeric_cols[:2]:
        vals = [float(r[c]) for r in results if _is_number(r.get(c))]
        if vals:
            kpis.append({"type": "kpi", "title": f"Total {c}", "metric": c, "value": sum(vals)})

    if time_cols and numeric_cols:
        charts.append(
            {
                "type": "line",
                "title": f"{numeric_cols[0]} over {time_cols[0]}",
                "xAxis": time_cols[0],
                "yAxis": numeric_cols[0],
                "series": [{"name": numeric_cols[0], "dataKey": numeric_cols[0]}],
            }
        )

    if string_cols and numeric_cols:
        charts.append(
            {
                "type": "bar",
                "title": f"{numeric_cols[0]} by {string_cols[0]}",
                "xAxis": string_cols[0],
                "yAxis": numeric_cols[0],
                "series": [{"name": numeric_cols[0], "dataKey": numeric_cols[0]}],
                "drilldown": True,
            }
        )
        charts.append(
            {
                "type": "pie",
                "title": f"{string_cols[0]} distribution",
                "nameKey": string_cols[0],
                "valueKey": numeric_cols[0],
            }
        )

    if len(numeric_cols) >= 2:
        charts.append(
            {
                "type": "scatter",
                "title": f"{numeric_cols[1]} vs {numeric_cols[0]}",
                "xAxis": numeric_cols[0],
                "yAxis": numeric_cols[1],
            }
        )

    geo_col = next((c for c in columns if c.lower() in {"country", "state", "region", "city"}), None)
    if geo_col and numeric_cols:
        charts.append(
            {
                "type": "choropleth",
                "title": f"{numeric_cols[0]} by {geo_col}",
                "regionKey": geo_col,
                "valueKey": numeric_cols[0],
            }
        )

    if numeric_cols and len(results) > 1:
        charts.append(
            {
                "type": "area",
                "title": f"{numeric_cols[0]} trend area",
                "xAxis": time_cols[0] if time_cols else columns[0],
                "yAxis": numeric_cols[0],
            }
        )

    if string_cols and len(string_cols) > 1 and numeric_cols:
        charts.append(
            {
                "type": "heatmap",
                "title": f"{numeric_cols[0]} heatmap",
                "xAxis": string_cols[0],
                "yAxis": string_cols[1],
                "valueKey": numeric_cols[0],
            }
        )

    # Keep MVP compact.
    charts = charts[:5]

    return {
        "version": "1.0",
        "title": f"Dashboard: {question[:80]}",
        "charts": charts,
        "kpis": kpis,
        "filters": [],
    }
