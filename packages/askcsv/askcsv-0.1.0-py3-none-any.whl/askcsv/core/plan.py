from __future__ import annotations

from typing import Any, Dict


class PlanError(ValueError):
    pass


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise PlanError(msg)


def validate_plan(plan: Dict[str, Any], schema: Dict[str, str]) -> None:
    _require(isinstance(plan, dict), "Plan must be a JSON object.")

    op = plan.get("operation")
    allowed_ops = {"describe", "aggregate", "groupby_aggregate", "topn", "value_counts"}
    _require(op in allowed_ops, f"Unsupported operation: {op}")

    cols = plan.get("columns", [])
    _require(isinstance(cols, list), "`columns` must be a list.")
    _require(all(isinstance(c, str) for c in cols), "`columns` must contain only strings.")
    for c in cols:
        _require(c in schema, f"Unknown column in columns: {c}")

    groupby = plan.get("groupby")
    if groupby is not None:
        _require(isinstance(groupby, list) and all(isinstance(g, str) for g in groupby), "`groupby` must be a list of strings.")
        for g in groupby:
            _require(g in schema, f"Unknown column in groupby: {g}")

    metrics = plan.get("metrics")
    if metrics is not None:
        _require(isinstance(metrics, list), "`metrics` must be a list.")
        for m in metrics:
            _require(isinstance(m, dict), "Each metric must be an object.")
            _require("col" in m and "agg" in m, "Each metric must contain {col, agg}.")
            _require(m["col"] in schema, f"Unknown metric col: {m['col']}")
            _require(m["agg"] in {"sum", "mean", "count", "min", "max"}, f"Unsupported agg: {m['agg']}")

    filters = plan.get("filters")
    if filters is not None:
        _require(isinstance(filters, list), "`filters` must be a list.")
        for f in filters:
            _require(isinstance(f, dict), "Each filter must be an object.")
            _require({"col", "op", "value"} <= set(f.keys()), "Each filter must have {col, op, value}.")
            _require(f["col"] in schema, f"Unknown filter col: {f['col']}")
            _require(f["op"] in {"==", "!=", ">", ">=", "<", "<=", "contains"}, f"Unsupported filter op: {f['op']}")

    topn = plan.get("topn")
    if topn is not None:
        _require(isinstance(topn, int) and 1 <= topn <= 1000, "`topn` must be an int between 1 and 1000.")

    sort_by = plan.get("sort_by")
    if sort_by is not None:
        _require(isinstance(sort_by, dict), "`sort_by` must be an object.")
        _require(sort_by.get("col") in schema, "sort_by.col must be a valid column.")
        _require(sort_by.get("agg") in {"sum", "mean", "count", "min", "max"}, "sort_by.agg invalid.")
        _require(isinstance(sort_by.get("ascending", False), bool), "sort_by.ascending must be boolean.")

    chart = plan.get("chart")
    if chart is not None:
        _require(isinstance(chart, dict), "`chart` must be an object.")
        _require(chart.get("type") in {"pie", "bar", "line", "hist"}, "Unsupported chart type.")
        # x/y are optional for hist
        if chart.get("type") != "hist":
            _require(isinstance(chart.get("x"), str), "chart.x must be a string.")
            _require(isinstance(chart.get("y"), str), "chart.y must be a string.")
