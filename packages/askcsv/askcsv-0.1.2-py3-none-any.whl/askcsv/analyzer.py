from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Literal, Dict
import pandas as pd

from .core.profiling import build_profile_summary
from .core.plan import validate_plan, PlanError
from .core.executor import execute_plan
from .core.charts import build_chart
from .llm.gemini import GeminiPlanner

PrivacyMode = Literal["schema_only", "sample_rows", "profile_summary"]


@dataclass
class AskResult:
    text: str
    table: Optional[pd.DataFrame] = None
    fig: Any = None  # matplotlib.figure.Figure | None

    def save_chart(self, path: str, dpi: int = 160) -> None:
        if self.fig is None:
            raise ValueError("No chart was generated for this prompt.")
        self.fig.savefig(path, dpi=dpi, bbox_inches="tight")


class Analyzer:
    """
    AskCSV engine:
    - Load CSV locally
    - Send only schema/sample/profile to Gemini (never full CSV)
    - Gemini returns JSON plan
    - Validate plan
    - Execute locally (pandas)
    - Optionally build chart (matplotlib)
    """
    def __init__(
        self,
        csv_path: str,
        api_key: str,
        model: str = "gemini-1.5-flash",
        privacy_mode: PrivacyMode = "profile_summary",
        sample_rows: int = 40,
        encoding: Optional[str] = None,
    ):
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path, encoding=encoding)
        self.privacy_mode = privacy_mode
        self.sample_rows = sample_rows

        self.planner = GeminiPlanner(api_key=api_key, model=model)

    def _schema(self) -> Dict[str, str]:
        return {c: str(self.df[c].dtype) for c in self.df.columns}

    def ask(self, prompt: str) -> AskResult:
        schema = self._schema()

        payload: Dict[str, object] = {"schema": schema, "user_prompt": prompt}

        if self.privacy_mode == "schema_only":
            pass
        elif self.privacy_mode == "sample_rows":
            n = min(self.sample_rows, len(self.df))
            payload["sample_rows"] = self.df.sample(n=n, random_state=42).to_dict(orient="records")
        elif self.privacy_mode == "profile_summary":
            payload["profile_summary"] = build_profile_summary(self.df)
        else:
            raise ValueError(f"Unknown privacy_mode: {self.privacy_mode}")

        plan = self.planner.make_plan(payload)

        try:
            validate_plan(plan, schema=schema)
        except PlanError as e:
            return AskResult(
                text=f"Plan validation failed: {e}\nTry rephrasing your prompt and mention exact column names.",
                table=None,
                fig=None,
            )

        text, table = execute_plan(self.df, plan)

        fig = None
        if plan.get("chart") is not None:
            try:
                # Prefer charting from the computed table if it exists
                fig = build_chart(table if table is not None else self.df, plan)
            except Exception as e:
                text += f"\n\n(Chart generation failed: {e})"

        return AskResult(text=text, table=table, fig=fig)
