from __future__ import annotations

from typing import Dict, Any
import pandas as pd


def _safe_top_values(s: pd.Series, k: int = 5) -> list:
    try:
        vc = s.dropna().astype(str).value_counts().head(k)
        return [{"value": idx, "count": int(cnt)} for idx, cnt in vc.items()]
    except Exception:
        return []


def build_profile_summary(df: pd.DataFrame, top_k: int = 5) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "rows": int(len(df)),
        "cols": int(df.shape[1]),
        "columns": [],
    }

    for col in df.columns:
        s = df[col]
        col_info: Dict[str, Any] = {
            "name": str(col),
            "dtype": str(s.dtype),
            "missing": int(s.isna().sum()),
        }

        if pd.api.types.is_numeric_dtype(s):
            s2 = pd.to_numeric(s, errors="coerce")
            col_info.update({
                "min": None if s2.dropna().empty else float(s2.min()),
                "max": None if s2.dropna().empty else float(s2.max()),
                "mean": None if s2.dropna().empty else float(s2.mean()),
            })
        else:
            col_info["top_values"] = _safe_top_values(s, k=top_k)

        summary["columns"].append(col_info)

    return summary
