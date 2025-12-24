from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

from typing import Any, Dict
import pandas as pd
import matplotlib.pyplot as plt


def build_chart(data: pd.DataFrame, plan: Dict[str, Any]):
    chart = plan.get("chart", {})
    ctype = chart.get("type")

    fig = plt.figure()
    ax = fig.add_subplot(111)

    title = chart.get("title")
    if title:
        ax.set_title(title)

    if ctype == "hist":
        col = chart.get("x") or (plan.get("columns") or [None])[0]
        if not col or col not in data.columns:
            raise ValueError("Histogram needs a valid column.")
        s = pd.to_numeric(data[col], errors="coerce").dropna()
        ax.hist(s)
        ax.set_xlabel(col)
        ax.set_ylabel("Frequency")
        return fig

    x = chart.get("x")
    y = chart.get("y")
    if not x or not y:
        raise ValueError("Chart needs x and y.")

    if x not in data.columns or y not in data.columns:
        raise ValueError(f"Chart columns not found in data: x={x}, y={y}")

    if ctype == "pie":
        s = data.set_index(x)[y]
        ax.pie(s, labels=s.index)
        return fig

    if ctype == "bar":
        ax.bar(data[x].astype(str), pd.to_numeric(data[y], errors="coerce").fillna(0))
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.tick_params(axis="x", rotation=45)
        return fig

    if ctype == "line":
        ax.plot(data[x], pd.to_numeric(data[y], errors="coerce").fillna(0))
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.tick_params(axis="x", rotation=45)
        return fig

    raise ValueError(f"Unsupported chart type: {ctype}")
