from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import pandas as pd


def _apply_filters(df: pd.DataFrame, filters: list[dict]) -> pd.DataFrame:
    out = df
    for f in filters:
        col = f["col"]
        op = f["op"]
        val = f["value"]

        if op == "contains":
            out = out[out[col].astype(str).str.contains(str(val), na=False)]
        elif op == "==":
            out = out[out[col] == val]
        elif op == "!=":
            out = out[out[col] != val]
        elif op == ">":
            out = out[pd.to_numeric(out[col], errors="coerce") > float(val)]
        elif op == ">=":
            out = out[pd.to_numeric(out[col], errors="coerce") >= float(val)]
        elif op == "<":
            out = out[pd.to_numeric(out[col], errors="coerce") < float(val)]
        elif op == "<=":
            out = out[pd.to_numeric(out[col], errors="coerce") <= float(val)]
    return out


def execute_plan(df: pd.DataFrame, plan: Dict[str, Any]) -> Tuple[str, Optional[pd.DataFrame]]:
    op = plan["operation"]
    data = df

    if plan.get("filters"):
        data = _apply_filters(data, plan["filters"])

    # describe
    if op == "describe":
        desc = data.describe(include="all").transpose()
        return "Here is a descriptive summary of your data.", desc

    # value_counts
    if op == "value_counts":
        col = plan.get("columns", [None])[0]
        if not col:
            return "Please specify a column for value counts.", None
        vc = data[col].astype(str).value_counts().reset_index()
        vc.columns = [col, "count"]
        topn = plan.get("topn")
        if topn:
            vc = vc.head(topn)
        return f"Value counts for **{col}**.", vc

    # aggregate (no groupby)
    if op == "aggregate":
        metrics = plan.get("metrics", [])
        if not metrics:
            return "Please specify metrics like sum/mean/count.", None

        row = {}
        for m in metrics:
            c, agg = m["col"], m["agg"]
            s = pd.to_numeric(data[c], errors="coerce") if agg in {"sum", "mean", "min", "max"} else data[c]
            if agg == "sum":
                row[f"{c}_sum"] = float(s.sum())
            elif agg == "mean":
                row[f"{c}_mean"] = float(s.mean())
            elif agg == "count":
                row[f"{c}_count"] = int(s.count())
            elif agg == "min":
                row[f"{c}_min"] = float(s.min())
            elif agg == "max":
                row[f"{c}_max"] = float(s.max())

        out = pd.DataFrame([row])
        return "Computed requested aggregates.", out

    # groupby_aggregate
    if op in {"groupby_aggregate", "topn"}:
        groupby = plan.get("groupby", [])
        metrics = plan.get("metrics", [])
        if not groupby or not metrics:
            return "Please specify groupby columns and metrics.", None

        agg_map = {}
        for m in metrics:
            c, agg = m["col"], m["agg"]
            agg_map[c] = agg_map.get(c, [])
            agg_map[c].append(agg)

        gb = data.groupby(groupby).agg(agg_map)

        # flatten multi-index columns
        gb.columns = ["_".join([str(a) for a in col if a]) for col in gb.columns.to_flat_index()]
        gb = gb.reset_index()

        # sorting
        sort_by = plan.get("sort_by")
        if sort_by:
            sort_col = f"{sort_by['col']}_{sort_by['agg']}"
            if sort_col in gb.columns:
                gb = gb.sort_values(sort_col, ascending=bool(sort_by.get("ascending", False)))

        # topn
        if op == "topn" and plan.get("topn"):
            gb = gb.head(int(plan["topn"]))

        return "Computed grouped aggregates.", gb

    return "Unsupported plan operation.", None
