# Market Data Research Project

This branch adds an offline, read-only historical market-data analysis tool in the research/ folder.

## Recommended workflow

Read research/README.md for setup and usage. The research package:

- Reads historical price CSV files already saved on your computer.
- Checks dates, prices, duplicates, and unusually large daily changes.
- Produces descriptive historical statistics and charts.
- Saves a Markdown report, summary CSV, and reproducibility manifest.
- Runs automated unit tests through GitHub Actions.

## Run the report

Install the isolated dependencies:

    python -m pip install -r research/requirements.txt

Place one CSV per symbol in research/data/input/ and run:

    python -m research.run_report

The generated report appears in research/output/.

## Scope

The research package does not connect to a brokerage or data provider, request credentials, generate buy/sell signals, select strategies, or place orders. Its outputs describe historical data and are not forecasts or investment advice.

The original root-level bot files are retained separately for repository history and are not imported by the research package. This branch does not change the default main branch.
