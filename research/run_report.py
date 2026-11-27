"""Create an offline descriptive report from local historical-price CSV files.

Example:
    python -m research.run_report --input-dir research/data/input --output-dir research/output
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from research.data.validate import read_price_csv
from research.metrics.summary import summarize_prices
from research.reporting.plots import write_charts


def build_report(input_dir: Path, output_dir: Path) -> Path:
    csv_files = sorted(input_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {input_dir}. Add one file per symbol, such as SPY.csv."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    series: dict[str, pd.DataFrame] = {}
    details: dict[str, dict] = {}
    for csv_path in csv_files:
        symbol = csv_path.stem.upper()
        frame, warnings, price_basis = read_price_csv(csv_path)
        if len(frame) < 2:
            raise ValueError(f"{csv_path.name} has fewer than two valid price observations.")
        series[symbol] = frame
        details[symbol] = {
            "summary": summarize_prices(frame),
            "warnings": warnings,
            "price_basis": price_basis,
            "filename": csv_path.name,
        }

    summary_rows = []
    for symbol, detail in details.items():
        summary_rows.append({"symbol": symbol, **detail["summary"]})
    pd.DataFrame(summary_rows).to_csv(output_dir / "historical_summary.csv", index=False)

    chart_names = write_charts(series, output_dir)
    lines = [
        "# Historical Market Data Report",
        "",
        "> Descriptive analysis of supplied CSV files only. This report does not generate",
        "> investment advice, trading signals, strategy rankings, or trade instructions.",
        "",
    ]

    for symbol, detail in details.items():
        summary = detail["summary"]
        lines.extend([
            f"## {symbol}",
            "",
            f"- Source file: {detail['filename']}",
            f"- Price column used: {detail['price_basis']}",
            f"- Date range: {summary['start_date']} to {summary['end_date']}",
            f"- Valid observations: {summary['observations']}",
            f"- Price change over the file's date range: {summary['price_change_pct']:.2f}%",
            f"- Annualized standard deviation of daily price changes: "
            f"{summary['annualized_daily_volatility_pct']:.2f}%",
            f"- Largest historical peak-to-trough decline: "
            f"{summary['maximum_peak_to_trough_decline_pct']:.2f}%",
            f"- Best / worst daily price change: {summary['best_daily_change_pct']:.2f}% / "
            f"{summary['worst_daily_change_pct']:.2f}%",
        ])
        if "average_reported_volume" in summary:
            lines.append(f"- Average reported daily volume: {summary['average_reported_volume']:,.0f}")
        if detail["warnings"]:
            lines.extend(["", "**Data-quality notes**"])
            lines.extend([f"- {warning}" for warning in detail["warnings"]])
        else:
            lines.append("- Data checks: no issues detected by the basic checks in this tool.")
        lines.append("")

    lines.extend(["## Charts", ""])
    for name in chart_names:
        lines.extend([f"![{name}]({name})", ""])
    lines.extend([
        "## Interpretation notes",
        "",
        "- Price changes are based on the selected adjusted-close column when available; otherwise, close is used.",
        "- Historical volatility and declines describe the supplied period and are not forecasts.",
        "- Correlations can change across time and do not establish causation.",
        "- Check the data provider's terms before sharing or redistributing downloaded CSV files.",
        "",
    ])

    report_path = output_dir / "report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a local descriptive report from historical price CSVs.")
    parser.add_argument("--input-dir", type=Path, default=Path("research/data/input"))
    parser.add_argument("--output-dir", type=Path, default=Path("research/output"))
    args = parser.parse_args()
    report = build_report(args.input_dir, args.output_dir)
    print(f"Report created: {report}")


if __name__ == "__main__":
    main()
