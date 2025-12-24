from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

from google import genai


SYSTEM_PROMPT = """
You are a planner for CSV analysis.

You must output ONE valid JSON object only.
No markdown. No explanations. No extra text.

Allowed operations:
- describe
- aggregate
- groupby_aggregate
- topn
- value_counts

Allowed aggregations:
- sum, mean, count, min, max

Allowed filter ops:
- ==, !=, >, >=, <, <=, contains

Allowed chart types:
- pie, bar, line, hist

JSON format:
{
  "operation": "describe|aggregate|groupby_aggregate|topn|value_counts",
  "columns": ["colA"],

  "groupby": ["colX"],
  "metrics": [{"col":"colY","agg":"sum"}],
  "filters": [{"col":"colZ","op":"==","value":"..."}],
  "topn": 10,
  "sort_by": {"col":"colY","agg":"sum","ascending": false},

  "chart": {
    "type":"pie|bar|line|hist",
    "x":"...",
    "y":"...",
    "title":"..."
  }
}

If the request is unclear, return:
{"operation":"describe","columns":[]}
"""


@dataclass
class GeminiPlanner:
    api_key: str
    model: str = "gemini-3-flash-preview"

    def make_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # API key is automatically read from GEMINI_API_KEY env var
        client = genai.Client(api_key=self.api_key)

        response = client.models.generate_content(
            model=self.model,
            contents=[
                SYSTEM_PROMPT,
                json.dumps(payload, ensure_ascii=False),
            ],
        )

        raw = (response.text or "").strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                "Gemini did not return valid JSON.\n"
                f"Raw response:\n{raw[:800]}"
            ) from e
