from __future__ import annotations

import argparse
import os
import sys

from .webapp import run_web


def main() -> None:
    p = argparse.ArgumentParser(prog="askcsv")
    sub = p.add_subparsers(dest="cmd", required=True)

    web = sub.add_parser("web", help="Launch a local web chat UI for a CSV file.")
    web.add_argument("csv", help="Path to CSV file")
    web.add_argument("--api-key", default=os.getenv("GEMINI_API_KEY"), help="Gemini API key (or set GEMINI_API_KEY)")
    web.add_argument("--model", default="gemini-1.5-flash")
    web.add_argument("--privacy-mode", default="profile_summary", choices=["schema_only", "sample_rows", "profile_summary"])
    web.add_argument("--sample-rows", type=int, default=40)
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=0)
    web.add_argument("--no-browser", action="store_true")

    args = p.parse_args()

    if args.cmd == "web":
        if not args.api_key:
            print("Error: missing Gemini API key. Use --api-key or set GEMINI_API_KEY.", file=sys.stderr)
            sys.exit(2)

        run_web(
            csv_path=args.csv,
            api_key=args.api_key,
            model=args.model,
            privacy_mode=args.privacy_mode,
            sample_rows=args.sample_rows,
            config=__import__("askcsv.webapp").webapp.WebConfig(
                host=args.host,
                port=args.port,
                open_browser=(not args.no_browser),
            ),
        )
